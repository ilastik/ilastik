from ilastik.workflows.carving.carvingApplet import CarvingApplet
from ilastik.utility import OpMultiLaneWrapper

from opSplitBodyCarving import OpSplitBodyCarving
from splitBodyCarvingGui import SplitBodyCarvingGui

class SplitBodyCarvingApplet(CarvingApplet):
    
    workflowName = "Split-body Carving"
    
    def __init__(self, workflow, *args, **kwargs):
        self._topLevelOperator = OpMultiLaneWrapper( OpSplitBodyCarving, parent=workflow )
        super(SplitBodyCarvingApplet, self).__init__(workflow, *args, **kwargs)
    
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
