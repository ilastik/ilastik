from ilastik.applets.base.standardApplet import StandardApplet
from opLabeling import OpLabeling
from labelingSerializer import LabelingSerializer


class LabelingApplet( StandardApplet ):
    """
    This applet demonstrates how to use the LabelingGui base class, which serves as a reusable base class for other applet GUIs that need a labeling UI.  
    """
    def __init__( self, workflow, projectFileGroupName, blockDims=None ):
        # Provide a custom top-level operator before we init the base class.
        if blockDims is None:
            blockDims = {'c': 1, 'x':512, 'y': 512, 'z': 512, 't': 1}
        self.__topLevelOperator = OpLabeling(parent=workflow, blockDims=blockDims)
        super(LabelingApplet, self).__init__( "Labeling" )
        self._serializableItems = [ LabelingSerializer( self.__topLevelOperator, projectFileGroupName ) ]
        self._gui = None
            
    @property
    def topLevelOperator(self):
        return self.__topLevelOperator

    @property
    def dataSerializers(self):
        return self._serializableItems

    def createSingleLaneGui(self, imageLaneIndex):
        from labelingGui import LabelingGui

        opLabeling = self.topLevelOperator.getLane(imageLaneIndex)
        
        labelingSlots = LabelingGui.LabelingSlots()
        labelingSlots.labelInput = opLabeling.LabelInputs
        labelingSlots.labelOutput = opLabeling.LabelImages
        labelingSlots.labelEraserValue = opLabeling.LabelEraserValue
        labelingSlots.labelDelete = opLabeling.LabelDelete
        labelingSlots.maxLabelValue = opLabeling.MaxLabelValue
        labelingSlots.labelsAllowed = opLabeling.LabelsAllowedFlags

        return LabelingGui( labelingSlots, opLabeling, rawInputSlot=opLabeling.InputImages )
