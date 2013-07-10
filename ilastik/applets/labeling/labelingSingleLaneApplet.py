from ilastik.applets.base.standardApplet import StandardApplet
from opLabeling import OpLabelingSingleLane
#from labelingSerializer import LabelingSerializer

class LabelingSingleLaneApplet( StandardApplet ):
    """
    This applet demonstrates how to use the LabelingGui base class, which serves as a reusable base class for other applet GUIs that need a labeling UI.  
    """
    def __init__( self, workflow, projectFileGroupName, blockDims=None ):
        super(LabelingSingleLaneApplet, self).__init__( "Simple Labeling", workflow )
            
    @property
    def singleLaneOperatorClass(self):
        return OpLabelingSingleLane

    @property
    def broadcastingSlots(self):
        return ['LabelEraserValue', 'LabelDelete']

    @property
    def dataSerializers(self):
        return [] # TODO

    def createSingleLaneGui(self, imageLaneIndex):
        from labelingGui import LabelingGui

        opLabeling = self.topLevelOperator.getLane(imageLaneIndex)
        
        labelingSlots = LabelingGui.LabelingSlots()
        labelingSlots.labelInput = opLabeling.LabelInput
        labelingSlots.labelOutput = opLabeling.LabelImage
        labelingSlots.labelEraserValue = opLabeling.LabelEraserValue
        labelingSlots.labelDelete = opLabeling.LabelDelete
        labelingSlots.maxLabelValue = opLabeling.MaxLabelValue
        labelingSlots.labelsAllowed = opLabeling.LabelsAllowedFlag
        
        # Special hack for labeling, required by the internal label array operator
        # Normally, it is strange to connect two same-operator input slots together like this.
        opLabeling.LabelInput.connect( opLabeling.InputImage )

        return LabelingGui( labelingSlots, opLabeling, rawInputSlot=opLabeling.InputImage )
