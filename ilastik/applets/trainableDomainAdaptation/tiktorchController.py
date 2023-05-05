from ilastik.applets.neuralNetwork.tiktorchController import BIOModelData, TiktorchOperatorModel


class TrainableDomaninAdaptationTiktorchOperatorModel(TiktorchOperatorModel):
    def clear(self):
        self._state = self.State.Empty
        self._operator.BIOModel.setValue(None)
        self._operator.ModelSession.setValue(None)
        self._operator.NumNNClasses.setValue(None)

    def setModel(self, bioModelData: BIOModelData):
        self._operator.NumNNClasses.disconnect()
        self._operator.BIOModel.setValue(bioModelData)

    def setSession(self, session):
        self._operator.NumNNClasses.disconnect()
        self._operator.ModelSession.setValue(session)
        self._operator.NumNNClasses.setValue(self.modelData.numClasses)
