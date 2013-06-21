from ilastik.applets.base.standardApplet import StandardApplet
from opFeatureSelection import OpFeatureSelection
from featureSelectionSerializer import FeatureSelectionSerializer, Ilastik05FeatureSelectionDeserializer

class FeatureSelectionApplet( StandardApplet ):
    """
    This applet allows the user to select sets of input data, 
    which are provided as outputs in the corresponding top-level applet operator.
    """
    def __init__( self, workflow, guiName, projectFileGroupName, filter_implementation='Original' ):
        self._filter_implementation = filter_implementation
        super(FeatureSelectionApplet, self).__init__(guiName, workflow)
        self._serializableItems = [ FeatureSelectionSerializer(self.topLevelOperator, projectFileGroupName),
                                    Ilastik05FeatureSelectionDeserializer(self.topLevelOperator) ]

    @property
    def singleLaneOperatorClass(self):
        return OpFeatureSelection

    @property
    def singleLaneOperatorInitArgs(self):
        return ((), {'filter_implementation' : self._filter_implementation})

    @property
    def broadcastingSlots(self):
        return ['Scales', 'FeatureIds', 'SelectionMatrix', 'FeatureListFilename']

    def createSingleLaneGui( self , laneIndex):
        from featureSelectionGui import FeatureSelectionGui
        opFeat = self.topLevelOperator.getLane(laneIndex)
        gui = FeatureSelectionGui( opFeat, self )
        return gui

    @property
    def dataSerializers(self):
        return self._serializableItems

