from ilastik.applets.base.standardApplet import StandardApplet
from opPixelClassification import OpPixelClassification
from pixelClassificationSerializer import PixelClassificationSerializer, Ilastik05ImportDeserializer
from ilastik.applets.base.applet import ControlCommand

class PixelClassificationApplet( StandardApplet ):
    """
    Implements the pixel classification "applet", which allows the ilastik shell to use it.
    """
    def __init__( self, workflow, projectFileGroupName ):
        self._topLevelOperator = OpPixelClassification( parent=workflow )
        super(PixelClassificationApplet, self).__init__( "Training" )

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
        self.enabled = False
        self.guiexists = False
    
    @property
    def topLevelOperator(self):
        return self._topLevelOperator

    @property
    def dataSerializers(self):
        return self._serializableItems
    
    def updateEnable(self,en):
        if self.enabled != en:
            self.enabled = en
            if self.guiexists:
                if en:
                    self.guiControlSignal.emit(ControlCommand.Pop)
                else:
                    self.guiControlSignal.emit(ControlCommand.DisableSelf)

    def createSingleLaneGui(self, imageLaneIndex):
        from pixelClassificationGui import PixelClassificationGui
        singleImageOperator = self.topLevelOperator.getLane(imageLaneIndex)
        pix = PixelClassificationGui( singleImageOperator, self.shellRequestSignal, self.guiControlSignal, self.predictionSerializer )
        self.guiexists = True
        return pix
