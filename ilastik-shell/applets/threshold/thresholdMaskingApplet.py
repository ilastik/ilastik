from ilastikshell.applet import Applet

from opThreshold import OpThresholdMasking
from thresholdGui import ThresholdGui

from lazyflow.graph import OperatorWrapper

class ThresholdApplet( Applet ):
    """
    This is a simple thresholding applet
    """
    def __init__( self, graph ):
        super(ThresholdApplet, self).__init__("Threshold Viewer")

        # Wrap the top-level operator, since the GUI supports multiple images
        self._topLevelOperator = OperatorWrapper( OpThresholdMasking(graph), promotedSlotNames=['InputImage'] )

        self._gui = ThresholdGui(self._topLevelOperator)
        
    @property
    def topLevelOperator(self):
        return self._topLevelOperator

    @property
    def viewerControlWidget(self):
        return self._centralWidget.viewerControlWidget

    @property
    def gui(self):
        return self._gui