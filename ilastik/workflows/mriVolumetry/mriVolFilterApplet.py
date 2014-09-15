from ilastik.applets.base.standardApplet import StandardApplet

from opMriVolFilter import OpMriVolFilter

class MriVolFilterApplet( StandardApplet ):
    """
    Applet that applies different methods 
    to 'polish' the prediction maps
    """

    def __init__( self, workflow, guiName, projectFileGroupName ):
        super(self.__class__, self).__init__( guiName, workflow )
        
    @property
    def singleLaneOperatorClass(self):
        return OpMriVolFilter

    @property
    def broadcastingSlots(self):
        return [ 'Sigma', 'Threshold', 'ActiveChannels']

    @property
    def singleLaneGuiClass(self):
        from mriVolFilterGui import MriVolFilterGui
        return MriVolFilterGui
