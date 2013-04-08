# Built-in
import logging
import collections

# Third-party
import numpy

# lazyflow
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.request import RequestLock
from lazyflow.roi import getIntersectingBlocks, getBlockBounds, getIntersection, roiToSlice
from lazyflow.operators import OpSubRegion

# ilastik
from ilastik.utility import bind
from ilastik.applets.objectExtraction.opObjectExtraction import OpObjectExtraction
from ilastik.applets.objectClassification.opObjectClassification import OpObjectPredict, OpRelabelSegmentation, OpMaxLabel

logger = logging.getLogger(__name__)
traceLogger = logging.getLogger("TRACE." + __name__)

class OpSingleBlockObjectPrediction( Operator ):
    RawImage = InputSlot()
    BinaryImage = InputSlot()

    Classifier = InputSlot()
    LabelsCount = InputSlot()
    
    PredictionImage = OutputSlot()
    BlockwiseRegionFeatures = OutputSlot() # Indexed by (t,c)

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
        self.BlockwiseRegionFeatures.connect( self._opExtract.BlockwiseRegionFeatures )
        
        self._opPredict = OpObjectPredict( parent=self )
        self._opPredict.Features.connect( self._opExtract.RegionFeatures )
        self._opPredict.Classifier.connect( self.Classifier )
        self._opPredict.LabelsCount.connect( self.LabelsCount )
        
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
    LabelsCount = InputSlot()
    BlockShape3dDict = InputSlot( value={'x' : 512, 'y' : 512, 'z' : 512} ) # A dict of SPATIAL block dims
    HaloPadding3dDict = InputSlot( value={'x' : 64, 'y' : 64, 'z' : 64} ) # A dict of spatial block dims

    PredictionImage = OutputSlot()
    BlockwiseRegionFeatures = OutputSlot()
    
    def __init__(self, *args, **kwargs):
        super( self.__class__, self ).__init__(*args, **kwargs)
        self._blockPipelines = {} # indexed by blockstart
        self._lock = RequestLock()
        
    def setupOutputs(self):
        # Check for preconditions.
        assert self.RawImage.meta.shape == self.BinaryImage.meta.shape, "Raw and binary images must have the same shape!"
        
        self.PredictionImage.meta.assignFrom( self.RawImage.meta )
        self.PredictionImage.meta.dtype = numpy.uint32 # (dtype ultimately comes from OpVigraLabelVolume)

        self._block_shape_dict = self.BlockShape3dDict.value
        self._halo_padding_dict = self.HaloPadding3dDict.value

        block_shape = self._getFullShape( self._block_shape_dict )
        
        region_feature_output_shape = ( numpy.array( self.PredictionImage.meta.shape ) + block_shape - 1 ) / block_shape
        self.BlockwiseRegionFeatures.meta.shape = tuple(region_feature_output_shape)
        self.BlockwiseRegionFeatures.meta.dtype = object
        self.BlockwiseRegionFeatures.meta.axistags = self.PredictionImage.meta.axistags
        
    def execute(self, slot, subindex, roi, destination):
        if slot == self.PredictionImage:
            return self._executePredictionImage( roi, destination )
        elif slot == self.BlockwiseRegionFeatures:
            return self._executeBlockwiseRegionFeatures( roi, destination )
        else:
            assert False, "Unknown output slot: {}".format( slot.name )

    def _executePredictionImage(self, roi, destination):
        # Determine intersecting blocks
        block_shape = self._getFullShape( self.BlockShape3dDict.value )
        block_starts = getIntersectingBlocks( block_shape, (roi.start, roi.stop) )
        block_starts = map( tuple, block_starts )

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

    def _executeBlockwiseRegionFeatures(self, roi, destination):
        """
        Provide data for the BlockwiseRegionFeatures slot.
        Note: Each block produces a single element of this slot's output.  Construct requested roi coordinates accordingly.
              e.g. if block_shape is (1,10,10,10,1), the features for the block starting at 
                   (1,20,30,40,5) should be requested via roi [(1,2,3,4,5),(2,3,4,5,6)]
        
        Note: It is assumed that you will request these features for debug purposes, AFTER requesting the prediction image.
              Therefore, it is considered an error to request features that are not already computed.
        """
        axiskeys = self.RawImage.meta.getAxisKeys()
        # Find the corresponding block start coordinates
        block_shape = self._getFullShape( self.BlockShape3dDict.value )
        pixel_roi = numpy.array(block_shape) * (roi.start, roi.stop)
        block_starts = getIntersectingBlocks( block_shape, pixel_roi )
        block_starts = map( tuple, block_starts )
        
        for block_start in block_starts:
            assert block_start in self._blockPipelines, "Not allowed to request region features for blocks that haven't yet been processed." # See note above

            # Discard spatial axes to get (t,c) index for region slot roi
            tagged_block_start = zip( axiskeys, block_start )
            tagged_block_start_tc = filter( lambda (k,v): k in 'tc', tagged_block_start )
            block_start_tc = map( lambda (k,v): v, tagged_block_start_tc )
            block_roi_tc = ( block_start_tc, block_start_tc + numpy.array([1,1]) )

            destination_start = numpy.array(block_start) / block_shape - roi.start
            destination_stop = destination_start + numpy.array( [1]*len(axiskeys) )

            opBlockPipeline = self._blockPipelines[block_start]
            req = opBlockPipeline.BlockwiseRegionFeatures( *block_roi_tc )
            req.writeInto( destination[ roiToSlice( destination_start, destination_stop ) ] )
            req.wait()
        
        return destination

    def _ensurePipelineExists(self, block_start):
        if block_start in self._blockPipelines:
            return
        with self._lock:
            if block_start in self._blockPipelines:
                return

            logger.debug( "Creating pipeline for block: {}".format( block_start ) )

            block_shape = self._getFullShape( self._block_shape_dict )
            halo_padding = self._getFullShape( self._halo_padding_dict )

            input_shape = self.RawImage.meta.shape
            block_stop = getBlockBounds( input_shape, block_shape, block_start )[1]
            block_roi = (block_start, block_stop)

            # Instantiate pipeline
            opBlockPipeline = OpSingleBlockObjectPrediction( block_roi, halo_padding, parent=self )
            opBlockPipeline.RawImage.connect( self.RawImage )
            opBlockPipeline.BinaryImage.connect( self.BinaryImage )
            opBlockPipeline.Classifier.connect( self.Classifier )
            opBlockPipeline.LabelsCount.connect( self.LabelsCount )

            # Forward dirtyness
            opBlockPipeline.PredictionImage.notifyDirty( bind(self._handleDirtyBlock, block_start ) )
            
            self._blockPipelines[block_start] = opBlockPipeline

    
    def _getFullShape(self, spatialShapeDict):
        axiskeys = self.RawImage.meta.getAxisKeys()
        # xyz block shape comes from input slot, but other axes are 1
        shape = [1] * len(axiskeys)
        for i, k in enumerate(axiskeys):
            if k in 'xyz':
                shape[i] = spatialShapeDict[k]
        return shape

    
    def _deleteAllPipelines(self):
        logger.debug("Deleting all pipelines.")
        oldBlockPipelines = self._blockPipelines
        self._blockPipelines = {}
        with self._lock:
            for opBlockPipeline in oldBlockPipelines.values():
                opBlockPipeline.cleanUp()
    
    
    def propagateDirty(self, slot, subindex, roi):
        if slot == self.BlockShape3dDict or slot == self.HaloPadding3dDict:
            self._deleteAllPipelines()
            self.PredictionImage.setDirty( slice(None) )
    
    
    def _handleDirtyBlock(self, block_start, slot, roi):
        # Convert roi from block coords to global coords
        block_relative_roi = (roi.start, roi.stop)
        global_roi = block_relative_roi + numpy.array(block_start)
        logger.debug("Setting roi dirty: {}".format(global_roi))
        self.PredictionImage.setDirty( *global_roi )


























