from ilastik.applets.base.standardApplet import StandardApplet

from opFillMissingSlices import OpFillMissingSlices, setDetectionMethod

class FillMissingSlicesApplet( StandardApplet ):
    """
    This is a simple thresholding applet
    """
    def __init__( self, workflow, guiName, projectFileGroupName ):
        super(FillMissingSlicesApplet, self).__init__(guiName, workflow)
        
    @property
    def singleLaneOperatorClass(self):
        return OpFillMissingSlices

    @property
    def broadcastingSlots(self):
        # Top-level operator broadcasting slices (yet)
        assert len( OpFillMissingSlices.inputSlots ) == 1, \
            "You changed the OpFillMissingSlices operator.  Should the new input slots be broadcasting?"
        return []
    
    @property
    def singleLaneGuiClass(self):
        #from fillMissingSlicesGui import FillMissingSlicesGui
        #return FillMissingSlicesGui
        from ilastik.applets.layerViewer import LayerViewerGui
        return LayerViewerGui
