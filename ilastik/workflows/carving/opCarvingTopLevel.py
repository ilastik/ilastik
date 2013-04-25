from lazyflow.graph import Operator, InputSlot, OutputSlot

from volumina.adaptors import Op5ifyer

from opCarving import OpCarving
from opPreprocessing import OpPreprocessing

from ilastik.utility import OperatorSubView, OpMultiLaneWrapper

class OpCarvingTopLevel(Operator):
    name = "OpCarvingTopLevel"
    
    RawData = InputSlot(level=1)
    MST = InputSlot(level=1)
    
    Segmentation = OutputSlot(level=1)
    DoneObjects = OutputSlot(level=1)
    HintOverlay = OutputSlot(level=1)
    DoneSegmentation = OutputSlot(level=1)
    Supervoxels = OutputSlot(level=1)
    Uncertainty = OutputSlot(level=1)

    ###
    # Multi-lane Operator
    ###
    
    def addLane(self, laneIndex):
        # Just add to our input slot, which will propagate to the rest of the internal connections
        assert len(self.RawData) == laneIndex
        #self.MST.resize(laneIndex+1)
        self.RawData.resize(laneIndex+1)

    def removeLane(self, index, final_length):
        # Just remove from our input slot, which will propagate to the rest of the internal connections
        assert len(self.RawData) == final_length + 1
        #self.MST.removeSlot( index, final_length )
        self.RawData.removeSlot(index, final_length)
    
    def getLane(self, laneIndex):
        return OperatorSubView(self, laneIndex)
        
    def __init__(self, parent=None,  hintOverlayFile=None, pmapOverlayFile=None):
        super(OpCarvingTopLevel, self).__init__(parent=parent)

        # Convert data to 5d before giving it to the real operators
        op5 = OpMultiLaneWrapper( Op5ifyer, parent=self, graph=self.graph )
        op5.input.connect( self.RawData )
        operator_kwargs={'hintOverlayFile': hintOverlayFile,
                         'pmapOverlayFile': pmapOverlayFile }
        self.opCarving = OpMultiLaneWrapper( OpCarving, operator_kwargs=operator_kwargs, parent=self )
        self.opCarving.RawData.connect(op5.output)
        self.opCarving.MST.connect( self.MST )
        
        # Special connection: WriteSeeds metadata must mirror the raw data
        self.opCarving.WriteSeeds.connect( self.opCarving.RawData )
        
        # The GUI monitors all top-level slots to decide when to refresh.
        # Hook up these top-level slots so the GUI can find them
        self.Segmentation.connect( self.opCarving.Segmentation )
        self.DoneObjects.connect( self.opCarving.DoneObjects )
        self.HintOverlay.connect( self.opCarving.HintOverlay )
        self.DoneSegmentation.connect( self.opCarving.DoneSegmentation )
        self.Supervoxels.connect( self.opCarving.Supervoxels )
        self.Supervoxels.connect( self.opCarving.Supervoxels )
        self.Uncertainty.connect( self.opCarving.Uncertainty )

    def propagateDirty(self, slot, subindex, roi):
        pass

    