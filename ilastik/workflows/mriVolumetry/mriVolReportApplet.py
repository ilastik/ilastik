from ilastik.applets.base.standardApplet import StandardApplet

# FIXME Hook up real operator
from opMriVolFilter import OpMriVolFilter

class MriVolReportApplet( StandardApplet ):
    """
    Applet that displays report result
    """

    def __init__( self, workflow, guiName, projectFileGroupName ):
        super(self.__class__, self).__init__( guiName, workflow )
        
    @property
    def singleLaneOperatorClass(self):
        # FIXME Hook up real operator
        return OpMriVolFilter

    @property
    def broadcastingSlots(self):
        return [ ]

    @property
    def singleLaneGuiClass(self):
        from mriVolReportGui import MriVolReportGui
        return MriVolReportGui
