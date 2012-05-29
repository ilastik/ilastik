from lazyflow import graph
from lazyflow.graph import OperatorWrapper
from ilastikshell.applet import Applet
from opSeededWatershed import OpSegmentor
from seededWatershedGui import SeededWatershedGui
from seededWatershedSerializer import SeededWatershedSerializer

class SeededWatershedApplet( Applet ):
    """
    Implements the seeded watershed "applet", which allows the ilastik shell to use it.
    """
    def __init__( self, graph ):
        Applet.__init__( self, "Seeded Watershed" )
        self.pipeline = OperatorWrapper(OpSegmentor( graph ))

        # Instantiate the main GUI, which creates the applet drawers (for now)
        self._centralWidget = SeededWatershedGui( self.pipeline, graph )

        # To save some typing, the menu bar is defined in the .ui file 
        #  along with the rest of the central widget.
        # However, we must expose it here as an applet property since we 
        #  want it to show up properly in the shell
        self._menuWidget = self._centralWidget.menuBar
        
        # For now, the central widget owns the applet bar gui
        self._controlWidgets = [ ("Preprocessing", self._centralWidget.setupPreprocessSettingsUi),
                                 ("Interactive Segmentation", self._centralWidget.labelControlUi),
                                 ("Algorithm Settings", self._centralWidget.setupAlgorithmSettingsUi)
                                  ]
        
        # We provide two independent serializing objects:
        #  one for the current scheme and one for importing old projects.
        self._serializableItems = [SeededWatershedSerializer(self.pipeline)] # Default serializer for new projects
    
    @property
    def topLevelOperator(self):
        return self.pipeline

    @property
    def centralWidget( self ):
        return self._centralWidget

    @property
    def appletDrawers(self):
        return self._controlWidgets
    
    @property
    def menuWidget( self ):
        return self._menuWidget

    @property
    def dataSerializers(self):
        return self._serializableItems
    
    @property
    def viewerControlWidget(self):
        return self._centralWidget.viewerControlWidget
    
    def setImageIndex(self, imageIndex):
        """
        Change the currently displayed image to the one specified by the given index.
        """
        self._centralWidget.setImageIndex(imageIndex)
    
