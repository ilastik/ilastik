import numpy
from lazyflow.graph import Operator, InputSlot
from lazyflow.utility import BigRequestStreamer, OrderedSignal
from lazyflow.roi import roiFromShape, roiToSlice

class OpExportToArray(Operator):
    Input = InputSlot()
    
    def __init__(self, *args, **kwargs):
        super( OpExportToArray, self ).__init__(*args, **kwargs)
        self.progressSignal = OrderedSignal()
    
    def setupOutputs(self):
        pass
        
    def execute(self, slot, subindex, roi, result):
        assert False, "This operator has no output slots"
    
    def propagateDirty(self, slot, subindex, roi):
        pass

    def run_export_to_array(self):
        # Allocate result
        final_result = numpy.ndarray( dtype=self.Input.meta.dtype, shape=self.Input.meta.shape )
        
        # Prepare streamer
        streamer = BigRequestStreamer( self.Input,
                                       roiFromShape(self.Input.meta.shape),
                                       allowParallelResults=True )
        def handle_block_result(roi, block_result):
            final_result[roiToSlice(*roi)] = block_result
        streamer.resultSignal.subscribe( handle_block_result )
        streamer.progressSignal.subscribe( self.progressSignal )

        # Perform export
        streamer.execute()
        return final_result
