###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the Lesser GNU General Public License
# as published by the Free Software Foundation; either version 2.1
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# See the files LICENSE.lgpl2 and LICENSE.lgpl3 for full text of the
# GNU Lesser General Public License version 2.1 and 3 respectively.
# This information is also available on the ilastik web site at:
#          http://ilastik.org/license/
###############################################################################

import sys
import numpy
from functools import partial

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.roi import getIntersectingRois, roiToSlice
from lazyflow.request import RequestPool

class OpSplitRequestsBlockwise(Operator):
    """
    Large requests serviced on the downstream Output will be broken up into smaller requests, 
    and requested in parallel from the upstream Input.
    The size of the smaller requests is determined by the BlockShape slot.
    A constructor argument offers an additional feature for exactly how requests are translated into blocks.
    """
    Input = InputSlot(allow_mask=True)
    BlockShape = InputSlot()
    Output = OutputSlot(allow_mask=True)

    def __init__(self, always_request_full_blocks, *args, **kwargs):
        """
        always_request_full_blocks: If True, requests for upstream data will always be the "full" block as specified
                                    by the BlockShape.  The requests will not be truncated to match the user's 
                                    requested ROI.  (But the user's requested ROI will be used to extract the data 
                                    from the block results.)
                                    
                                    This feature allows us to turn an "unblocked" cache into a "blocked" cache.
                                    (If we didn't expand requests to the full blocks they intersect, the upstream 
                                    cache blocks would not have uniform size.)                                    
        """
        super( OpSplitRequestsBlockwise, self ).__init__(*args, **kwargs)
        self._always_request_full_blocks = always_request_full_blocks
    
    def setupOutputs(self):
        self.Output.meta.assignFrom( self.Input.meta )
        if len(self.BlockShape.value) != len(self.Input.meta.shape):
            self.Output.meta.NOTREADY = True
            return
        self.Output.meta.ideal_blockshape = tuple(numpy.minimum(self.BlockShape.value, self.Input.meta.shape))

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

    def execute(self, slot, subindex, roi, result):
        clipped_block_rois = getIntersectingRois( self.Input.meta.shape, self.BlockShape.value, (roi.start, roi.stop), True )
        if self._always_request_full_blocks:
            full_block_rois = getIntersectingRois( self.Input.meta.shape, self.BlockShape.value, (roi.start, roi.stop), False )
        else:
            full_block_rois = clipped_block_rois
            
        pool = RequestPool()
        for full_block_roi, clipped_block_roi in zip( full_block_rois, clipped_block_rois ):
            full_block_roi = numpy.asarray(full_block_roi)
            clipped_block_roi = numpy.asarray(clipped_block_roi)

            req = self.Input(*full_block_roi)
            output_roi = numpy.asarray(clipped_block_roi) - roi.start
            if (full_block_roi == clipped_block_roi).all():
                req.writeInto( result[roiToSlice(*output_roi)] )
            else:
                roi_within_block = clipped_block_roi - full_block_roi[0]
                def copy_request_result( output_roi, roi_within_block, request_result ):
                    self.Output.stype.copy_data( result[roiToSlice(*output_roi)], request_result[roiToSlice(*roi_within_block)] )
                req.notify_finished( partial(copy_request_result, output_roi, roi_within_block) )
            pool.add(req)
            del req
        pool.wait()
    
    def propagateDirty(self, slot, subindex, roi):
        if slot is self.Input:
            self.Output.setDirty( roi.start, roi.stop )
