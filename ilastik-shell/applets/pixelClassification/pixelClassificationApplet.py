from ilastikshell.applet import Applet
from opPixelClassification import OpPixelClassification
from pixelClassificationGui import PixelClassificationGui
from pixelClassificationSerializer import PixelClassificationSerializer, Ilastik05ImportDeserializer

class PixelClassificationApplet( Applet ):
    """
    Implements the pixel classification "applet", which allows the ilastik shell to use it.
    """
    def __init__( self, graph ):
        Applet.__init__( self, "Pixel Classification" )

        self._topLevelOperator = OpPixelClassification( graph )

        self._gui = PixelClassificationGui( self._topLevelOperator, graph )
        
        # We provide two independent serializing objects:
        #  one for the current scheme and one for importing old projects.
        self._serializableItems = [PixelClassificationSerializer(self._topLevelOperator), # Default serializer for new projects
                                   Ilastik05ImportDeserializer(self._topLevelOperator)]   # Legacy (v0.5) importer
    
    @property
    def topLevelOperator(self):
        return self._topLevelOperator

    @property
    def dataSerializers(self):
        return self._serializableItems

    @property
    def gui(self):
        return self._gui


     