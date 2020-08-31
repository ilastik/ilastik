import enum
import time
import dataclasses
import threading
import logging

from typing import List

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class ModelInfo:
    name: str
    knownClasses: List[int]
    hasTraining: bool

    @property
    def numClasses(self):
        return len(self.knownClasses)


class TiktorchController:
    class State:
        ReadFromProjectFile = "READ_FROM_PROJECT"
        Uploading = "UPLOADING"
        Ready = "READY"
        Empty = "EMPTY"
        Error = "ERROR"

    def __init__(self, operator, connectionFactory):
        self.connectionFactory = connectionFactory
        self.operator = operator
        self._stateListeners = []
        self._state = self.State.Empty

        self.operator.ModelInfo.notifyDirty(self._handleOperatorStateChange)
        self.operator.ModelSession.notifyDirty(self._handleOperatorStateChange)
        self.operator.ModelBinary.notifyDirty(self._handleOperatorStateChange)

    def _emptyState(self):
        assert self._state != self.State.Uploading

        self._state = self.State.Empty
        self.operator.ModelBinary.setValue(None)
        self.operator.ModelSession.setValue(None)
        self.operator.ModelInfo.setValue(None)
        self.operator.NumClasses.setValue(None)

    def loadModel(self, modelPath: str) -> None:
        self._emptyState()
        self._notifyStateChanged()

        with open(modelPath, "rb") as modelFile:
            modelBytes = modelFile.read()

        self.operator.ModelBinary.setValue(modelBytes)
        self.uploadModel()

    def uploadModel(self):
        srvConfig = self.operator.ServerConfig.value
        modelBytes = self.operator.ModelBinary.value

        def _reportProgress(progress):
            print("REPORTING", progress)
            self.progress = progress
            self._state = self.State.Uploading
            self._notifyStateChanged()

        def _uploadModel():
            connection = self.connectionFactory.ensure_connection(srvConfig)

            try:
                uploadId = connection.upload(modelBytes, progress_callback=_reportProgress)
                model = connection.create_model_session(uploadId, [d.id for d in srvConfig.devices])
            except Exception:
                self._state = self.State.Error
                self._notifyStateChanged()

            else:
                info = ModelInfo(model.name, model.known_classes, model.has_training)

                self.operator.ModelBinary.setValue(modelBytes)
                self.operator.ModelSession.setValue(model)
                self.operator.ModelInfo.setValue(info)
                self.operator.NumClasses.setValue(info.numClasses)

                self._state = self.State.Ready
                self._notifyStateChanged()

        uploadThread = threading.Thread(target=_uploadModel, name="ModelUploadThread", daemon=True)
        uploadThread.start()

    def closeModel(self):
        self.operator.ModelBinary.setValue(b"")
        self.operator.ModelInfo.setValue(None)

        model = self.operator.ModelSession.value
        self.operator.ModelSession.setValue(None)

        model.close()

    def _handleOperatorStateChange(self, *args, **kwargs):
        if self.operator.ModelInfo.ready() and self.operator.ModelBinary.ready() and not self.operator.ModelSession.ready():
            self._state = self.State.ReadFromProjectFile
        elif self.operator.ModelInfo.ready() and self.operator.ModelBinary.ready() and self.operator.ModelSession.ready():
            self._state = self.State.Ready
        elif not self.operator.ModelInfo.ready():
            self._state = self.State.Empty

        self._notifyStateChanged()

    @property
    def modelInfo(self):
        return self.operator.ModelInfo.value

    def registerListener(self, fn):
        self._stateListeners.append(fn)
        self._callListener(fn)

    def _callListener(self, fn):
        try:
            fn(self._state)
        except Exception:
            logger.exception("Failed to call listener %s", fn)

    def _notifyStateChanged(self):
        for fn in self._stateListeners:
            print("CALLING", fn)
            self._callListener(fn)
