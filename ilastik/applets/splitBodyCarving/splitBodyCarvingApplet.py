from ilastik.workflows.carving.carvingApplet import CarvingApplet
from ilastik.applets.labeling.labelingGui import LabelingGui
from opSplitBodyCarving import OpSplitBodyCarving
from splitBodyCarvingGui import SplitBodyCarvingGui

class SplitBodyCarvingApplet(CarvingApplet):
    
    workflowName = "Split-body Carving"
    
    def __init__(self, workflow, *args, **kwargs):
        super(SplitBodyCarvingApplet, self).__init__(workflow, *args, **kwargs)

        self._topLevelOperator = OpSplitBodyCarving( parent=workflow )
        self._topLevelOperator.opCarving.BackgroundPriority.setValue(0.95)
        self._topLevelOperator.opCarving.NoBiasBelow.setValue(64)
    
    def createSingleLaneGui(self, laneIndex):
        """
        Override from base class.
        """
        # Get a single-lane view of the top-level operator
        topLevelOperatorView = self.topLevelOperator.getLane(laneIndex)

        gui = SplitBodyCarvingGui( topLevelOperatorView )

        gui.minLabelNumber = 2
        gui.maxLabelNumber = 2

        return gui
