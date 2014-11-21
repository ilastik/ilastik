from ilastik.applets.base.standardApplet import StandardApplet

from opMriVolFilter import OpMriVolFilter
from mriVolFilterSerializer import MriVolFilterSerializer


class MriVolFilterApplet(StandardApplet):
    """
    Applet that applies different methods 
    to 'polish' the prediction maps
    """

    def __init__(self, workflow, guiName, projectFileGroupName):
        super(MriVolFilterApplet, self).__init__(guiName, workflow)
        serializer = MriVolFilterSerializer(self.topLevelOperator,
                                            projectFileGroupName)
        self._serializableItems = [serializer]

    @property
    def singleLaneOperatorClass(self):
        return OpMriVolFilter

    @property
    def broadcastingSlots(self):
        return []
        #return ['Method', 'Configuration', 'Threshold', 'ActiveChannels']

    @property
    def dataSerializers(self):
        return self._serializableItems

    @property
    def singleLaneGuiClass(self):
        from mriVolFilterGui import MriVolFilterGui
        return MriVolFilterGui
