from ilastik.applets.base.standardApplet import StandardApplet

# FIXME Hook up real operator
from opCostVolumeFilter import OpMriVolPreproc

class MriVolReportApplet( StandardApplet ):
    """
    Applet that displays report result
    """

    def __init__( self, workflow, guiName, projectFileGroupName ):
        super(self.__class__, self).__init__( guiName, workflow )
        
    @property
    def singleLaneOperatorClass(self):
        # FIXME Hook up real operator
        return OpMriVolPreproc

    @property
    def broadcastingSlots(self):
        return [ ]

    @property
    def singleLaneGuiClass(self):
        from mriVolReportGui import MriVolReportGui
        return MriVolReportGui
