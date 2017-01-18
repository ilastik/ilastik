from __future__ import division
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
#		   http://ilastik.org/license/
###############################################################################
import numpy
import vigra
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.operators import OpArrayCache
from lazyflow.utility import Timer

import logging
logger = logging.getLogger(__name__)

class OpMaskedWatershed(Operator):
    """
    Performs a seeded watershed within a masked region.
    The masking is achieved using using vigra's terminate=StopAtThreshold feature.
    """
    Input = InputSlot(optional=True) # If no input is given, output is voronoi within the masked region.
    Mask = InputSlot() # Watershed will only be computed for pixels where mask=True
    Seeds = InputSlot()    
    
    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super( OpMaskedWatershed, self ).__init__(*args, **kwargs)

        # Use an internal operator to prepare the data, 
        #  for easy caching/parallelization.
        self._opPrepInput = _OpPrepWatershedInput( parent=self )
        self._opPrepInput.Input.connect( self.Input )
        self._opPrepInput.Mask.connect( self.Mask )
        
        self._opPreppedInputCache = OpArrayCache( parent=self )
        self._opPreppedInputCache.Input.connect( self._opPrepInput.Output )

    def setupOutputs(self):
        if self.Input.ready():
            assert self.Input.meta.drange is not None, "Masked watershed requires input drange to be specified"

        # Cache the prepared input in 8 blocks
        blockshape = numpy.array( self._opPrepInput.Output.meta.shape ) // 2
        blockshape = numpy.maximum( 1, blockshape )
        self._opPreppedInputCache.blockShape.setValue( tuple(blockshape) )
        
        self.Output.meta.assignFrom( self.Mask.meta )
        self.Output.meta.dtype = numpy.uint32

    def execute(self, slot, subindex, roi, result):
        # The input preparation involves converting to uint8 and combining 
        #  the mask so we can use the StopAtThreshold mechanism
        with Timer() as prep_timer:
            input_data = self._opPreppedInputCache.Output(roi.start, roi.stop).wait()
        logger.debug("Input prep took {} seconds".format( prep_timer.seconds() ) )

        input_axistags = self._opPrepInput.Output.meta.axistags
        max_input_value = self._opPrepInput.Output.meta.drange[1]

        seeds = self.Seeds(roi.start, roi.stop).wait()
        
        # The input_data has max value outside the mask area.
        # Discard seeds outside the mask
        seeds[input_data == max_input_value] = 0

        # Reduce to 3-D (keep order of xyz axes)
        tags = input_axistags
        axes3d = "".join( [tag.key for tag in tags if tag.key in 'xyz'] )
        
        input_view = vigra.taggedView( input_data, input_axistags )
        input_view = input_view.withAxes( *axes3d )
        input_view = vigra.taggedView( input_view, axes3d )
        
        seeds_view = vigra.taggedView( seeds, self.Seeds.meta.axistags )
        seeds_view = seeds_view.withAxes( *axes3d )
        seeds_view = seeds_view.astype( numpy.uint32 )
        
        result_view = vigra.taggedView( result, self.Output.meta.axistags )
        result_view = result_view.withAxes( *axes3d )
        result_view = vigra.taggedView( result_view, axes3d )
        
        with Timer() as watershed_timer:
            # The 'watershedsNew' function is faster and supports StopAtThreshold even in turbo mode
            _, maxLabel = vigra.analysis.watershedsNew( input_view,
                                                        seeds=seeds_view,
                                                        out=result_view,
                                                        method='turbo',
                                                        terminate=vigra.analysis.SRGType.StopAtThreshold,
                                                        max_cost=max_input_value-1 )

        logger.debug( "vigra.watershedsNew() took {} seconds ({} seeds)"
                      .format( watershed_timer.seconds(), maxLabel ) )
        return result

    def propagateDirty(self, slot, subindex, roi):
        self.Output.setDirty()

class _OpPrepWatershedInput(Operator):
    """
    The vigra watershed API doesn't natively support the notion of a "mask" for the watershed,
    but a nearly identical effect can be achieved using vigra's "StopAtTheshold" termination criteria.
    For all pixels outside the mask, we set the input data to 255, and tell vigra to use 254 as the max_cost.
    But before we can apply the mask, we have to bump down the value of any "naturally ocurring" 255 pixels in the input data. 
    """
    Input = InputSlot(optional=True)
    Mask = InputSlot()
    
    Output = OutputSlot()
    
    def setupOutputs(self):
        if self.Input.ready():
            self.Output.meta.assignFrom(self.Input.meta)
            self.Output.meta.drange = (0,255)
        else:
            self.Output.meta.assignFrom(self.Mask.meta)
            self.Output.meta.drange = (0,1)
        self.Output.meta.dtype = numpy.uint8
    
    def execute(self, slot, subindex, roi, result):
        mask = self.Mask(roi.start, roi.stop).wait()
        
        if self.Input.ready():
            assert self.Input.meta.drange is not None or self.Input.meta.dtype != numpy.uint8,\
                "Can't use OpMaskedWatershed on images with no drange (except for uint8 images)."
            
            input_data = self.Input(roi.start, roi.stop).wait()
            
            # We achieve a "masked" watershed by setting the masked area 
            # to an input value that is higher than anything else in the image, 
            # and then using the 'stopAtThreshold' feature of the vigra watershed
            drange = self.Input.meta.drange
            # Convert to uint8 if possible for performance reasons.
            assert self.Input.meta.drange is not None or self.Input.meta.dtype == numpy.uint8
            if self.Input.meta.dtype != numpy.uint8:
                drange = self.Input.meta.drange
                input_data = numpy.asarray(input_data, dtype=numpy.float32)
                input_data -= drange[0]
                input_data /= (drange[1] - drange[0])
                input_data *= 255.0
                input_data = input_data.astype(numpy.uint8)
            
            # We need to use the highest value (e.g. 255) for the mask
            stopping_threshold = numpy.iinfo(input_data.dtype).max

            # If the input happens to contain that value already, nudge it down.
            input_data[input_data == stopping_threshold] = stopping_threshold-1
            
            # Replace masked-out pixels with the mask_value
            input_data[:] = numpy.where( mask, input_data, stopping_threshold )
        else:
            # Use a zero input (voronoi diagram, except for the mask)
            input_data = numpy.asarray(mask, numpy.uint8)
            numpy.logical_not(input_data, out=input_data)

        result[:] = input_data
        return result

    def propagateDirty(self, slot, subindex, roi):
        self.Output.setDirty(roi.start, roi.stop)
    