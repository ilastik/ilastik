from functools import partial
import logging
logger = logging.getLogger(__name__)

import numpy

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.request import RequestLock, Request, RequestPool
from lazyflow.utility import OrderedSignal
from lazyflow.roi import getBlockBounds, getIntersectingBlocks, determineBlockShape

class OpFeatureMatrixCache(Operator):
    """
    - Request features and labels in blocks
    - For nonzero label pixels in each block, extract the label image
    - Cache the feature matrix for each block separately
    - Output the concatenation of all feature matrices
    
    Note: This operator does not currently have "NonZeroLabelBlocks" input slot.
          Instead, it only requests labels for blocks that have been
          marked dirty via dirty notifications from the LabelImage slot.
          As a result, you MUST connect/configure this operator before you 
          load your upstream label cache with values.
          This operator must already be "watching" when when the label operator 
          is initialized with its first labels.
    """    
    FeatureImage = InputSlot()
    LabelImage = InputSlot()
    
    # Output is a single 'value', which is a 2D ndarray.
    # The first row is labels, the rest are the features.
    # (As a consequence of this, labels are converted to float)
    LabelAndFeatureMatrix = OutputSlot()
    
    ProgressSignal = OutputSlot()   # For convenience of passing several progress signals 
                                    # to a downstream operator (such as OpConcatenateFeatureMatrices),  
                                    # we provide the progressSignal member as an output slot.

    MAX_BLOCK_PIXELS = 1e6

    def __init__(self, *args, **kwargs):
        super(OpFeatureMatrixCache, self).__init__(*args, **kwargs)
        self._lock = RequestLock()
        
        self.progressSignal = OrderedSignal()
        self._progress_lock = RequestLock()
        
        self._blockshape = None
        self._dirty_blocks = set()
        self._blockwise_feature_matrices = {}
        self._block_locks = {} # One lock per stored block

        self._init_blocks(None, None)
        
    def _init_blocks(self, input_shape, new_blockshape):
        old_blockshape = self._blockshape
        if new_blockshape == old_blockshape:
            # Nothing to do
            return
        
        if ( len(self._dirty_blocks) != 0
             or len(self._blockwise_feature_matrices) != 0):
            raise RuntimeError("It's too late to change the dimensionality of your data after you've already started training.\n"
                               "Delete all your labels and try again.")

        # In these set/dict members, the block id (dict key) 
        #  is simply the block's start coordinate (as a tuple)
        self._blockshape = new_blockshape
        logger.debug("Initialized with blockshape: {}".format(new_blockshape))
    
    def setupOutputs(self):
        # We assume that channel the last axis
        assert self.FeatureImage.meta.getAxisKeys()[-1] == 'c'
        assert self.LabelImage.meta.getAxisKeys()[-1] == 'c'
        assert self.LabelImage.meta.shape[-1] == 1
        
        # For now, we assume that the two input images have the same shape (except channel)
        # This constraint could be relaxed in the future if necessary
        assert self.FeatureImage.meta.shape[:-1] == self.LabelImage.meta.shape[:-1],\
            "FeatureImage and LabelImage shapes do not match: {} vs {}"\
            "".format( self.FeatureImage.meta.shape, self.LabelImage.meta.shape )
    
        self.LabelAndFeatureMatrix.meta.shape = (1,)
        self.LabelAndFeatureMatrix.meta.dtype = object
        self.LabelAndFeatureMatrix.meta.channel_names = self.FeatureImage.meta.channel_names
        
        num_feature_channels = self.FeatureImage.meta.shape[-1]
        if num_feature_channels != self.LabelAndFeatureMatrix.meta.num_feature_channels:
            self.LabelAndFeatureMatrix.meta.num_feature_channels = num_feature_channels
            self.LabelAndFeatureMatrix.setDirty()

        self.ProgressSignal.meta.shape = (1,)
        self.ProgressSignal.meta.dtype = object
        self.ProgressSignal.setValue( self.progressSignal )

        # Auto-choose a blockshape
        tagged_shape = self.LabelImage.meta.getTaggedShape()
        if 't' in tagged_shape:
            # A block should never span multiple time slices.
            # For txy volumes, that could lead to lots of extra features being computed.
            tagged_shape['t'] = 1
        blockshape = determineBlockShape( tagged_shape.values(), OpFeatureMatrixCache.MAX_BLOCK_PIXELS )

        # Don't span more than 256 px along any axis
        blockshape = tuple(min(x, 256) for x in blockshape)
        self._init_blocks(self.LabelImage.meta.shape, blockshape)
        
    def execute(self, slot, subindex, roi, result):
        assert slot == self.LabelAndFeatureMatrix
        self.progressSignal(0.0)

        # Technically, this could result in strange progress reporting if execute() 
        #  is called by multiple threads in parallel.
        # This could be fixed with some fancier progress state, but 
        # (1) We don't expect that to by typical, and
        # (2) progress reporting is merely informational.
        num_dirty_blocks = len( self._dirty_blocks )
        remaining_dirty = [num_dirty_blocks]
        def update_progress( result ):
            remaining_dirty[0] -= 1
            percent_complete = 95.0*(num_dirty_blocks - remaining_dirty[0])/num_dirty_blocks
            self.progressSignal( percent_complete )

        # Update all dirty blocks in the cache
        logger.debug( "Updating {} dirty blocks".format(num_dirty_blocks) )

        # Before updating the blocks, ensure that the necessary block locks exist
        # It's better to do this now instead of inside each request
        #  to avoid contention over self._lock
        with self._lock:
            for block_start in self._dirty_blocks:
                if block_start not in self._block_locks:
                    self._block_locks[block_start] = RequestLock()

        # Update each block in its own request.
        pool = RequestPool()
        reqs = {}
        for block_start in self._dirty_blocks:
            req = Request( partial(self._get_features_for_block, block_start ) )
            req.notify_finished( update_progress )
            reqs[block_start] = req
            pool.add( req )
        pool.wait()

        # Now store the results we got.
        # It's better to store the blocks here -- rather than within each request -- to 
        #  avoid contention over self._lock from within every block's request.
        with self._lock:
            for block_start, req in reqs.items():
                if req.result is None:
                    # 'None' means the block wasn't dirty. No need to update.
                    continue
                labels_and_features_matrix = req.result
                self._dirty_blocks.remove(block_start)
                
                if labels_and_features_matrix.shape[0] > 0:
                    # Update the block entry with the new matrix.
                    self._blockwise_feature_matrices[block_start] = labels_and_features_matrix
                else:
                    # All labels were removed from the block,
                    # So the new feature matrix is empty.  
                    # Just delete its entry from our list.
                    try:
                        del self._blockwise_feature_matrices[block_start]
                    except KeyError:
                        pass

        # Concatenate the all blockwise results
        if self._blockwise_feature_matrices:
            total_feature_matrix = numpy.concatenate( self._blockwise_feature_matrices.values(), axis=0 )
        else:
            # No label points at all.
            # Return an empty label&feature matrix (of the correct shape)
            num_feature_channels = self.FeatureImage.meta.shape[-1]
            total_feature_matrix = numpy.ndarray( shape=(0, 1 + num_feature_channels), dtype=numpy.float32 )

        self.progressSignal(100.0)
        logger.debug( "After update, there are {} clean blocks".format( len(self._blockwise_feature_matrices) ) )
        result[0] = total_feature_matrix

    def propagateDirty(self, slot, subindex, roi):
        assert slot == self.FeatureImage or slot == self.LabelImage

        # Our blocks are tracked by label roi (1 channel)
        roi = roi.copy()
        roi.start[-1] = 0
        roi.stop[-1] = 1
        # Bookkeeping: Track the dirty blocks
        block_starts = getIntersectingBlocks( self._blockshape, (roi.start, roi.stop) )
        block_starts = map( tuple, block_starts )
        
        # 
        # If the features were dirty (not labels), we only really care about
        #  the blocks that are actually stored already
        # For big dirty rois (e.g. the entire image), 
        #  we avoid a lot of unnecessary entries in self._dirty_blocks
        if slot == self.FeatureImage:
            block_starts = set( block_starts ).intersection( self._blockwise_feature_matrices.keys() )

        with self._lock:
            self._dirty_blocks.update( block_starts )

        # Output has no notion of roi. It's all dirty.
        self.LabelAndFeatureMatrix.setDirty()

    def _get_features_for_block(self, block_start):
        """
        Computes the feature matrix for the given block IFF the block is dirty.
        Otherwise, returns None.
        """
        # Caller must ensure that the lock for this block already exists!
        with self._block_locks[block_start]:
            if block_start not in self._dirty_blocks:
                # Nothing to do if this block isn't actually dirty
                # (For parallel requests, its theoretically possible.)
                return None
            block_roi = getBlockBounds( self.LabelImage.meta.shape, self._blockshape, block_start )
            # TODO: Shrink the requested roi using the nonzero blocks slot...
            #       ...or just get rid of the nonzero blocks slot...
            labels_and_features_matrix = self._extract_feature_matrix(block_roi)
            return labels_and_features_matrix

    def _extract_feature_matrix(self, label_block_roi):
        num_feature_channels = self.FeatureImage.meta.shape[-1]
        labels = self.LabelImage(label_block_roi[0], label_block_roi[1]).wait()
        label_block_positions = numpy.nonzero(labels[...,0].view(numpy.ndarray))
        labels_matrix = labels[label_block_positions].astype(numpy.float32).view(numpy.ndarray)
        
        if len(label_block_positions) == 0 or len(label_block_positions[0]) == 0:
            # No label points in this roi.
            # Return an empty label&feature matrix (of the correct shape)
            return numpy.ndarray( shape=(0, 1 + num_feature_channels), dtype=numpy.float32 )

        # Shrink the roi to the bounding box of nonzero labels
        block_bounding_box_start = numpy.array( map( numpy.min, label_block_positions ) )
        block_bounding_box_stop = 1 + numpy.array( map( numpy.max, label_block_positions ) )
        
        global_bounding_box_start = block_bounding_box_start + label_block_roi[0][:-1]
        global_bounding_box_stop  = block_bounding_box_stop + label_block_roi[0][:-1]

        # Since we're just requesting the bounding box, offset the feature positions by the box start
        bounding_box_positions = numpy.transpose( numpy.transpose(label_block_positions) - numpy.array(block_bounding_box_start) )
        bounding_box_positions = tuple(bounding_box_positions)

        # Append channel roi (all feature channels)
        feature_roi_start = list(global_bounding_box_start) + [0]
        feature_roi_stop = list(global_bounding_box_stop) + [num_feature_channels]

        # Request features (bounding box only)
        features = self.FeatureImage(feature_roi_start, feature_roi_stop).wait()

        # Cast as plain ndarray (not VigraArray), since we don't need/want axistags
        features_matrix = features[bounding_box_positions].view(numpy.ndarray)
        return numpy.concatenate( (labels_matrix, features_matrix), axis=1)

        