from ilastik.applets.base.applet import Applet
from opLabeling import OpLabeling
from labelingSerializer import LabelingSerializer


from ilastik.applets.base.applet import SingleToMultiAppletAdapter
class LabelingApplet( SingleToMultiAppletAdapter ):
    """
    This applet demonstrates how to use the LabelingGui base class, which serves as a reusable base class for other applet GUIs that need a labeling UI.  
    """
    def __init__( self, workflow, projectFileGroupName, blockDims=None ):
        # Provide a custom top-level operator before we init the base class.
        self._topLevelOperator = OpLabeling(parent=workflow, blockDims=blockDims)
        Applet.__init__( self, "Generic Labeling" )

        self._topLevelOperator.name = "Labeling Top-Level Operator"
        self._serializableItems = [ LabelingSerializer( self._topLevelOperator, projectFileGroupName ) ]
        self._gui = None
            
    @property
    def topLevelOperator(self):
        return self._topLevelOperator

    @property
    def dataSerializers(self):
        return self._serializableItems

    @property
    def singleImageGuiClass(self):
        from labelingGui import LabelingGui
        return LabelingGui

    def createSingleImageGui(self, imageLaneIndex):
        from labelingGui import LabelingGui

        opLabeling = self.topLevelOperatorForLane(imageLaneIndex)
        
        labelingSlots = LabelingGui.LabelingSlots()
        labelingSlots.labelInput = opLabeling.LabelInputs
        labelingSlots.labelOutput = opLabeling.LabelImages
        labelingSlots.labelEraserValue = opLabeling.LabelEraserValue
        labelingSlots.labelDelete = opLabeling.LabelDelete
        labelingSlots.maxLabelValue = opLabeling.MaxLabelValue
        labelingSlots.labelsAllowed = opLabeling.LabelsAllowedFlags

        return LabelingGui( labelingSlots, opLabeling, rawInputSlot=opLabeling.InputImages )

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
        raise NotImplementedError
    
