from ilastik.applets.base.applet import Applet
from opLabeling import OpLabeling
from labelingSerializer import LabelingSerializer

class LabelingApplet( Applet ):
    """
    This applet demonstrates how to use the LabelingGui base class, which serves as a reusable base class for other applet GUIs that need a labeling UI.  
    """
    def __init__( self, workflow, projectFileGroupName ):
        Applet.__init__( self, "Generic Labeling" )

        self._topLevelOperator = OpLabeling(parent=workflow)
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
    def gui(self):
        if self._gui is None:
            from labelingGui import LabelingGui

            labelingSlots = LabelingGui.LabelingSlots()
            labelingSlots.labelInput = self.topLevelOperator.LabelInputs
            labelingSlots.labelOutput = self.topLevelOperator.LabelImages
            labelingSlots.labelEraserValue = self.topLevelOperator.LabelEraserValue
            labelingSlots.labelDelete = self.topLevelOperator.LabelDelete
            labelingSlots.maxLabelValue = self.topLevelOperator.MaxLabelValue
            labelingSlots.labelsAllowed = self.topLevelOperator.LabelsAllowedFlags
            
            self._gui = LabelingGui( labelingSlots, self.topLevelOperator, rawInputSlot=self.topLevelOperator.InputImages )
        return self._gui

