from ilastik.ilastikshell.applet import Applet

class LayerViewerApplet( Applet ):
    """
    This is a simple viewer applet
    """
    def __init__( self, graph ):
        super(LayerViewerApplet, self).__init__("layer Viewer")

        # NO TOP-LEVEL OPERATOR.  Subclasses must provide their own...
        self._topLevelOperator = None

        # Instantiate the main GUI, which creates the applet drawers (for now)
        self._centralWidget = None
        self._menuWidget = self._centralWidget.menuBar
        
        # The central widget owns the applet drawer gui
        self._drawers = [ ("Results Viewer", self._centralWidget.getAppletDrawerUi() ) ]
        
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

