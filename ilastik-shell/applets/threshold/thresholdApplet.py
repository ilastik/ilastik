from ilastikshell.applet import Applet

from opThreshold import OpThresholdViewer
from thresholdGui import ThresholdGui

from lazyflow.graph import OperatorWrapper

class ThresholdApplet( Applet ):
    """
    This is a simple thresholding applet
    """
    def __init__( self, graph ):
        super(ThresholdApplet, self).__init__("Threshold Viewer")

        # Wrap the top-level operator, since the GUI supports multiple images        
        self._topLevelOperator = OperatorWrapper( OpThresholdViewer(graph), promotedSlotNames=['InputImage'] )

        # Instantiate the main GUI, which creates the applet drawers (for now)
        self._centralWidget = ThresholdGui(self._topLevelOperator)
        self._menuWidget = self._centralWidget.menuBar
        
        # The central widget owns the applet drawer gui
        self._drawers = [ ("Threshold Viewer", self._centralWidget.getAppletDrawerUi() ) ]
        
        self._preferencesManager = None
        self._serializableItems = []
    
    @property
    def centralWidget( self ):
        return self._centralWidget

    @property
    def appletDrawers(self):
        return self._drawers
    
    @property
    def menuWidget( self ):
        return self._menuWidget

    @property
    def dataSerializers(self):
        return self._serializableItems

    @property
    def topLevelOperator(self):
        return self._topLevelOperator
    
    @property
    def appletPreferencesManager(self):
         return self._preferencesManager

    @property
    def viewerControlWidget(self):
        return self._centralWidget.viewerControlWidget
    
    def setImageIndex(self, imageIndex):
        """
        Change the currently displayed image to the one specified by the given index.
        """
        self._centralWidget.setImageIndex( imageIndex )

