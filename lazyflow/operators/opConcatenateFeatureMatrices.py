import itertools
import logging
logger = logging.getLogger(__name__)

import numpy

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.request import RequestPool
from lazyflow.utility import OrderedSignal

class OpConcatenateFeatureMatrices(Operator):
    """
    """
    FeatureMatrices = InputSlot(level=1)
    ConcatenatedOutput = OutputSlot()
    
    def __init__(self, *args, **kwargs):
        super(OpConcatenateFeatureMatrices, self).__init__(*args, **kwargs)
        self.progressSignal = OrderedSignal()

    def setupOutputs(self):
        self.ConcatenatedOutput.meta.shape = (1,)
        self.ConcatenatedOutput.meta.dtype = object
    
    def execute(self, slot, subindex, roi, result):
        assert slot == self.ConcatenatedOutput
        
        pool = RequestPool()
        subresults = []
        for slot in self.FeatureMatrices:
            subresults.append([None])
            req = slot[:].writeInto( subresults[-1] )
            # TODO: Progress...
            pool.add(req)
        pool.wait()

        # Since the subresults are returned in 'value' slots,
        #  we have to unpack them from their single-element lists.
        subresult_list = list( itertools.chain(*subresults) )
        
        total_matrix = numpy.concatenate( subresult_list, axis=0 )
        result[0] = total_matrix        
    
    def propagateDirty(self, slot, subindex, roi):
        self.ConcatenatedOutput.setDirty()
    
    

