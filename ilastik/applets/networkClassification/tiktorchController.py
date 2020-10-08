import enum
import dataclasses
import logging

from typing import List

from lazyflow.operators.tiktorch import IConnectionFactory

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class ModelInfo:
    name: str
    knownClasses: List[int]
    hasTraining: bool

    @property
    def numClasses(self):
        return len(self.knownClasses)


class TiktorchOperatorModel:
    @enum.unique
    class State(enum.Enum):
        ReadFromProjectFile = "READ_FROM_PROJECT"
        Ready = "READY"
        Empty = "EMPTY"

    def __init__(self, operator):
        self._operator = operator
        self._operator.ModelInfo.notifyDirty(self._handleOperatorStateChange)
        self._operator.ModelSession.notifyDirty(self._handleOperatorStateChange)
        self._operator.ModelBinary.notifyDirty(self._handleOperatorStateChange)
        self._stateListeners = set()
        self._state = self.State.Empty

    @property
    def serverConfig(self):
        return self._operator.ServerConfig.value

    @property
    def modelBytes(self):
        return self._operator.ModelBinary.value

    @property
    def modelInfo(self):
        return self._operator.ModelInfo.value

    @property
    def session(self):
        if self._operator.ModelSession.ready():
            return self._operator.ModelSession.value
        return None

    def clear(self):
        self._state = self.State.Empty
        self._operator.ModelBinary.setValue(None)
        self._operator.ModelSession.setValue(None)
        self._operator.ModelInfo.setValue(None)
        self._operator.NumClasses.setValue(None)

    def setState(self, content, info, session):
        self._operator.NumClasses.disconnect()

        self._operator.ModelBinary.setValue(content)
        self._operator.ModelSession.setValue(session)
        self._operator.ModelInfo.setValue(info)
        self._operator.NumClasses.setValue(info.numClasses)

    def _handleOperatorStateChange(self, *args, **kwargs):
        if (
            self._operator.ModelInfo.ready()
            and self._operator.ModelBinary.ready()
            and not self._operator.ModelSession.ready()
        ):
            self._state = self.State.ReadFromProjectFile
        elif (
            self._operator.ModelInfo.ready()
            and self._operator.ModelBinary.ready()
            and self._operator.ModelSession.ready()
        ):
            self._state = self.State.Ready
        elif not self._operator.ModelInfo.ready():
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

    def loadModel(self, modelPath: str, *, progressCallback=None, cancelToken=None) -> None:
        with open(modelPath, "rb") as modelFile:
            modelBytes = modelFile.read()

        return self.uploadModel(modelBytes=modelBytes, progressCallback=progressCallback, cancelToken=cancelToken)

    def uploadModel(self, *, modelBytes=None, progressCallback=None, cancelToken=None):
        srvConfig = self._model.serverConfig

        connection = self.connectionFactory.ensure_connection(srvConfig)

        def _createModelFromUpload(uploadId: str):
            if cancelToken.cancelled:
                return None

            session = connection.create_model_session(uploadId, [d.id for d in srvConfig.devices])
            info = ModelInfo(session.name, session.known_classes, session.has_training)
            # TODO: Move to main thread
            self._model.setState(modelBytes, info, session)
            return info

        result = connection.upload(modelBytes, progress_cb=progressCallback, cancel_token=cancelToken)
        return result.map(_createModelFromUpload)

    def closeSession(self):
        session = self._model.session
        self._model.clear()
        if session:
            session.close()
