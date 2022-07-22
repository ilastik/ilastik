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
from hashlib import blake2b
from typing import Dict, List, Sequence, Union

from bioimageio.spec import serialize_raw_resource_description_to_dict
from bioimageio.spec.shared.raw_nodes import ImplicitOutputShape, ParametrizedInputShape
from bioimageio.spec.shared.raw_nodes import ResourceDescription as RawResourceDescription

from lazyflow.operators.tiktorch import IConnectionFactory

logger = logging.getLogger(__name__)

# When implementing training, check code that accesses this flag -
# used to hide "unused" gui elements
ALLOW_TRAINING = False


def tagged_input_shapes(raw_spec: RawResourceDescription) -> Dict[str, Dict[str, int]]:
    def min_shape(shape):
        return shape.min if isinstance(shape, ParametrizedInputShape) else shape

    return {inp.name: dict(zip(inp.axes, min_shape(inp.shape))) for inp in raw_spec.inputs}


def explicit_tagged_shape(axes: Sequence[str], shape: ImplicitOutputShape, *, ref: Dict[str, int]) -> Dict[str, int]:
    return {axis: int(ref[axis] * scale + 2 * offset) for axis, scale, offset in zip(axes, shape.scale, shape.offset)}


def tagged_output_shapes(raw_spec: RawResourceDescription) -> Dict[str, Dict[str, int]]:
    inputs = tagged_input_shapes(raw_spec)
    outputs = {}
    for out in raw_spec.outputs:
        if isinstance(out.shape, ImplicitOutputShape):
            outputs[out.name] = explicit_tagged_shape(out.axes, out.shape, ref=inputs[out.shape.reference_tensor])
        else:
            outputs[out.name] = dict(zip(out.axes, out.shape))
    return outputs


@dataclasses.dataclass
class ModelInfo:
    name: str
    knownClasses: List[int]
    hasTraining: bool

    @property
    def numClasses(self):
        return len(self.knownClasses)


@dataclasses.dataclass(frozen=True)
class BIOModelData:
    # doi, nickname, or path
    modelUri: str
    # model zip
    binary: bytes
    # rdf raw description as a dict
    rawDescription: RawResourceDescription
    # hash of the raw description
    hashVal: str = ""

    def __post_init__(self):
        if not getattr(self.rawDescription, "name"):
            raise ValueError("rawDescription must contain the 'name' attribute.")
        if len(self.rawDescription.outputs) != 1:
            raise ValueError("Cannot deal with models that have multiple outputs at the moment")
        if not self.hashVal:
            hash_val = blake2b(
                BIOModelData.raw_model_description_to_string(self.rawDescription).encode("utf8")
            ).hexdigest()
            object.__setattr__(self, "hashVal", f"$blake2b${hash_val}")

    @staticmethod
    def raw_model_description_to_string(rawModelDescription):
        return json.dumps(
            serialize_raw_resource_description_to_dict(rawModelDescription), separators=(",", ":"), sort_keys=True
        )

    @property
    def numClasses(self):
        return list(tagged_output_shapes(self.rawDescription).values())[0]["c"]

    @property
    def name(self):
        return self.rawDescription.name


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
        if self._operator.BIOModel.ready():
            if self._operator.ModelSession.ready():
                self._state = self.State.Ready
            else:
                self._state = self.State.ModelDataAvailable
        else:
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


class TiktorchController:
    def __init__(self, model: TiktorchOperatorModel, connectionFactory: IConnectionFactory) -> None:
        self.connectionFactory = connectionFactory
        self._model = model

    def setModelData(self, modelUri, rawDescription, modelBinary):
        self._model.clear()
        modelData = BIOModelData(
            modelUri=modelUri,
            binary=modelBinary,
            rawDescription=rawDescription,
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
