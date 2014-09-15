from ilastik.applets.base.standardApplet import StandardApplet

from opMriVolReport import OpMriVolReport

class MriVolReportApplet( StandardApplet ):
    """
    Applet that displays report results
    """

    def __init__( self, workflow, guiName, projectFileGroupName ):
        super(self.__class__, self).__init__( guiName, workflow )
        
    @property
    def singleLaneOperatorClass(self):
        return OpMriVolReport

    @property
    def broadcastingSlots(self):
        return [ ]

    @property
    def singleLaneGuiClass(self):
        from mriVolReportGui import MriVolReportGui
        return MriVolReportGui
