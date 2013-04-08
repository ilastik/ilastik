from ilastik.applets.labeling.labelingApplet import LabelingApplet
from ilastik.applets.labeling.labelingGui import LabelingGui

from opCarvingTopLevel import OpCarvingTopLevel
from carvingSerializer import CarvingSerializer
from carvingGui import CarvingGui

class CarvingApplet(LabelingApplet):
    
    workflowName = "Carving"
    workflowDescription = "this is obviously self-explanatory"
    
    def __init__(self, workflow, projectFileGroupName, carvingGraphFile, hintOverlayFile=None, pmapOverlayFile=None):
        if hintOverlayFile is not None:
            assert isinstance(hintOverlayFile, str)

        self._topLevelOperator = OpCarvingTopLevel( parent=workflow, carvingGraphFile=carvingGraphFile, hintOverlayFile=hintOverlayFile, pmapOverlayFile=pmapOverlayFile )
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
        labelingSlots.labelInput = topLevelOperatorView.opCarving.WriteSeeds
        labelingSlots.labelOutput = topLevelOperatorView.opCarving.opLabeling.LabelImage
        labelingSlots.labelEraserValue = topLevelOperatorView.opCarving.opLabeling.LabelEraserValue
        labelingSlots.labelDelete = topLevelOperatorView.opCarving.opLabeling.LabelDelete
        labelingSlots.maxLabelValue = topLevelOperatorView.opCarving.opLabeling.MaxLabelValue
        labelingSlots.labelsAllowed = topLevelOperatorView.opCarving.opLabeling.LabelsAllowedFlag
        
        gui = CarvingGui( labelingSlots,
                          topLevelOperatorView,
                          rawInputSlot=topLevelOperatorView.opCarving.RawData )

        gui.minLabelNumber = 2
        gui.maxLabelNumber = 2

        return gui
