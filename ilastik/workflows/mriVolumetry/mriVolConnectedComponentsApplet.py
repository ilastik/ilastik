from ilastik.applets.base.standardApplet import StandardApplet
from opConnectedComponents import OpMriVolCC

class MriVolConnectedComponentsApplet( StandardApplet ):
    """
    Applet that computes connected components and removes them if they are smaller a given threshold

    """

    def __init__( self, workflow, guiName, projectFileGroupName ):
        super(self.__class__, self).__init__( guiName, workflow )

    @property
    def singleLaneOperatorClass(self):
        return OpMriVolCC

    @property
    def broadcastingSlots(self):
        return ['Threshold']

    @property
    def singleLaneGuiClass(self):
        from mriVolConnectedComponentsGui import MriVolConnectedComponentsGui
        return MriVolConnectedComponentsGui
