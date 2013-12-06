from ilastik.applets.base.standardApplet import StandardApplet

from opGraphCutSegmentation import OpGraphCutSegmentation


class GraphCutSegmentationApplet(StandardApplet):
    """
    bla
    """
    def __init__(self, workflow, guiName, projectFileGroupName):
        super(self.__class__, self).__init__(guiName, workflow)

    @property
    def singleLaneOperatorClass(self):
        return OpThresholdTwoLevels

    @property
    def broadcastingSlots(self):
        raise NotImplementedError("slots??")
        return ['MinSize',
                'MaxSize',
                'HighThreshold',
                'LowThreshold',
                'SmootherSigma',
                'CurOperator',
                'SingleThreshold',
                'Channel']

    @property
    def singleLaneGuiClass(self):
        from graphCutSegmentationGui import GraphCutSegmentationGui
        return ThresholdTwoLevelsGui

    @property
    def dataSerializers(self):
        return self._serializableItems
