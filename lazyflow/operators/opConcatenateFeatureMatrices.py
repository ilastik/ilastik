import itertools
from functools import partial
import logging
logger = logging.getLogger(__name__)

import numpy

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.request import RequestPool, RequestLock
from lazyflow.utility import OrderedSignal

class OpConcatenateFeatureMatrices(Operator):
    """
    Designed to receive a multi-slot of FeatureMatrix outputs from OpFeatureMatrixCache, 
    and concatenate the results into one big feature matrix.
    """
    FeatureMatrices = InputSlot(level=1) # Each subslot is a 'value' slot with a matrix as the value.
    ProgressSignals = InputSlot(level=1)

    ConcatenatedOutput = OutputSlot()
    
    def __init__(self, *args, **kwargs):
        super(OpConcatenateFeatureMatrices, self).__init__(*args, **kwargs)
        self._dirty_slots = set()
        self.progressSignal = OrderedSignal()

    def setupOutputs(self):
        self.ConcatenatedOutput.meta.shape = (1,)
        self.ConcatenatedOutput.meta.dtype = object
    
    def execute(self, slot, subindex, roi, result):
        assert slot == self.ConcatenatedOutput
        self.progressSignal(0.0)

        num_dirty_slots = len( self._dirty_slots )
        subtask_progress = {}
        progress_lock = RequestLock()
        def forward_progress_updates( feature_slot, progress ):
            with progress_lock:
                subtask_progress[feature_slot] = progress
                total_progress = 0.95*sum( subtask_progress.values() ) / num_dirty_slots
            self.progressSignal( total_progress )

        logger.debug( "Updating features for {} dirty images out of {}"\
                      "".format( len(self._dirty_slots), len(self.FeatureMatrices) ) )
        
        pool = RequestPool()
        subresults = []
        for feature_slot, progress_slot in zip(self.FeatureMatrices, self.ProgressSignals):
            subresults.append([None])
            req = feature_slot[:]
            req.writeInto( subresults[-1] )

            # Only use progress for slots that were dirty.
            # The others are going to be really fast.
            if feature_slot in self._dirty_slots:
                sub_progress_signal = progress_slot.value
                sub_progress_signal.subscribe( partial(forward_progress_updates, feature_slot ) )
            pool.add(req)
        pool.wait()

        # Reset dirty slots
        self._dirty_slots = set()

        # Since the subresults are returned in 'value' slots,
        #  we have to unpack them from their single-element lists.
        subresult_list = list( itertools.chain(*subresults) )
        
        total_matrix = numpy.concatenate( subresult_list, axis=0 )
        self.progressSignal(100.0)
        result[0] = total_matrix        
    
    def propagateDirty(self, slot, subindex, roi):
        if slot == self.FeatureMatrices:
            self._dirty_slots.add( self.FeatureMatrices[subindex] )
            self.ConcatenatedOutput.setDirty()
        else:
            assert slot == self.ProgressSignals, \
                "Unhandled dirty slot: {}".format( slot.name )
    
    

