import sys
import numpy
from functools import partial
from lazyflow.graph import Operator, InputSlot
from opUnblockedArrayCache import OpUnblockedArrayCache
from lazyflow.request import Request, RequestPool
from lazyflow.roi import getIntersectingRois, roiToSlice
from lazyflow.rtype import SubRegion

class OpSimpleBlockedArrayCache(OpUnblockedArrayCache):
    BlockShape = InputSlot(optional=True) # Must be a tuple.  Any 'None' elements will be interpreted as 'max' for that dimension.
    BypassModeEnabled = InputSlot(value=False)

    def __init__(self, *args, **kwargs):
        super( OpSimpleBlockedArrayCache, self ).__init__(*args, **kwargs)
        self._blockshape = None

    def setupOutputs(self):
        super( OpSimpleBlockedArrayCache, self ).setupOutputs()
        if self.BlockShape.ready():
            self._blockshape = self.BlockShape.value
        else:
            self._blockshape = self.Input.meta.shape

        if len(self._blockshape) != len(self.Input.meta.shape):
            self.Output.meta.NOTREADY = True
            return

        # Replace 'None' (or zero) with default (from Input shape)
        self._blockshape = tuple( numpy.where(self._blockshape, self._blockshape, self.Input.meta.shape) )

        self.Output.meta.ideal_blockshape = tuple(numpy.minimum(self._blockshape, self.Input.meta.shape))

        # Estimate ram usage per requested pixel
        ram_per_pixel = 0
        if self.Input.meta.dtype == object or self.Input.meta.dtype == numpy.object_:
            ram_per_pixel = sys.getsizeof(None)
        elif numpy.issubdtype(self.Input.meta.dtype, numpy.dtype):
            ram_per_pixel = self.Input.meta.dtype().nbytes
        
        # One 'pixel' includes all channels
        tagged_shape = self.Input.meta.getTaggedShape()
        if 'c' in tagged_shape:
            ram_per_pixel *= float(tagged_shape['c'])
        
        if self.Input.meta.ram_usage_per_requested_pixel is not None:
            ram_per_pixel = max( ram_per_pixel, self.Input.meta.ram_usage_per_requested_pixel )
        
        self.Output.meta.ram_usage_per_requested_pixel = ram_per_pixel        

    def _execute_Output(self, slot, subindex, roi, result):
        """
        Overridden from OpUnblockedArrayCache
        """
        def copy_block( full_block_roi, clipped_block_roi ):
            full_block_roi = numpy.asarray(full_block_roi)
            clipped_block_roi = numpy.asarray(clipped_block_roi)
            output_roi = numpy.asarray(clipped_block_roi) - roi.start

            block_roi = self._get_containing_block_roi( clipped_block_roi )
            
            # Skip cache and copy full block directly
            if self.BypassModeEnabled.value:
                full_block_data = self.Output.stype.allocateDestination( SubRegion(self.Output, *full_block_roi ) )

                self.Input(*full_block_roi).writeInto(full_block_data).block()
                
                roi_within_block = clipped_block_roi - full_block_roi[0]
                self.Output.stype.copy_data( result[roiToSlice(*output_roi)],
                                             full_block_data[roiToSlice(*roi_within_block)] )
            # If data data exists already or we can just fetch it without needing extra scratch space,
            # just call the base class
            elif block_roi is not None or (full_block_roi == clipped_block_roi).all():
                self._execute_Output_impl( clipped_block_roi, result[roiToSlice(*output_roi)] )
            elif self.Input.meta.dontcache:
                # Data isn't in the cache, but we don't need it in the cache anyway.
                self.Input(*clipped_block_roi).writeInto(result[roiToSlice(*output_roi)]).block()
            else:
                # Data doesn't exist yet in the cache.
                # Request the full block, but then discard the parts we don't need.
                
                # (We use allocateDestination() here to support MaskedArray types.)
                # TODO: We should probably just get rid of MaskedArray support altogether...
                full_block_data = self.Output.stype.allocateDestination( SubRegion(self.Output, *full_block_roi ) )
                self._execute_Output_impl( full_block_roi, full_block_data )
    
                roi_within_block = clipped_block_roi - full_block_roi[0]
                self.Output.stype.copy_data( result[roiToSlice(*output_roi)],
                                             full_block_data[roiToSlice(*roi_within_block)] )

        clipped_block_rois = getIntersectingRois( self.Input.meta.shape, self._blockshape, (roi.start, roi.stop), True )
        full_block_rois = getIntersectingRois( self.Input.meta.shape, self._blockshape, (roi.start, roi.stop), False )

        pool = RequestPool()
        for full_block_roi, clipped_block_roi in zip( full_block_rois, clipped_block_rois ):
            req = Request( partial( copy_block, full_block_roi, clipped_block_roi ) )
            pool.add(req)
        pool.wait()
        
    def propagateDirty(self, slot, subindex, roi):
        if slot in (self.BypassModeEnabled, self.BlockShape):
            return
        super(OpSimpleBlockedArrayCache, self ).propagateDirty(slot, subindex, roi)
