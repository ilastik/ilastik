from ilastikshell.applet import Applet
from opPixelClassification import OpPixelClassification
from pixelClassification import PixelClassificationGui
from pixelClassificationSerializer import PixelClassificationSerializer, Ilastik05ImportDeserializer

class PixelClassificationApplet( Applet ):
    """
    Implements the pixel classification "applet", which allows the ilastik shell to use it.
    """
    def __init__( self, graph ):
        Applet.__init__( self, "Pixel Classification" )
        self.pipeline = OpPixelClassification( graph )

        # Instantiate the main GUI, which creates the applet drawers (for now)
        self._centralWidget = PixelClassificationGui( self.pipeline, graph )

        # To save some typing, the menu bar is defined in the .ui file 
        #  along with the rest of the central widget.
        # However, we must expose it here as an applet property since we 
        #  want it to show up properly in the shell
        self._menuWidget = self._centralWidget.menuBar
        
        # For now, the central widget owns the applet bar gui
        self._controlWidgets = [ ("Label Marking", self._centralWidget.labelControlUi),
                                 ("Prediction", self._centralWidget.predictionControlUi) ]
        
        # We provide two independent serializing objects:
        #  one for the current scheme and one for importing old projects.
        self._serializableItems = [PixelClassificationSerializer(self.pipeline), # Default serializer for new projects
                                   Ilastik05ImportDeserializer(self.pipeline)]   # Legacy (v0.5) importer
    
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
    
