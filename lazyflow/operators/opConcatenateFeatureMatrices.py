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
        self._num_feature_channels = 0 # Not including the labels...
        self._channel_names = []

    def setupOutputs(self):
        self.ConcatenatedOutput.meta.shape = (1,)
        self.ConcatenatedOutput.meta.dtype = object
        if len(self.FeatureMatrices) == 0:
            return
        
        num_feature_channels = self.FeatureMatrices[0].meta.num_feature_channels
        channel_names = self.FeatureMatrices[0].meta.channel_names
        for slot in self.FeatureMatrices:
            if slot.meta.num_feature_channels != num_feature_channels:
                logger.debug("Input matrices have the wrong number of channels")
                self.ConcatenatedOutput.meta.NOTREADY = True
                return
            if slot.meta.channel_names != channel_names:
                logger.debug("Input matrices have different channel names")
                self.ConcatenatedOutput.meta.NOTREADY = True
                return
        
        self.ConcatenatedOutput.meta.num_feature_channels = num_feature_channels
        self.ConcatenatedOutput.meta.channel_names = channel_names
        
        if ( num_feature_channels != self._num_feature_channels or
             channel_names != self._channel_names ):
            self._num_feature_channels = num_feature_channels
            self._channel_names = channel_names

            # If the number of features changed, we want to notify downstream 
            #  caches that the old feature matrices are dirty.
            # (For some reason the normal dirty notification mechanism doesn't work in this case.)
            self.ConcatenatedOutput.setDirty()
    
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
    
    

