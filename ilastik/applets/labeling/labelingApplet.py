from ilastik.applets.base.applet import Applet
from opLabeling import OpLabeling
from labelingSerializer import LabelingSerializer

class LabelingApplet( Applet ):
    """
    Implements the pixel classification "applet", which allows the ilastik shell to use it.
    """
    def __init__( self, graph, projectFileGroupName ):
        Applet.__init__( self, "Generic Labeling" )

        self._topLevelOperator = OpLabeling(graph=graph)
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

