from ilastik.applets.base.standardApplet import StandardApplet
from opSplitBodyPostprocessing import OpSplitBodyPostprocessing

class SplitBodyPostprocessingApplet( StandardApplet ):
    """
    This applet can be used as a simple viewer of raw image data.  
    Its main purpose is to provide a simple example of how to use the LayerViewerGui, 
    which is intended to be used as a base class for most other applet GUIs.
    """
    def __init__( self, workflow ):
        super(SplitBodyPostprocessingApplet, self).__init__("Split-body post-processing", workflow)

    @property
    def singleLaneOperatorClass(self):
        return OpSplitBodyPostprocessing
    
    @property
    def singleLaneGuiClass(self):
        from splitBodyPostprocessingGui import SplitBodyPostprocessingGui
        return SplitBodyPostprocessingGui

    @property
    def broadcastingSlots(self):
        return []
    
    @property
    def dataSerializers(self):
        return []
