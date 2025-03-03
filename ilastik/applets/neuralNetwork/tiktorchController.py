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
from __future__ import annotations
import dataclasses
import enum
import logging
from hashlib import blake2b
from typing import List, TYPE_CHECKING

from ilastik.applets.neuralNetwork.opNNclass import OpNNTrainingClassification
from lazyflow.operators.tiktorch.classifier import (
    ModelSession,
    ModelUnetSession,
    TiktorchUnetConnectionFactory,
    TrainingConnection,
    UnetConfig,
)

if TYPE_CHECKING:
    from bioimageio.spec import ModelDescr

from lazyflow.operators.tiktorch import IConnectionFactory

logger = logging.getLogger(__name__)

# When implementing training, check code that accesses this flag -
# used to hide "unused" gui elements
ALLOW_TRAINING = False


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
    rawDescription: ModelDescr
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
        # Note: bioimageio imports are delayed as to prevent https request to
        # github and bioimage.io on ilastik startup

        return rawModelDescription.json()

    @property
    def numClasses(self):
        from ilastik.utility.bioimageio_utils import AxisUtils

        assert len(self.rawDescription.outputs) == 1
        output = self.rawDescription.outputs[0]
        return AxisUtils.get_channel_axis_strict(output).size

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

    def setSession(self, session: ModelSession):
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

        def _createModelFromUpload(uploadId: str):
            if cancelToken.cancelled:
                return None

            session_id = connection.create_model_session_with_id(
                uploadId, [d.id for d in srvConfig.devices if d.enabled]
            )
            session = ModelSession(session_id, self._model.modelData.rawDescription, connection)
            info = ModelInfo(session.name, session.known_classes, session.has_training)
            # TODO: Move to main thread
            self._model.setSession(session)
            return info

        result = connection.upload(self._model.modelData.binary, progress_cb=progressCallback, cancel_token=cancelToken)
        return result.map(_createModelFromUpload)

    def closeSession(self):
        session = self._model.session
        self._model.clearSession()
        if session:
            session.close()


class TiktorchUnetOperatorModel:
    def __init__(self, operator: OpNNTrainingClassification):
        self._operator = operator

    @property
    def serverConfig(self):
        return self._operator.ServerConfig.value

    @property
    def session(self) -> ModelUnetSession:
        if not self._operator.ModelSession.ready():
            raise ValueError(f"ModelUnetSession is not ready")
        return self._operator.ModelSession.value

    def clearSession(self):
        if self._operator.ModelSession.ready():
            self.session.close()
        self._operator.ModelSession.setValue(None)
        self._operator.NumClasses.setValue(None)

    def setSession(self, session: ModelUnetSession):
        self._operator.NumClasses.disconnect()
        self._operator.ModelSession.setValue(session)
        self._operator.NumClasses.setValue(session.unet_config.get_num_out_classes())


class TiktorchUnetController:
    def __init__(self, model: TiktorchUnetOperatorModel, connectionFactory: TiktorchUnetConnectionFactory) -> None:
        self.connectionFactory = connectionFactory
        self._model = model

    def initTraining(self, unet_config: UnetConfig):
        """Initialize model on tiktorch server"""
        srvConfig = self._model.serverConfig
        connection: TrainingConnection = self.connectionFactory.ensure_connection(srvConfig)
        server_devices = [d.id for d in srvConfig.devices if d.enabled]
        # todo: configure devices
        session = connection.init_training(unet_config)
        model_unet_session = ModelUnetSession(session=session, factory=connection, unet_config=unet_config)
        self._model.setSession(session=model_unet_session)

    def closeSession(self):
        self._model.clearSession()
