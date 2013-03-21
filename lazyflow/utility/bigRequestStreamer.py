import numpy
from lazyflow.utility import RoiRequestBatch
from lazyflow.roi import getIntersectingBlocks, getBlockBounds

import logging
logger = logging.getLogger(__name__)

class BigRequestStreamer(object):
    """
    Execute a big request by breaking it up into smaller requests.
    
    This class encapsulates the logic for dividing big rois into smaller ones to be executed separately.
    It relies on a RoiRequestBatch object, which is responsible for creating and scheduling the request for each roi.
    """
    def __init__(self, outputSlot, roi, minBlockShape, batchSize=None):
        self._outputSlot = outputSlot
        self._bigRoi = roi
        self._minBlockShape = minBlockShape
        
        if batchSize is None:
            batchSize=2

        # Align the blocking with the start of the roi
        offsetRoi = ([0] * len(roi[0]), numpy.subtract(roi[1], roi[0]))
        self._minBlockStarts = getIntersectingBlocks(minBlockShape, offsetRoi)
        self._minBlockStarts += roi[0] # Un-offset

        totalVolume = numpy.prod( numpy.subtract(roi[1], roi[0]) )
        # For now, simply iterate over the min blocks
        # TODO: Auto-dialate block sizes based on CPU/RAM usage.
        def roiGen():
            block_iter = self._minBlockStarts.__iter__()
            while True:
                block_start = block_iter.next()

                # Use offset blocking
                offset_block_start = block_start - self._bigRoi[0]
                offset_data_shape = numpy.subtract(self._bigRoi[1], self._bigRoi[0])
                offset_block_bounds = getBlockBounds( offset_data_shape, minBlockShape, offset_block_start )
                
                # Un-offset
                block_bounds = ( offset_block_bounds[0] + self._bigRoi[0],
                                 offset_block_bounds[1] + self._bigRoi[0] )
                logger.debug( "Requesting Roi: {}".format( block_bounds ) )
                yield block_bounds
        
        self._requestBatch = RoiRequestBatch( self._outputSlot, roiGen(), totalVolume, batchSize )

    @property
    def progressSignal(self):
        return self._requestBatch.progressSignal

    @property
    def resultSignal(self):
        return self._requestBatch.resultSignal

    def execute(self):
        self._requestBatch.execute()
