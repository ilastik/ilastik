from ilastik.applets.base.standardApplet import StandardApplet
from opFeatureSelection import OpFeatureSelection
from featureSelectionSerializer import FeatureSelectionSerializer, Ilastik05FeatureSelectionDeserializer

class FeatureSelectionApplet( StandardApplet ):
    """
    This applet allows the user to select sets of input data, 
    which are provided as outputs in the corresponding top-level applet operator.
    """
    def __init__( self, workflow, guiName, projectFileGroupName ):
        super(FeatureSelectionApplet, self).__init__(guiName, workflow)
        self._serializableItems = [ FeatureSelectionSerializer(self.topLevelOperator, projectFileGroupName),
                                    Ilastik05FeatureSelectionDeserializer(self.topLevelOperator) ]

    @property
    def singleLaneOperatorClass(self):
        return OpFeatureSelection

    @property
    def broadcastingSlots(self):
        return ['Scales', 'FeatureIds', 'SelectionMatrix']
    
    @property
    def singleLaneGuiClass(self):
        from featureSelectionGui import FeatureSelectionGui
        return FeatureSelectionGui

    @property
    def dataSerializers(self):
        return self._serializableItems

