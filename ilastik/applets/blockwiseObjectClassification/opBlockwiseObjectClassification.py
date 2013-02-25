# Built-in
import logging
from functools import partial

# Third-party
import numpy

# lazyflow
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.request import RequestLock
from lazyflow.roi import getIntersectingBlocks, getBlockBounds, getIntersection, roiToSlice
from lazyflow.operators import OpSubRegion

# ilastik
from ilastik.applets.objectExtraction.opObjectExtraction import OpObjectExtraction
from ilastik.applets.objectClassification.opObjectClassification import OpObjectPredict, OpRelabelSegmentation

logger = logging.getLogger(__name__)
traceLogger = logging.getLogger("TRACE." + __name__)

class OpSingleBlockObjectPrediction( Operator ):
    RawImage = InputSlot()
    BinaryImage = InputSlot()

    Classifier = InputSlot()
    
    PredictionImage = OutputSlot()

    # Schematic:
    #
    # RawImage -----> opRawSubRegion ------                        _______________________ 
    #                                      \                      /                       \
    # BinaryImage --> opBinarySubRegion --> opExtract --(features)--> opPredict --(map)--> opPredictionImage --via execute()--> PredictionImage
    #                                                \               /                    /
    #                                                 \    Classifier                    /
    #                                                  \                                /
    #                                                   (labels)------------------------

    # +----------------------------------------------------------------+
    # | input_shape = RawImage.meta.shape                              |
    # |                                                                |
    # |                                                                |
    # |                                                                |
    # |                                                                |
    # |                                                                |
    # |                                                                |
    # |                    halo_shape = blockshape + 2*halo_padding    |
    # |                    +------------------------+                  |
    # |                    | halo_roi               |                  |
    # |                    | (for internal pipeline)|                  |
    # |                    |                        |                  |
    # |                    |  +------------------+  |                  |
    # |                    |  | block_roi        |  |                  |
    # |                    |  | (output shape)   |  |                  |
    # |                    |  |                  |  |                  |
    # |                    |  |                  |  |                  |
    # |                    |  |                  |  |                  |
    # |                    |  +------------------+  |                  |
    # |                    |                        |                  |
    # |                    |                        |                  |
    # |                    |                        |                  |
    # |                    +------------------------+                  |
    # |                                                                |
    # |                                                                |
    # |                                                                |
    # |                                                                |
    # |                                                                |
    # |                                                                |
    # |                                                                |
    # +----------------------------------------------------------------+

    def __init__(self, block_roi, halo_padding, *args, **kwargs):
        super( self.__class__, self ).__init__( *args, **kwargs )
        
        self.block_roi = block_roi # In global coordinates
        self._halo_padding = halo_padding
        
        self._opBinarySubRegion = OpSubRegion( parent=self )
        self._opBinarySubRegion.Input.connect( self.BinaryImage )
        
        self._opRawSubRegion = OpSubRegion( parent=self )
        self._opRawSubRegion.Input.connect( self.RawImage )
        
        self._opExtract = OpObjectExtraction( parent=self )
        self._opExtract.BinaryImage.connect( self._opBinarySubRegion.Output )
        self._opExtract.RawImage.connect( self._opRawSubRegion.Output )
        
        self._opPredict = OpObjectPredict( parent=self )
        self._opPredict.Features.connect( self._opExtract.RegionFeatures )
        self._opPredict.Classifier.connect( self.Classifier )
        
        self._opPredictionImage = OpRelabelSegmentation( parent=self )
        self._opPredictionImage.Image.connect( self._opExtract.LabelImage ) 
        self._opPredictionImage.Features.connect( self._opExtract.RegionFeatures )
        self._opPredictionImage.ObjectMap.connect( self._opPredict.Predictions )
        
    def setupOutputs(self):
        input_shape = self.RawImage.meta.shape
        self._halo_roi = self.computeHaloRoi( input_shape, self._halo_padding, self.block_roi ) # In global coordinates
        
        # Output roi in our own coordinates (i.e. relative to the halo start)
        self._output_roi = self.block_roi - self._halo_roi[0]
        
        halo_start = tuple(self._halo_roi[0])
        halo_stop = tuple(self._halo_roi[1])
        
        self._opBinarySubRegion.Start.setValue( halo_start )
        self._opBinarySubRegion.Stop.setValue( halo_stop )

        self._opRawSubRegion.Start.setValue( halo_start )
        self._opRawSubRegion.Stop.setValue( halo_stop )

        self.PredictionImage.meta.assignFrom( self._opPredictionImage.Output.meta )
        self.PredictionImage.meta.shape = tuple( numpy.subtract( self.block_roi[1], self.block_roi[0] ) )

        # Forward dirty regions to our own output
        self._opPredictionImage.Output.notifyDirty( self._handleDirtyPrediction )
    
    def execute(self, slot, subindex, roi, destination):
        assert slot == self.PredictionImage, "Unknown input slot"
        assert (numpy.array(roi.stop) <= self.PredictionImage.meta.shape).all(), "Roi is out-of-bounds"

        # Extract from the output (discard halo)
        halo_offset = numpy.subtract(self.block_roi[0], self._halo_roi[0])
        adjusted_roi = ( halo_offset + roi.start,
                         halo_offset + roi.stop )
        return self._opPredictionImage.Output(*adjusted_roi).writeInto(destination).wait()

    def propagateDirty(self, slot, subindex, roi):
        """
        Nothing to do here because dirty notifications are propagated 
        through our internal pipeline and forwarded to our output via 
        our notifyDirty handler.
        """
        pass
    
    def _handleDirtyPrediction(self, slot, roi):
        """
        Foward dirty notifications from our internal output slot to the external one,
        but first discard the halo and offset the roi to compensate for the halo.
        """
        # Discard halo.  dirtyRoi is in internal coordinates (i.e. relative to halo start)
        dirtyRoi = getIntersection( (roi.start, roi.stop), self._output_roi, assertIntersect=False )
        if dirtyRoi is not None:
            halo_offset = numpy.subtract(self.block_roi[0], self._halo_roi[0])
            adjusted_roi = dirtyRoi - halo_offset # adjusted_roi is in output coordinates (relative to output block start)
            self.PredictionImage.setDirty( *adjusted_roi )

    @classmethod
    def computeHaloRoi(cls, dataset_shape, halo_padding, block_roi):
        block_roi = numpy.array(block_roi)
        block_start, block_stop = block_roi
        # Compute halo and clip to dataset bounds
        halo_start = block_start - halo_padding
        halo_start = numpy.maximum( halo_start, (0,)*len(dataset_shape) )

        halo_stop = block_stop + halo_padding
        halo_stop = numpy.minimum( halo_stop, dataset_shape )
        
        halo_roi = (halo_start, halo_stop)
        return halo_roi


class OpBlockwiseObjectClassification( Operator ):
    """
    Handles prediction ONLY.  Training must be provided externally and loaded via the serializer.
    """
    RawImage = InputSlot()
    BinaryImage = InputSlot()
    Classifier = InputSlot()
    BlockShape = InputSlot()
    HaloPadding = InputSlot()

    PredictionImage = OutputSlot()
    
    def __init__(self, *args, **kwargs):
        super( self.__class__, self ).__init__(*args, **kwargs)
        self._blockPipelines = {} # indexed by blockstart
        self._lock = RequestLock()
        
    def setupOutputs(self):
        self.PredictionImage.meta.assignFrom( self.RawImage.meta )
        self.PredictionImage.meta.dtype = numpy.uint32 # (dtype ultimately comes from OpVigraLabelVolume)
        
    def execute(self, slot, subindex, roi, destination):
        assert slot == self.PredictionImage, "Unknown Output Slot"

        # Determine intersecting blocks
        block_shape = self.BlockShape.value
        block_starts = getIntersectingBlocks( block_shape, (roi.start, roi.stop) )
        block_starts = map( lambda x: tuple(x), block_starts )

        # Ensure that block pipelines exist (create first if necessary)
        for block_start in block_starts:
            self._ensurePipelineExists(block_start)

        # Retrieve result from each block, and write into the approprate region of the destination
        # TODO: Parallelize this loop
        for block_start in block_starts:
            opBlockPipeline = self._blockPipelines[block_start]
            block_roi = opBlockPipeline.block_roi
            block_intersection = getIntersection( block_roi, (roi.start, roi.stop) )
            block_relative_intersection = numpy.subtract(block_intersection, block_roi[0])
            destination_relative_intersection = numpy.subtract(block_intersection, roi.start)
            
            destination_slice = roiToSlice( *destination_relative_intersection )
            req = opBlockPipeline.PredictionImage( *block_relative_intersection )
            req.writeInto( destination[destination_slice] )
            req.wait()

        return destination

    def _ensurePipelineExists(self, block_start):
        if block_start in self._blockPipelines:
            return
        with self._lock:
            if block_start in self._blockPipelines:
                return

            logger.debug( "Creating pipeline for block: {}".format( block_start ) )

            # Compute parameters
            block_shape = self.BlockShape.value
            halo_padding = self.HaloPadding.value
            input_shape = self.RawImage.meta.shape
            block_stop = getBlockBounds( input_shape, block_shape, block_start )[1]
            block_roi = (block_start, block_stop)

            # Instantiate pipeline
            opBlockPipeline = OpSingleBlockObjectPrediction( block_roi, halo_padding, parent=self )
            opBlockPipeline.RawImage.connect( self.RawImage )
            opBlockPipeline.BinaryImage.connect( self.BinaryImage )
            opBlockPipeline.Classifier.connect( self.Classifier )
            
            # Forward dirtyness
            opBlockPipeline.PredictionImage.notifyDirty( partial(self._handleDirtyBlock, block_start ) )
            
            self._blockPipelines[block_start] = opBlockPipeline
    
    def propagateDirty(self, slot, subindex, roi):
        pass # Dirtyness from each block is propagated via our notifyDirty handler (below)
    
    def _handleDirtyBlock(self, block_start, slot, roi):
        # Convert roi from block coords to global coords
        block_relative_roi = (roi.start, roi.stop)
        global_roi = block_relative_roi + numpy.array(block_start)
        logger.debug("Setting roi dirty: {}".format(global_roi))
        self.PredictionImage.setDirty( *global_roi )


























