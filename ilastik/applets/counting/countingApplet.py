from ilastik.applets.base.standardApplet import StandardApplet

from opCounting import OpCounting
from countingGui import CountingGui
from countingSerializer import CountingSerializer

from lazyflow.graph import OperatorWrapper

class CountingApplet(StandardApplet):
    def __init__(self,
                 name="Counting",
                 workflow=None,
                 projectFileGroupName="Counting"):
        self._topLevelOperator = OpCounting(parent=workflow)
        super(CountingApplet, self).__init__(name=name, workflow=workflow)

        #self._serializableItems = [
        #    ObjectClassificationSerializer(projectFileGroupName,
        #                                   self.topLevelOperator)]
        self._serializableItems = [CountingSerializer(self._topLevelOperator, projectFileGroupName)]   # Legacy (v0.5) importer
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
        return CountingGui(singleImageOperator,
                                       self.shellRequestSignal,
                                       self.guiControlSignal, self.predictionSerializer)
