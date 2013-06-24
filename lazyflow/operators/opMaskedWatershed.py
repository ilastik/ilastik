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

        if self.Input.ready():
            inputImage = self.Input(roi.start, roi.stop).wait()
            # We achieve a "masked" watershed by setting the masked area 
            # to an input value that is higher than anything else in the image, 
            # and then using the 'stopAtThreshold' feature of the vigra watershed
            drange = self.Input.meta.drange
            stopping_threshold = drange[1]
            if issubclass( self.Input.meta.dtype, numpy.floating ) or self.Input.meta.dtype is float:
                stopping_threshold += 0.5
            else:
                assert drange < numpy.iinfo(self.Input.meta.dtype).max, \
                    "Can't use OpMaskedWatershed if your image's drange max is the same as the dtype max (must leave some headroom)."
            numpy.logical_not( mask, out=mask )
            inputImage[:] = numpy.where( mask, stopping_threshold+1, inputImage )
        else:
            # Use a zero input (voronoi diagram, except for the mask)
            inputImage = numpy.asarray(mask, numpy.uint8)
            numpy.logical_not(inputImage, out=inputImage)
            stopping_threshold = 0
        
        _, maxLabel = vigra.analysis.watersheds( inputImage[0,...,0],
                                               seeds=seeds[0,...,0],
                                               out=result[0,...,0],
                                               method='RegionGrowing', 
                                               terminate=vigra.analysis.SRGType.StopAtThreshold,
                                               max_cost=stopping_threshold )

        return result

    def propagateDirty(self, slot, subindex, roi):
        self.Output.setDirty()

