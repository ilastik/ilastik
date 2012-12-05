from ilastik.applets.labeling.labelingApplet import LabelingApplet
from ilastik.applets.labeling.labelingGui import LabelingGui
from ilastik.applets.labeling.opLabeling import OpLabeling

from opCarvingTopLevel import OpCarvingTopLevel
from carvingSerializer import CarvingSerializer
from carvingGui import CarvingGui

class CarvingApplet(LabelingApplet):

    def __init__(self, workflow, projectFileGroupName, carvingGraphFile, hintOverlayFile=None):
        if hintOverlayFile is not None:
            assert isinstance(hintOverlayFile, str)

        blockDims = {'c': 1, 'x':512, 'y': 512, 'z': 512, 't': 1}
        labelingOperator = OpLabeling(parent=workflow, blockDims=blockDims)
        self._topLevelOperator = OpCarvingTopLevel( parent=workflow, labelingOperator=labelingOperator, carvingGraphFile=carvingGraphFile, hintOverlayFile=hintOverlayFile )
        self._topLevelOperator.opCarving.BackgroundPriority.setValue(0.95)
        self._topLevelOperator.opCarving.NoBiasBelow.setValue(64)

        super(CarvingApplet, self).__init__(workflow, projectFileGroupName)

    @property
    def dataSerializers(self):
        return [ CarvingSerializer(self._topLevelOperator, "carving") ]

    @property
    def topLevelOperator(self):
        """
        Override from base class.
        """
        return self._topLevelOperator

    def createSingleLaneGui(self, laneIndex):
        """
        Override from base class.
        """
        # Get a single-lane view of the top-level operator
        topLevelOperatorView = self.topLevelOperator.getLane(laneIndex)

        labelingSlots = LabelingGui.LabelingSlots()
        labelingSlots.labelInput = topLevelOperatorView.opLabeling.LabelInputs
        labelingSlots.labelOutput = topLevelOperatorView.opLabeling.LabelImages
        labelingSlots.labelEraserValue = topLevelOperatorView.opLabeling.LabelEraserValue
        labelingSlots.labelDelete = topLevelOperatorView.opLabeling.LabelDelete
        labelingSlots.maxLabelValue = topLevelOperatorView.opLabeling.MaxLabelValue
        labelingSlots.labelsAllowed = topLevelOperatorView.opLabeling.LabelsAllowedFlags
        
        gui = CarvingGui( labelingSlots,
                          topLevelOperatorView,
                          rawInputSlot=topLevelOperatorView.opCarving.RawData )

        gui.minLabelNumber = 2
        gui.maxLabelNumber = 2

        return gui