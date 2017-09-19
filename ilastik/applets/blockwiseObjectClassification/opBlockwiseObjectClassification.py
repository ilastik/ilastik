###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#		   http://ilastik.org/license.html
###############################################################################
# Built-in
from __future__ import division
import logging

# Third-party
import numpy

# lazyflow
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.request import RequestLock, RequestPool
from lazyflow.roi import getIntersectingBlocks, getBlockBounds, getIntersection, roiToSlice, TinyVector
from lazyflow.operators import OpSubRegion, OpMultiArrayStacker, OpBlockedArrayCache
from lazyflow.stype import Opaque
from lazyflow.rtype import List

# ilastik
from ilastik.utility import bind
from ilastik.applets.objectExtraction.opObjectExtraction import OpObjectExtraction
from ilastik.applets.objectClassification.opObjectClassification import OpObjectPredict, OpRelabelSegmentation, OpMaxLabel, OpMultiRelabelSegmentation
from ilastik.applets.base.applet import DatasetConstraintError

logger = logging.getLogger(__name__)
traceLogger = logging.getLogger("TRACE." + __name__)

class OpSingleBlockObjectPrediction( Operator ):
    RawImage = InputSlot()
    BinaryImage = InputSlot()

    SelectedFeatures = InputSlot(rtype = List, stype=Opaque)

    Classifier = InputSlot()
    LabelsCount = InputSlot()
    
    ObjectwisePredictions = OutputSlot(stype=Opaque, rtype=List)
    PredictionImage = OutputSlot()
    ProbabilityChannelImage = OutputSlot()
    BlockwiseRegionFeatures = OutputSlot() # Indexed by (t,c)

    # Schematic:
    #
    # RawImage -----> opRawSubRegion ------                        _______________________ 
    #                                      \                      /                       \
    # BinaryImage --> opBinarySubRegion --> opExtract --(features)--> opPredict --(map)--> opPredictionImage --via execute()--> PredictionImage
    #                                      /         \               /                    /
    #                 SelectedFeatures-----           \   Classifier                     /
    #                                                  \                                /
    #                                                   (labels)---------------------------> opProbabilityChannelsToImage

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
        self._opExtract.Features.connect(self.SelectedFeatures)
        self.BlockwiseRegionFeatures.connect( self._opExtract.BlockwiseRegionFeatures )
        
        self._opExtract._opRegFeats._opCache.name = "blockwise-regionfeats-cache"
        
        self._opPredict = OpObjectPredict( parent=self )
        self._opPredict.Features.connect( self._opExtract.RegionFeatures )
        self._opPredict.SelectedFeatures.connect( self.SelectedFeatures )
        self._opPredict.Classifier.connect( self.Classifier )
        self._opPredict.LabelsCount.connect( self.LabelsCount )
        self.ObjectwisePredictions.connect( self._opPredict.Predictions )
        
        self._opPredictionImage = OpRelabelSegmentation( parent=self )
        self._opPredictionImage.Image.connect( self._opExtract.LabelImage ) 
        self._opPredictionImage.Features.connect( self._opExtract.RegionFeatures )
        self._opPredictionImage.ObjectMap.connect( self._opPredict.Predictions )

        self._opPredictionCache = OpBlockedArrayCache( parent=self )
        self._opPredictionCache.Input.connect( self._opPredictionImage.Output )
        
        self._opProbabilityChannelsToImage = OpMultiRelabelSegmentation( parent=self )
        self._opProbabilityChannelsToImage.Image.connect( self._opExtract.LabelImage )
        self._opProbabilityChannelsToImage.ObjectMaps.connect( self._opPredict.ProbabilityChannels )
        self._opProbabilityChannelsToImage.Features.connect( self._opExtract.RegionFeatures )
        
        self._opProbabilityChannelStacker = OpMultiArrayStacker( parent=self )
        self._opProbabilityChannelStacker.Images.connect( self._opProbabilityChannelsToImage.Output )
        self._opProbabilityChannelStacker.AxisFlag.setValue('c')
        
        self._opProbabilityCache = OpBlockedArrayCache( parent=self )
        self._opProbabilityCache.Input.connect( self._opProbabilityChannelStacker.Output )

    def setupOutputs(self):
        tagged_input_shape = self.RawImage.meta.getTaggedShape()
        self._halo_roi = self.computeHaloRoi( tagged_input_shape, self._halo_padding, self.block_roi ) # In global coordinates
        
        # Output roi in our own coordinates (i.e. relative to the halo start)
        self._output_roi = self.block_roi - self._halo_roi[0]
        
        halo_start, halo_stop = list(map(tuple, self._halo_roi))
        
        self._opRawSubRegion.Roi.setValue( (halo_start, halo_stop) )

        # Binary image has only 1 channel.  Adjust halo subregion.
        assert self.BinaryImage.meta.getTaggedShape()['c'] == 1
        c_index = self.BinaryImage.meta.axistags.channelIndex
        binary_halo_roi = numpy.array(self._halo_roi)
        binary_halo_roi[:, c_index] = (0,1) # Binary has only 1 channel.
        binary_halo_start, binary_halo_stop = list(map(tuple, binary_halo_roi))
        
        self._opBinarySubRegion.Roi.setValue( (binary_halo_start, binary_halo_stop) )

        self.PredictionImage.meta.assignFrom( self._opPredictionImage.Output.meta )
        self.PredictionImage.meta.shape = tuple( numpy.subtract( self.block_roi[1], self.block_roi[0] ) )

        self.ProbabilityChannelImage.meta.assignFrom( self._opProbabilityChannelStacker.Output.meta )
        probability_shape = numpy.subtract( self.block_roi[1], self.block_roi[0] )
        probability_shape[-1] = self._opProbabilityChannelStacker.Output.meta.shape[-1]
        self.ProbabilityChannelImage.meta.shape = tuple(probability_shape)

        # Cache the entire block
        self._opPredictionCache.BlockShape.setValue( self._opPredictionCache.Input.meta.shape )
        self._opProbabilityCache.BlockShape.setValue( self._opProbabilityCache.Input.meta.shape )

        # Forward dirty regions to our own output
        self._opPredictionImage.Output.notifyDirty( self._handleDirtyPrediction )

    def execute(self, slot, subindex, roi, destination):
        assert slot is self.PredictionImage or slot is self.ProbabilityChannelImage, "Unknown input slot"
        assert (numpy.array(roi.stop) <= slot.meta.shape).all(), "Roi is out-of-bounds"

        # Extract from the output (discard halo)
        halo_offset = numpy.subtract(self.block_roi[0], self._halo_roi[0])
        adjusted_roi = ( halo_offset + roi.start,
                         halo_offset + roi.stop )
        if slot is self.PredictionImage:
            return self._opPredictionCache.Output(*adjusted_roi).writeInto(destination).wait()
        elif slot is self.ProbabilityChannelImage:
            return self._opProbabilityCache.Output(*adjusted_roi).writeInto(destination).wait()

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

            # Expand to all channels and set channel image dirty
            adjusted_roi[:,-1] = (0, self.ProbabilityChannelImage.meta.shape[-1])            
            self.ProbabilityChannelImage.setDirty( *adjusted_roi )

    @classmethod
    def computeHaloRoi(cls, tagged_dataset_shape, halo_padding, block_roi):
        block_roi = numpy.array(block_roi)
        block_start, block_stop = block_roi
        
        channel_index = list(tagged_dataset_shape.keys()).index('c')
        block_start[ channel_index ] = 0
        block_stop[ channel_index ] = tagged_dataset_shape['c']
        
        # Compute halo and clip to dataset bounds
        halo_start = block_start - halo_padding
        halo_start = numpy.maximum( halo_start, (0,)*len(halo_start) )

        halo_stop = block_stop + halo_padding
        halo_stop = numpy.minimum( halo_stop, list(tagged_dataset_shape.values()) )
        
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
    SelectedFeatures = InputSlot(rtype=List, stype=Opaque)
    BlockShape3dDict = InputSlot( value={'x' : 512, 'y' : 512, 'z' : 512} ) # A dict of SPATIAL block dims
    HaloPadding3dDict = InputSlot( value={'x' : 64, 'y' : 64, 'z' : 64} ) # A dict of spatial block dims

    PredictionImage = OutputSlot()
    ProbabilityChannelImage = OutputSlot()
    BlockwiseRegionFeatures = OutputSlot()
    
    def __init__(self, *args, **kwargs):
        super( self.__class__, self ).__init__(*args, **kwargs)
        self._blockPipelines = {} # indexed by blockstart
        self._lock = RequestLock()
        
    def setupOutputs(self):
        # Check for preconditions.
        if self.RawImage.ready() and self.BinaryImage.ready():
            rawTaggedShape = self.RawImage.meta.getTaggedShape()
            binTaggedShape = self.BinaryImage.meta.getTaggedShape()
            rawTaggedShape['c'] = None
            binTaggedShape['c'] = None
            if dict(rawTaggedShape) != dict(binTaggedShape):
                msg = "Raw data and other data must have equal dimensions (different channels are okay).\n"\
                      "Your datasets have shapes: {} and {}".format( self.RawImage.meta.shape, self.BinaryImage.meta.shape )
                raise DatasetConstraintError( "Blockwise Object Classification", msg )
        
        self._block_shape_dict = self.BlockShape3dDict.value
        self._halo_padding_dict = self.HaloPadding3dDict.value

        self.PredictionImage.meta.assignFrom( self.RawImage.meta )
        self.PredictionImage.meta.dtype = numpy.uint8 # Ultimately determined by meta.mapping_dtype from OpRelabelSegmentation
        prediction_tagged_shape = self.RawImage.meta.getTaggedShape()
        prediction_tagged_shape['c'] = 1
        self.PredictionImage.meta.shape = tuple( prediction_tagged_shape.values() )

        block_shape = self._getFullShape( self._block_shape_dict )
        self.PredictionImage.meta.ideal_blockshape = block_shape

        raw_ruprp = self.RawImage.meta.ram_usage_per_requested_pixel
        binary_ruprp = self.BinaryImage.meta.ram_usage_per_requested_pixel
        try:
            prediction_ruprp = max( raw_ruprp, binary_ruprp )
        except Exception:
            prediction_ruprp = None
            
        self.PredictionImage.meta.ram_usage_per_requested_pixel = prediction_ruprp

        self.ProbabilityChannelImage.meta.assignFrom( self.RawImage.meta )
        self.ProbabilityChannelImage.meta.dtype = numpy.float32
        prediction_channels_tagged_shape = self.RawImage.meta.getTaggedShape()
        prediction_channels_tagged_shape['c'] = self.LabelsCount.value
        self.ProbabilityChannelImage.meta.shape = tuple( prediction_channels_tagged_shape.values() )
        self.ProbabilityChannelImage.meta.ram_usage_per_requested_pixel = prediction_ruprp

        region_feature_output_shape = ( numpy.array( self.PredictionImage.meta.shape ) + block_shape - 1 ) // block_shape
        self.BlockwiseRegionFeatures.meta.shape = tuple(region_feature_output_shape)
        self.BlockwiseRegionFeatures.meta.dtype = object
        self.BlockwiseRegionFeatures.meta.axistags = self.PredictionImage.meta.axistags

        
    def execute(self, slot, subindex, roi, destination):
        if slot == self.PredictionImage or slot == self.ProbabilityChannelImage:
            return self._executePredictionImage( slot, roi, destination )
        elif slot == self.BlockwiseRegionFeatures:
            return self._executeBlockwiseRegionFeatures( roi, destination )
        else:
            assert False, "Unknown output slot: {}".format( slot.name )

    def _executePredictionImage(self, slot, roi, destination):
        roi_one_channel = numpy.array( (roi.start, roi.stop) )
        roi_one_channel[...,-1] = (0,1)
        # Determine intersecting blocks
        block_shape = self._getFullShape( self.BlockShape3dDict.value )
        block_starts = getIntersectingBlocks( block_shape, roi_one_channel )
        block_starts = list(map( tuple, block_starts ))

        # Ensure that block pipelines exist (create first if necessary)
        for block_start in block_starts:
            self._ensurePipelineExists(block_start)

        # Retrieve result from each block, and write into the appropriate region of the destination
        pool = RequestPool()
        for block_start in block_starts:
            opBlockPipeline = self._blockPipelines[block_start]
            block_roi = opBlockPipeline.block_roi
            block_intersection = getIntersection( block_roi, roi_one_channel )
            block_relative_intersection = numpy.subtract(block_intersection, block_roi[0])
            destination_relative_intersection = numpy.subtract(block_intersection, roi_one_channel[0])

            block_slot = opBlockPipeline.PredictionImage            
            if slot == self.ProbabilityChannelImage:
                block_slot = opBlockPipeline.ProbabilityChannelImage
                # Add channels back to roi
                block_relative_intersection[...,-1] = ( roi.start[-1], roi.stop[-1] )
                destination_relative_intersection[...,-1] = (0, roi.stop[-1] - roi.start[-1])

            # Request the data
            destination_slice = roiToSlice( *destination_relative_intersection )
            req = block_slot( *block_relative_intersection )
            req.writeInto( destination[destination_slice] )
            pool.add( req )
        pool.wait()

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
        block_starts = list(map( tuple, block_starts ))
        
        # TODO: Parallelize this?
        for block_start in block_starts:
            assert block_start in self._blockPipelines, "Not allowed to request region features for blocks that haven't yet been processed." # See note above

            # Discard spatial axes to get (t,c) index for region slot roi
            tagged_block_start = list(zip( axiskeys, block_start ))
            tagged_block_start_tc = [k_v for k_v in tagged_block_start if k_v[0] in 'tc']
            block_start_tc = [k_v1[1] for k_v1 in tagged_block_start_tc]
            block_roi_tc = ( block_start_tc, block_start_tc + numpy.array([1,1]) )
            block_roi_t = (block_roi_tc[0][:-1], block_roi_tc[1][:-1])

            assert sys.version_info.major == 2, "Alert! This loop has not been tested "\
            "under python 3. Please remove this assetion and be wary of any strnage behavior you encounter"
            destination_start = numpy.array(block_start) // block_shape - roi.start
            destination_stop = destination_start + numpy.array( [1]*len(axiskeys) )

            opBlockPipeline = self._blockPipelines[block_start]
            req = opBlockPipeline.BlockwiseRegionFeatures( *block_roi_t )
            destination_without_channel = destination[ roiToSlice( destination_start, destination_stop ) ]
            destination_with_channel = destination_without_channel[ ...,block_roi_tc[0][-1] : block_roi_tc[1][-1] ]
            req.writeInto( destination_with_channel )
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
            opBlockPipeline.SelectedFeatures.connect( self.SelectedFeatures )

            # Forward dirtyness
            opBlockPipeline.PredictionImage.notifyDirty( bind(self._handleDirtyBlock, block_start ) )
            
            self._blockPipelines[block_start] = opBlockPipeline

    def get_blockshape(self):
        return self._getFullShape(self.BlockShape3dDict.value)

    def get_block_roi(self, block_start):
        block_shape = self._getFullShape( self._block_shape_dict )
        input_shape = self.RawImage.meta.shape
        block_stop = getBlockBounds( input_shape, block_shape, block_start )[1]
        block_roi = (block_start, block_stop)
        return block_roi

    def is_in_block(self, block_start, coord):
        block_roi = self.get_block_roi(block_start)
        coord_roi = (coord, TinyVector( coord ) + 1)
        intersection = getIntersection(block_roi, coord_roi, False)
        return (intersection is not None)
        
    
    def _getFullShape(self, spatialShapeDict):
        # 't' should match raw input
        # 'c' should be 1 (output image has exactly 1 channel)
        # xyz come from spatialShapeDict
        axiskeys = self.RawImage.meta.getAxisKeys()
        shape = [0] * len(axiskeys)
        for i, k in enumerate(axiskeys):
            if k in 'xyz':
                shape[i] = spatialShapeDict[k]
            elif k == 'c':
                shape[i] = 1
            elif k == 't':
                shape[i] = 1
            else:
                assert False,  "Unknown axis key: '{}'".format( k )
        
        return shape

    
    def _deleteAllPipelines(self):
        logger.debug("Deleting all pipelines.")
        oldBlockPipelines = self._blockPipelines
        self._blockPipelines = {}
        with self._lock:
            for opBlockPipeline in list(oldBlockPipelines.values()):
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


























