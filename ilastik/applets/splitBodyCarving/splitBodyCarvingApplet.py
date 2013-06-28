from ilastik.workflows.carving.carvingApplet import CarvingApplet
from ilastik.utility import OpMultiLaneWrapper

from opSplitBodyCarving import OpSplitBodyCarving
from splitBodyCarvingSerializer import SplitBodyCarvingSerializer

class SplitBodyCarvingApplet(CarvingApplet):
    
    workflowName = "Split-body Carving"
    
    def __init__(self, workflow, *args, **kwargs):
        self._topLevelOperator = OpMultiLaneWrapper( OpSplitBodyCarving, parent=workflow )
        super(SplitBodyCarvingApplet, self).__init__(workflow, *args, **kwargs)
        self._serializers = None
        
    @property
    def dataSerializers(self):
        if self._serializers is None:
            self._serializers = [ SplitBodyCarvingSerializer(self.topLevelOperator, self._projectFileGroupName) ]
        return self._serializers
    
    def createSingleLaneGui(self, laneIndex):
        """
        Override from base class.
        """
        from splitBodyCarvingGui import SplitBodyCarvingGui
        # Get a single-lane view of the top-level operator
        topLevelOperatorView = self.topLevelOperator.getLane(laneIndex)

        gui = SplitBodyCarvingGui( topLevelOperatorView )

        gui.minLabelNumber = 2
        gui.maxLabelNumber = 2

        return gui
