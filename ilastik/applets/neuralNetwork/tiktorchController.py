###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2021, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#          http://ilastik.org/license.html
###############################################################################
import dataclasses
import enum
import json
import logging
import operator as stdop
from collections.abc import Mapping
from hashlib import blake2b
from numbers import Number
from typing import List

from bioimageio.spec import serialize_raw_resource_description_to_dict
from bioimageio.spec.shared.raw_nodes import ImplicitOutputShape, ParametrizedInputShape
from bioimageio.spec.shared.raw_nodes import ResourceDescription as RawResourceDescription

from lazyflow.operators.tiktorch import IConnectionFactory

logger = logging.getLogger(__name__)

# When implementing training, check code that accesses this flag -
# used to hide "unused" gui elements
ALLOW_TRAINING = False


def _tagged_op(op, a, b):
    if isinstance(a, Number) and isinstance(b, Mapping):
        return _tagged_op(op, {k: a for k in b}, b)
    elif isinstance(a, Mapping) and isinstance(b, Number):
        return _tagged_op(op, a, {k: b for k in a})
    elif isinstance(a, Mapping) and isinstance(b, Mapping):
        return {k: op(a[k], b[k]) for k in a}
    else:
        raise ValueError(f"Need to supply at least one Dict-like object, got types (a: {type(a)} and b: {type(b)})")


def _tagged_multiplication(a, b):
    return _tagged_op(stdop.mul, a, b)


def _tagged_sum(a, b):
    return _tagged_op(stdop.add, a, b)


def tagged_input_shapes(raw_spec):
    tagged_shapes = {}
    for input_ in raw_spec.inputs:
        if isinstance(input_.shape, ParametrizedInputShape):
            shape = input_.shape.min
        else:
            shape = input_.shape
        tagged_shapes[input_.name] = {ax: sz for ax, sz in zip(input_.axes, shape)}
    return tagged_shapes


def tagged_output_shapes(raw_spec):
    tagged_shapes = {}
    inputs = tagged_input_shapes(raw_spec)

    for output in raw_spec.outputs:
        if isinstance(output.shape, ImplicitOutputShape):
            assert output.shape.reference_tensor in inputs
            tagged_scale = {k: v for k, v in zip(output.axes, output.shape.scale)}
            tagged_offset = {k: v for k, v in zip(output.axes, output.shape.offset)}
            tagged_shape = _tagged_sum(
                _tagged_multiplication(inputs[output.shape.reference_tensor], tagged_scale),
                _tagged_multiplication(2, tagged_offset),
            )
            tagged_shapes[output.name] = {k: int(v) for k, v in tagged_shape.items()}
        else:
            tagged_shapes[output.name] = {k: v for k, v in zip(output.axes, output.shape)}

    return tagged_shapes


@dataclasses.dataclass
class ModelInfo:
    name: str
    knownClasses: List[int]
    hasTraining: bool

    @property
    def numClasses(self):
        return len(self.knownClasses)


@dataclasses.dataclass
class BIOModelData:
    name: str
    # doi, nickname, or path
    modelUri: str
    # model zip
    binary: bytes
    # rdf raw description as a dict
    rawDescription: RawResourceDescription
    # hash of the raw description
    hashVal: str

    @property
    def numClasses(self):
        assert len(self.rawDescription.outputs) == 1, "Cannot deal with models that have multiple outputs at the moment"
        return list(tagged_output_shapes(self.rawDescription).values())[0]["c"]


class TiktorchOperatorModel:
    @enum.unique
    class State(enum.Enum):
        ModelDataAvailable = "ModelDataAvailable"
        Ready = "READY"
        Empty = "EMPTY"

    def __init__(self, operator):
        self._operator = operator
        self._operator.ModelSession.notifyDirty(self._handleOperatorStateChange)
        self._operator.BIOModel.notifyDirty(self._handleOperatorStateChange)
        self._stateListeners = set()
        self._state = self.State.Empty

    @property
    def serverConfig(self):
        return self._operator.ServerConfig.value

    @property
    def modelBinary(self):
        return self.modelData.binary

    @property
    def modelData(self):
        return self._operator.BIOModel.value

    @property
    def rawModelInfo(self):
        return self.modelData.rawDescription

    @property
    def session(self):
        if self._operator.ModelSession.ready():
            return self._operator.ModelSession.value
        return None

    @property
    def modelUri(self):
        return self.modelData.modelUri

    def clear(self):
        self._state = self.State.Empty
        self._operator.BIOModel.setValue(None)
        self._operator.ModelSession.setValue(None)
        self._operator.NumClasses.setValue(None)

    def clearSession(self):
        self._operator.ModelSession.setValue(None)

    def setModel(self, bioModelData: BIOModelData):
        self._operator.NumClasses.disconnect()
        self._operator.BIOModel.setValue(bioModelData)

    def setSession(self, session):
        self._operator.NumClasses.disconnect()
        self._operator.ModelSession.setValue(session)
        self._operator.NumClasses.setValue(self.modelData.numClasses)

    def _handleOperatorStateChange(self, *args, **kwargs):
        if self._operator.BIOModel.ready() and not self._operator.ModelSession.ready():
            self._state = self.State.ModelDataAvailable
        elif self._operator.BIOModel.ready() and self._operator.ModelSession.ready():
            self._state = self.State.Ready
        elif not self._operator.BIOModel.ready():
            self._state = self.State.Empty

        self._notifyStateChanged()

    def registerListener(self, fn):
        self._stateListeners.add(fn)
        self._callListener(fn)

    def removeListener(self, fn):
        self._stateListeners.discard(fn)

    def _callListener(self, fn):
        try:
            fn(self._state)
        except Exception:
            logger.exception("Failed to call listener %s", fn)

    def _notifyStateChanged(self):
        for fn in self._stateListeners:
            self._callListener(fn)


class EnchancerTiktorchOperatorModel(TiktorchOperatorModel):
    def setSession(self, session):
        self._operator.NumClasses.disconnect()
        self._operator.ModelSession.setValue(session)
        self._operator.NumNNClasses.setValue(self.modelData.numClasses)


class TiktorchController:
    def __init__(self, model: TiktorchOperatorModel, connectionFactory: IConnectionFactory) -> None:
        self.connectionFactory = connectionFactory
        self._model = model

    def setModelData(self, modelUri, rawDescription, modelBinary):
        self._model.clear()
        modelData = BIOModelData(
            name=rawDescription.name,
            modelUri=modelUri,
            binary=modelBinary,
            rawDescription=rawDescription,
            hashVal=TiktorchController.computeModelHash(rawDescription),
        )
        self._model.setModel(bioModelData=modelData)

    def uploadModel(self, *, progressCallback=None, cancelToken=None):
        """Initialize model on tiktorch server"""
        srvConfig = self._model.serverConfig

        connection = self.connectionFactory.ensure_connection(srvConfig)

        modelData = self._model.modelData

        def _createModelFromUpload(uploadId: str):
            if cancelToken.cancelled:
                return None

            session = connection.create_model_session(uploadId, [d.id for d in srvConfig.devices if d.enabled])
            info = ModelInfo(session.name, session.known_classes, session.has_training)
            # TODO: Move to main thread
            self._model.setSession(session)
            return info

        result = connection.upload(modelData.binary, progress_cb=progressCallback, cancel_token=cancelToken)
        return result.map(_createModelFromUpload)

    def closeSession(self):
        session = self._model.session
        self._model.clearSession()
        if session:
            session.close()

    @staticmethod
    def computeModelHash(rawModelDescription) -> str:
        has_val = blake2b(
            TiktorchController.raw_model_description_to_string(rawModelDescription).encode("utf8")
        ).hexdigest()
        return f"$blake2b${has_val}"

    @staticmethod
    def raw_model_description_to_string(rawModelDescription):
        return json.dumps(serialize_raw_resource_description_to_dict(rawModelDescription))
