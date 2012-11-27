from ilastik.applets.base.applet import Applet

from opThresholdMasking import OpThresholdMasking
from thresholdMaskingSerializer import ThresholdMaskingSerializer

from lazyflow.graph import OperatorWrapper

from ilastik.applets.base.applet import SingleToMultiAppletAdapter
class ThresholdMaskingApplet( SingleToMultiAppletAdapter ):
    """
    This is a simple thresholding applet
    """
    def __init__( self, workflow, guiName, projectFileGroupName ):
        super(ThresholdMaskingApplet, self).__init__(guiName, workflow)

        # Wrap the top-level operator, since the GUI supports multiple images
        #self._topLevelOperator = OperatorWrapper( OpThresholdMasking, parent=workflow, promotedSlotNames=['InputImage'] )

        #self._gui = None
        
        self._serializableItems = [ ThresholdMaskingSerializer(self.topLevelOperator, projectFileGroupName) ]
        
    @property
    def operatorClass(self):
        return OpThresholdMasking

    @property
    def broadcastingSlotNames(self):
        return ['MinValue', 'MaxValue']
    
    @property
    def singleImageGuiClass(self):
        from thresholdMaskingGui import ThresholdMaskingGui
        return ThresholdMaskingGui

    @property
    def dataSerializers(self):
        return self._serializableItems
