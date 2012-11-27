from ilastik.applets.base.applet import Applet

from opFeatureSelection import OpFeatureSelection

from featureSelectionSerializer import FeatureSelectionSerializer, Ilastik05FeatureSelectionDeserializer

from lazyflow.graph import OperatorWrapper

from ilastik.applets.base.applet import SingleToMultiAppletAdapter
class FeatureSelectionApplet( SingleToMultiAppletAdapter ):
    """
    This applet allows the user to select sets of input data, 
    which are provided as outputs in the corresponding top-level applet operator.
    """
    def __init__( self, workflow, guiName, projectFileGroupName ):
        super(FeatureSelectionApplet, self).__init__(guiName, workflow)

        # Top-level operator is wrapped to support multiple images.
        # Note that the only promoted input slot is the image.  All other inputs are shared among all inner operators.        
        #self._topLevelOperator = OperatorWrapper( OpFeatureSelection, parent=workflow, promotedSlotNames=set(['InputImage']) )
        #assert len(self._topLevelOperator.InputImage) == 0

        self._serializableItems = [ FeatureSelectionSerializer(self._topLevelOperator, projectFileGroupName),
                                    Ilastik05FeatureSelectionDeserializer(self._topLevelOperator) ]

    @property
    def operatorClass(self):
        return OpFeatureSelection

    @property
    def broadcastingSlotNames(self):
        return ['Scales', 'FeatureIds', 'SelectionMatrix']
    
    @property
    def guiClass(self):
        from featureSelectionGui import FeatureSelectionGui
        return FeatureSelectionGui

    @property
    def dataSerializers(self):
        return self._serializableItems

