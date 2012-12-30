import numpy
from lazyflow.roiRequestBatch import RoiRequestBatch
from lazyflow.roi import getIntersectingBlocks, getBlockBounds

class BigRequestStreamer(object):
    """
    Execute a big request by breaking it up into smaller requests.
    
    This class encapsulates the logic for dividing big rois into smaller ones to be executed separately.
    It relies on a RoiRequestBatch object, which is responsible for creating and scheduling the request for each roi.
    """
    def __init__(self, outputSlot, roi, minBlockShape):
        self._outputSlot = outputSlot
        self._bigRoi = roi
        self._minBlockShape = minBlockShape
        self._minBlockStarts = getIntersectingBlocks(minBlockShape, roi)
        self._requestedBlocks = numpy.zeros( self._minBlockStarts.shape[:-1], dtype=bool )
        
        totalVolume = numpy.prod( numpy.subtract(roi[1], roi[0]) )
        # For now, simply iterate over the min blocks
        # TODO: Auto-dialate block sizes based on CPU/RAM usage.
        def roiGen():
            block_iter = self._minBlockStarts.__iter__()
            while True:
                block_start = block_iter.next()
                yield getBlockBounds( self._outputSlot.meta.shape, minBlockShape, block_start )
        
        self._requestBatch = RoiRequestBatch( self._outputSlot, roiGen(), totalVolume, 10 )

    @property
    def progressSignal(self):
        return self._requestBatch.progressSignal

    @property
    def resultSignal(self):
        return self._requestBatch.resultSignal

    def execute(self):
        self._requestBatch.execute()
