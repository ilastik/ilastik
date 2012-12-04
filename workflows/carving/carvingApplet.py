from ilastik.applets.labeling.labelingApplet import LabelingApplet
from ilastik.applets.labeling.labelingGui import LabelingGui

from opCarvingTopLevel import OpCarvingTopLevel
from carvingSerializer import CarvingSerializer
from carvingGui import CarvingGui

class CarvingApplet(LabelingApplet):

    def __init__(self, workflow, projectFileGroupName, carvingGraphFile, hintOverlayFile=None):
        super(CarvingApplet, self).__init__(workflow, projectFileGroupName, blockDims = {'c': 1, 'x':512, 'y': 512, 'z': 512, 't': 1})
        if hintOverlayFile is not None:
            assert isinstance(hintOverlayFile, str)

        labelingOperator = self._topLevelOperator
        self._topLevelOperator = OpCarvingTopLevel( parent=workflow, labelingOperator=labelingOperator, carvingGraphFile=carvingGraphFile, hintOverlayFile=hintOverlayFile )

        self._topLevelOperator.opCarving.BackgroundPriority.setValue(0.95)
        self._topLevelOperator.opCarving.NoBiasBelow.setValue(64)

    @property
    def dataSerializers(self):
        return [ CarvingSerializer(self._topLevelOperator, "carving") ]

    @property
    def gui(self):
        if self._gui is None:

            labelingSlots = LabelingGui.LabelingSlots()
            labelingSlots.labelInput = self.topLevelOperator.opLabeling.LabelInputs
            labelingSlots.labelOutput = self.topLevelOperator.opLabeling.LabelImages
            labelingSlots.labelEraserValue = self.topLevelOperator.opLabeling.LabelEraserValue
            labelingSlots.labelDelete = self.topLevelOperator.opLabeling.LabelDelete
            labelingSlots.maxLabelValue = self.topLevelOperator.opLabeling.MaxLabelValue
            labelingSlots.labelsAllowed = self.topLevelOperator.opLabeling.LabelsAllowedFlags
            
            self._gui = CarvingGui( labelingSlots,
                                    self.topLevelOperator,
                                    rawInputSlot=self.topLevelOperator.opCarving.RawData,
                                    carvingApplet=self )
        return self._gui