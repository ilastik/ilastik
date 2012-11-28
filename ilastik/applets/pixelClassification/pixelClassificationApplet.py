from ilastik.applets.base.applet import Applet
from opPixelClassification import OpPixelClassification
from pixelClassificationSerializer import PixelClassificationSerializer, Ilastik05ImportDeserializer

from ilastik.applets.base.applet import SingleToMultiAppletAdapter
class PixelClassificationApplet( SingleToMultiAppletAdapter ):
    """
    Implements the pixel classification "applet", which allows the ilastik shell to use it.
    """
    def __init__( self, workflow, projectFileGroupName ):
        self._topLevelOperator = OpPixelClassification( parent=workflow )
        Applet.__init__( self, "Pixel Classification" )

        # We provide two independent serializing objects:
        #  one for the current scheme and one for importing old projects.
        self._serializableItems = [PixelClassificationSerializer(self._topLevelOperator, projectFileGroupName), # Default serializer for new projects
                                   Ilastik05ImportDeserializer(self._topLevelOperator)]   # Legacy (v0.5) importer


        self._gui = None
        
        # GUI needs access to the serializer to enable/disable prediction storage
        self.predictionSerializer = self._serializableItems[0]

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
    def singleImageGuiClass(self):
        from pixelClassificationGui import PixelClassificationGui
        return PixelClassificationGui

    def createSingleImageGui(self, imageLaneIndex):
        from pixelClassificationGui import PixelClassificationGui
        singleImageOperator = self.topLevelOperatorForLane(imageLaneIndex)
        return PixelClassificationGui( singleImageOperator, self.shellRequestSignal, self.guiControlSignal, self.predictionSerializer )        

    def addLane(self, laneIndex):
        """
        Add an image lane to the top-level operator.
        """
        numLanes = len(self.topLevelOperator.InputImages)
        assert numLanes == laneIndex, "Image lanes must be appended."        
        self.topLevelOperator.InputImages.resize(numLanes+1)
        
    def removeLane(self, laneIndex, finalLength):
        """
        Remove the specified image lane from the top-level operator.
        """
        self.topLevelOperator.InputImages.removeSlot(laneIndex, finalLength)

    @property
    def operatorClass(self):
        # This should never be called because we provided a custom top-level operator
        assert False

    @property
    def broadcastingSlotNames(self):
        # This should never be called because we provided a custom top-level operator
        assert False
