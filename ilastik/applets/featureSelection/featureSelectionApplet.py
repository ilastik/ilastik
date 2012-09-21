from ilastik.applets.base.applet import Applet

from opFeatureSelection import OpFeatureSelection

from featureSelectionSerializer import FeatureSelectionSerializer, Ilastik05FeatureSelectionDeserializer

from lazyflow.graph import OperatorWrapper

class FeatureSelectionApplet( Applet ):
    """
    This applet allows the user to select sets of input data, 
    which are provided as outputs in the corresponding top-level applet operator.
    """
    def __init__( self, graph, guiName, projectFileGroupName ):
        super(FeatureSelectionApplet, self).__init__(guiName)

        # Top-level operator is wrapped to support multiple images.
        # Note that the only promoted input slot is the image.  All other inputs are shared among all inner operators.        
        self._topLevelOperator = OperatorWrapper( OpFeatureSelection, graph=graph, promotedSlotNames=set(['InputImage']) )
        assert len(self._topLevelOperator.InputImage) == 0

        self._serializableItems = [ FeatureSelectionSerializer(self._topLevelOperator, projectFileGroupName),
                                    Ilastik05FeatureSelectionDeserializer(self._topLevelOperator) ]

        self._gui = None
            
    @property
    def dataSerializers(self):
        return self._serializableItems

    @property
    def topLevelOperator(self):
        return self._topLevelOperator

    @property    
    def gui(self):
        if self._gui is None:
            from featureSelectionGui import FeatureSelectionGui
            self._gui = FeatureSelectionGui(self._topLevelOperator)
        return self._gui


