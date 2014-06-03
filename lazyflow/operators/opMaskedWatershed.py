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

class OpMaskedWatershed(Operator):
    """
    Performs a seeded watershed within a masked region.
    The masking achieved using using vigra's terminate=StopAtThreshold feature.
    """
    Input = InputSlot(optional=True) # If no input is given, output is voronoi within the masked region.
    Mask = InputSlot() # Watershed will only be computed for pixels where mask=True
    Seeds = InputSlot()    
    
    Output = OutputSlot()

    def setupOutputs(self):
        if self.Input.ready():
            assert self.Input.meta.drange is not None, "Masked watershed requires input drange to be specified"
        
        self.Output.meta.assignFrom( self.Mask.meta )
        self.Output.meta.dtype = numpy.uint32

    def execute(self, slot, subindex, roi, result):
        mask = self.Mask(roi.start, roi.stop).wait()
        seeds = self.Seeds(roi.start, roi.stop).wait()
        
        # Discard seeds outside the mask
        seeds[mask == 0] = 0

        if self.Input.ready():
            assert self.Input.meta.drange is not None or self.Input.meta.dtype != numpy.uint8,\
                "Can't use OpMaskedWatershed on images with no drange (except for uint8 images)."
            input_data = self.Input(roi.start, roi.stop).wait()
            input_axistags = self.Input.meta.axistags
            # We achieve a "masked" watershed by setting the masked area 
            # to an input value that is higher than anything else in the image, 
            # and then using the 'stopAtThreshold' feature of the vigra watershed
            drange = self.Input.meta.drange
            # Convert to uint8 if possible for performance reasons.
            if self.Input.meta.drange is not None and self.Input.meta.dtype != numpy.uint8:
                drange = self.Input.meta.drange
                input_data = numpy.asarray(input_data, dtype=numpy.float32)
                input_data -= drange[0]
                input_data /= (drange[1] - drange[0])
                input_data *= 255.0
                input_data = input_data.astype(numpy.uint8)
                drange = (0,255)
            
            # We need to use the highest value (e.g. 255) for the mask
            stopping_threshold = numpy.iinfo(input_data.dtype).max

            # If the input happens to contain that value already, nudge it down.
            input_data[input_data == stopping_threshold] = stopping_threshold-1
            
            # Invert the mask (we want to keep the watershed out of the non-mask pixels)    
            numpy.logical_not( mask, out=mask )
            
            # Replace masked-out pixels with the mask_value
            input_data[:] = numpy.where( mask, stopping_threshold, input_data )
        else:
            # Use a zero input (voronoi diagram, except for the mask)
            input_data = numpy.asarray(mask, numpy.uint8)
            numpy.logical_not(input_data, out=input_data)
            stopping_threshold = 1
            input_axistags = self.Mask.meta.axistags
        
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
        
        _, maxLabel = vigra.analysis.watersheds( volume=input_view,
                                                 seeds=seeds_view,
                                                 out=result_view,
                                                 method='RegionGrowing', # Turbo mode doesn't support masks :-(
                                                 terminate=vigra.analysis.SRGType.StopAtThreshold,
                                                 max_cost=stopping_threshold-1 )
        return result

    def propagateDirty(self, slot, subindex, roi):
        self.Output.setDirty()

