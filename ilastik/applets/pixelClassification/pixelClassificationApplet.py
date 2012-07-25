from ilastikshell.applet import Applet
from opPixelClassification import OpPixelClassification
from pixelClassificationGui import PixelClassificationGui
from pixelClassificationSerializer import PixelClassificationSerializer, Ilastik05ImportDeserializer

class PixelClassificationApplet( Applet ):
    """
    Implements the pixel classification "applet", which allows the ilastik shell to use it.
    """
    def __init__( self, graph, projectFileGroupName ):
        Applet.__init__( self, "Pixel Classification" )

        self._topLevelOperator = OpPixelClassification( graph )

        # We provide two independent serializing objects:
        #  one for the current scheme and one for importing old projects.
        self._serializableItems = [PixelClassificationSerializer(self._topLevelOperator, projectFileGroupName), # Default serializer for new projects
                                   Ilastik05ImportDeserializer(self._topLevelOperator)]   # Legacy (v0.5) importer

        # GUI needs access to the serializer to enable/disable prediction storage
        predictionSerializer = self._serializableItems[0]

        self._gui = PixelClassificationGui( self._topLevelOperator, self.guiControlSignal, self.shellRequestSignal, predictionSerializer )
        
        # FIXME: For now, we can directly connect the progress signal from the classifier training operator
        #  directly to the applet's overall progress signal, because it's the only thing we report progress for at the moment.
        # If we start reporting progress for multiple tasks that might occur simulatneously,
        #  we'll need to aggregate the progress updates.
        self._topLevelOperator.opTrain.progressSignal.subscribe(self.progressSignal.emit)
    
    @property
    def topLevelOperator(self):
        return self._topLevelOperator

    @property
    def dataSerializers(self):
        return self._serializableItems

    @property
    def gui(self):
        return self._gui
