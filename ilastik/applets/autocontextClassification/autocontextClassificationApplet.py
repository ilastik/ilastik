from ilastik.applets.base.standardApplet import StandardApplet
from opAutocontextClassification import OpAutocontextClassification
from autocontextClassificationSerializer import AutocontextClassificationSerializer

class AutocontextClassificationApplet( StandardApplet ):
    """
    Implements the pixel classification "applet", which allows the ilastik shell to use it.
    """
    def __init__( self, workflow, projectFileGroupName ):
        self._topLevelOperator = OpAutocontextClassification( parent=workflow )
        super(AutocontextClassificationApplet, self).__init__( "Training" )

        # GUI needs access to the serializer to enable/disable prediction storage
        self.predictionSerializer = AutocontextClassificationSerializer(self._topLevelOperator, projectFileGroupName)
        self._serializableItems = [ self.predictionSerializer ]
        
        self._gui = None        

        # FIXME: For now, we can directly connect the progress signal from the classifier training operator
        #  directly to the applet's overall progress signal, because it's the only thing we report progress for at the moment.
        # If we start reporting progress for multiple tasks that might occur simulatneously,
        #  we'll need to aggregate the progress updates.
        #self._topLevelOperator.opTrain.progressSignal.subscribe(self.progressSignal.emit)
    
    @property
    def topLevelOperator(self):
        return self._topLevelOperator

    @property
    def dataSerializers(self):
        return self._serializableItems

    def createSingleLaneGui(self, imageLaneIndex):
        from autocontextClassificationGui import AutocontextClassificationGui
        singleImageOperator = self.topLevelOperator.getLane(imageLaneIndex)
        return AutocontextClassificationGui( singleImageOperator, self.shellRequestSignal, self.guiControlSignal, self.predictionSerializer )        
