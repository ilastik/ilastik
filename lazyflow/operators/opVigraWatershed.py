from lazyflow.graph import Operator, InputSlot, OutputSlot

import numpy
import vigra
import logging

logger = logging.getLogger(__name__)

class OpVigraWatershed(Operator):
    """
    Operator wrapper for vigra's default watershed function.
    """
    name = "OpVigraWatershed"
    category = "Vigra"
    
    InputImage = InputSlot() 
    PaddingWidth = InputSlot() # Specifies the extra pixels around the border of the image to use when computing the watershed.
                               # (Region is clipped to the size of the input image.)
    
    Output = OutputSlot()
    
    def setupOutputs(self):
        self.Output.meta.assignFrom( self.InputImage.meta )
        self.Output.meta.dtype = numpy.uint32
    
    def getSlicings(self, roi):
        """
        Pad the given roi to obtain a new slicing to use for obtaining input data.
        Return the padded slicing and the slicing that returns the original roi within the padded data.
        """
        tags = self.InputImage.meta.axistags
        pairs = zip([tag.key for tag in tags], zip(roi.start, roi.stop) )
        slices = [(k, slice(start, stop)) for (k,(start, stop)) in pairs]

        # Compute the watershed over a larger area than requested (padded area)
        padding = self.PaddingWidth.value
        paddedSlices = [] # The requested slicing + padding
        outputSlices = [] # The slicing to get the requested slicing from the padded data
        for i,(key,s) in enumerate(slices):
            p = s
            if key in 'xyz':
                p_start = max(s.start - padding, 0)
                p_stop = min(s.stop + padding, self.InputImage.shape[i])
                p = slice(p_start, p_stop)

            paddedSlices += [p]
            o = slice( s.start - p.start, s.stop - p.start )
            outputSlices += [o]
        
        return paddedSlices, outputSlices
    
    def execute(self, slot, roi, result):
        if slot.name == 'Output':
            # Every request is computed on-the-fly.
            # (No caching)
            paddedSlices, outputSlices = self.getSlicings(roi)
            
            # Get input data
            inputRegion = self.InputImage[paddedSlices].wait()
            
            # Makes sure vigra will understand this type
            if inputRegion.dtype != numpy.uint8 and inputRegion.dtype != numpy.float32:
                inputRegion = inputRegion.astype('float32')
            
            # Convert to vigra array
            inputRegion = inputRegion.view(vigra.VigraArray)
            inputRegion.axistags = self.InputImage.meta.axistags

            # Reduce to 3-D (keep order of xyz axes)
            tags = self.InputImage.meta.axistags
            inputRegion = inputRegion.withAxes( *[tag.key for tag in tags if tag.key in 'xyz'] )
            logger.debug( 'inputRegion 3D shape:{}'.format(inputRegion.shape) )
            
            logger.debug( "roi={}".format(roi) )
            logger.debug( "paddedSlices={}".format(paddedSlices) )
            logger.debug( "outputSlices={}".format(outputSlices) )
            
            # This is where the magic happens
            logger.info( "Computing Watershed of block {}, dtype={}".format(paddedSlices, inputRegion.dtype) )
            watershed, maxLabel = vigra.analysis.watersheds(inputRegion)
            logger.info( "Finished Watershed" )
            
            logger.debug( "watershed 3D output shape={}".format(watershed.shape) )
            logger.debug( "maxLabel={}".format(maxLabel) )

            # Promote back to 5-D
            watershed = watershed.withAxes( *[tag.key for tag in tags] )
            logger.debug( "watershed 5D shape: {}".format(watershed.shape) )
            logger.debug( "watershed axistags: {}".format(watershed.axistags) )
            
            #print numpy.unique(watershed[outputSlices]).shape
            # Return only the region the user requested
            result[...] = watershed[outputSlices]

    def propagateDirty(self, inputSlot, roi):
        if not self.configured():
            self.Output.setDirty(slice(None))
        elif inputSlot.name == "InputImage":
            paddedSlicing, outputSlicing = self.getSlicings(roi)
            self.Output.setDirty(paddedSlicing)
        elif inputSlot.name == "PaddingWidth":
            self.Output.setDirty(slice(None))
        else:
            assert False, "Unknown input slot."

