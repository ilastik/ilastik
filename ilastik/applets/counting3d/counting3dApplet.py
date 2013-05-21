from ilastik.applets.base.standardApplet import StandardApplet

from opCounting3d import OpCounting3d
from counting3dGui import Counting3dGui
from counting3dSerializer import Counting3dSerializer

from lazyflow.graph import OperatorWrapper

class Counting3dApplet(StandardApplet):
    def __init__(self,
                 name="Counting3d",
                 workflow=None,
                 projectFileGroupName="Counting3d"):
        self._topLevelOperator = OpCounting3d(parent=workflow)
        super(Counting3dApplet, self).__init__(name=name, workflow=workflow)

        #self._serializableItems = [
        #    ObjectClassificationSerializer(projectFileGroupName,
        #                                   self.topLevelOperator)]
        self._serializableItems = [Counting3dSerializer(self._topLevelOperator, projectFileGroupName)]   # Legacy (v0.5) importer
        self.predictionSerializer = self._serializableItems[0]

        self._topLevelOperator.opTrain.progressSignal.subscribe(self.progressSignal.emit)

    @property
    def topLevelOperator(self):
        return self._topLevelOperator

    @property
    def dataSerializers(self):
        return self._serializableItems

    def createSingleLaneGui(self, imageLaneIndex):
        singleImageOperator = self.topLevelOperator.getLane(imageLaneIndex)
        return Counting3dGui(singleImageOperator,
                                       self.shellRequestSignal,
                                       self.guiControlSignal, self.predictionSerializer)
