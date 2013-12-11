from ilastik.applets.base.standardApplet import StandardApplet

from opGraphCutSegmentation import OpGraphCutSegmentation
from graphCutSegmentationGui import GraphCutSegmentationGui


class GraphCutSegmentationApplet(StandardApplet):
    """
    bla
    """
    def __init__(self, workflow, guiName, projectFileGroupName):
        super(self.__class__, self).__init__(guiName, workflow)

    @property
    def singleLaneOperatorClass(self):
        return OpGraphCutSegmentation

    @property
    def broadcastingSlots(self):
        return ['Beta',
                'Channel']

    @property
    def singleLaneGuiClass(self):
        from graphCutSegmentationGui import GraphCutSegmentationGui
        return GraphCutSegmentationGui

    #@property
    #def dataSerializers(self):
        #return self._serializableItems
