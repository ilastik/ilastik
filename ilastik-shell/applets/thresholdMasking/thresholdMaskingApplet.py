from ilastikshell.applet import Applet

from opThresholdMasking import OpThresholdMasking
from thresholdMaskingGui import ThresholdMaskingGui

from lazyflow.graph import OperatorWrapper

class ThresholdMaskingApplet( Applet ):
    """
    This is a simple thresholding applet
    """
    def __init__( self, graph, guiName, projectFileGroupName ):
        super(ThresholdMaskingApplet, self).__init__(guiName)

        # Wrap the top-level operator, since the GUI supports multiple images
        self._topLevelOperator = OperatorWrapper( OpThresholdMasking(graph), promotedSlotNames=['InputImage'] )

        self._gui = ThresholdMaskingGui(self._topLevelOperator)
        
    @property
    def topLevelOperator(self):
        return self._topLevelOperator

    @property
    def viewerControlWidget(self):
        return self._centralWidget.viewerControlWidget

    @property
    def gui(self):
        return self._gui