import numpy
import h5py
import os

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.roi import roiToSlice
from lazyflow.operators import OpSlicedBlockedArrayCache, OpMultiArraySlicer2
from lazyflow.operators import OpPixelFeaturesPresmoothed as OpPixelFeaturesPresmoothed_Original
from lazyflow.operators import OpPixelFeaturesInterpPresmoothed as OpPixelFeaturesPresmoothed_Interpolated
from lazyflow.operators.imgFilterOperators import OpPixelFeaturesPresmoothed as OpPixelFeaturesPresmoothed_Refactored
#from lazyflow.operators.imgFilterOperators import OpPixelFeaturesPresmoothed

class OpFeatureSelection(Operator):
    """
    The top-level operator for the feature selection applet.
    """
    name = "OpFeatureSelection"
    category = "Top-level"

    # Multiple input images
    InputImage = InputSlot()

    # The following input slots are applied uniformly to all input images
    Scales = InputSlot() # The list of possible scales to use when computing features
    FeatureIds = InputSlot() # The list of features to compute
    SelectionMatrix = InputSlot() # A matrix of bools indicating which features to output.
                         # The matrix rows correspond to feature types in the order specified by the FeatureIds input.
                         #  (See OpPixelFeaturesPresmoothed for the available feature types.)
                         # The matrix columns correspond to the scales provided in the Scales input,
                         #  which requires that the number of matrix columns must match len(Scales.value)
    FeatureListFilename = InputSlot(stype="str", optional=True)
    
    # Features are presented in the channels of the output image
    # Output can be optionally accessed via an internal cache.
    # (Training a classifier benefits from caching, but predicting with an existing classifier does not.)
    OutputImage = OutputSlot()
    CachedOutputImage = OutputSlot()

    FeatureLayers = OutputSlot(level=1) # For the GUI, we also provide each feature as a separate slot in this multislot

    # For ease of development and testing, the underlying feature computation implementation 
    #  can be switched via a constructor argument.  These are the possible choices.
    FilterImplementations = ['Original', 'Refactored', 'Interpolated']
    
    def __init__(self, filter_implementation, *args, **kwargs):
        super(OpFeatureSelection, self).__init__(*args, **kwargs)

        # Create the operator that actually generates the features
        if filter_implementation == 'Original':
            self.opPixelFeatures = OpPixelFeaturesPresmoothed_Original(parent=self)
        elif filter_implementation == 'Refactored':
            self.opPixelFeatures = OpPixelFeaturesPresmoothed_Refactored(parent=self)
        elif filter_implementation == 'Interpolated':
            self.opPixelFeatures = OpPixelFeaturesPresmoothed_Interpolated(parent=self)
            self.opPixelFeatures.InterpolationScaleZ.setValue(2)
        else:
            assert False, "Unknown filter implementation option: {}".format( filter_implementation )

        # Create the cache
        self.opPixelFeatureCache = OpSlicedBlockedArrayCache(parent=self)
        self.opPixelFeatureCache.name = "opPixelFeatureCache"

        # Connect the cache to the feature output
        self.opPixelFeatureCache.Input.connect(self.opPixelFeatures.Output)
        self.opPixelFeatureCache.fixAtCurrent.setValue(False)

        # Connect our internal operators to our external inputs 
        self.opPixelFeatures.Scales.connect( self.Scales )
        self.opPixelFeatures.FeatureIds.connect( self.FeatureIds )
        self.opPixelFeatures.Matrix.connect( self.SelectionMatrix )
        self.opPixelFeatures.Input.connect( self.InputImage )

    def setupOutputs(self):        
        if self.FeatureListFilename.ready() and len(self.FeatureListFilename.value) > 0:
            f = open(self.FeatureListFilename.value, 'r')
            self._files = []
            for line in f:
                line = line.strip()
                if len(line) > 0:
                    self._files.append(line)
            f.close()
            
            self.OutputImage.disconnect()
            self.CachedOutputImage.disconnect()
            self.FeatureLayers.disconnect()
            
            axistags = self.inputs["InputImage"].meta.axistags
            
            self.FeatureLayers.resize(len(self._files))
            for i in range(len(self._files)):
                f = h5py.File(self._files[i], 'r')
                shape = f["data"].shape
                assert len(shape) == 3
                dtype = f["data"].dtype
                f.close()
                self.FeatureLayers[i].meta.shape    = shape+(1,)
                self.FeatureLayers[i].meta.dtype    = dtype
                self.FeatureLayers[i].meta.axistags = axistags 
                self.FeatureLayers[i].meta.description = os.path.basename(self._files[i]) 
            
            self.OutputImage.meta.shape    = (shape) + (len(self._files),)
            self.OutputImage.meta.dtype    = dtype 
            self.OutputImage.meta.axistags = axistags 
            
            self.CachedOutputImage.meta.shape    = (shape) + (len(self._files),)
            self.CachedOutputImage.meta.dtype    = dtype 
            self.CachedOutputImage.meta.axistags = axistags 
            return
           
        # Connect our external outputs to our internal operators
        self.OutputImage.connect( self.opPixelFeatures.Output )
        self.CachedOutputImage.connect( self.opPixelFeatureCache.Output )
        self.FeatureLayers.connect( self.opPixelFeatures.Features )

        # We choose block shapes that have only 1 channel because the channels may be 
        #  coming from different features (e.g different filters) and probably shouldn't be cached together.
        blockDimsX = { 't' : (1,1),
                       'z' : (128,256),
                       'y' : (128,256),
                       'x' : (32,32),
                       'c' : (1000,1000) } # Overestimate number of feature channels: Cache block dimensions will be clipped to the size of the actual feature image

        blockDimsY = { 't' : (1,1),
                       'z' : (128,256),
                       'y' : (32,32),
                       'x' : (128,256),
                       'c' : (1000,1000) }

        blockDimsZ = { 't' : (1,1),
                       'z' : (32,32),
                       'y' : (128,256),
                       'x' : (128,256),
                       'c' : (1000,1000) }
        
        axisOrder = [ tag.key for tag in self.InputImage.meta.axistags ]
        innerBlockShapeX = tuple( blockDimsX[k][0] for k in axisOrder )
        outerBlockShapeX = tuple( blockDimsX[k][1] for k in axisOrder )

        innerBlockShapeY = tuple( blockDimsY[k][0] for k in axisOrder )
        outerBlockShapeY = tuple( blockDimsY[k][1] for k in axisOrder )

        innerBlockShapeZ = tuple( blockDimsZ[k][0] for k in axisOrder )
        outerBlockShapeZ = tuple( blockDimsZ[k][1] for k in axisOrder )

        # Configure the cache        
        self.opPixelFeatureCache.innerBlockShape.setValue( (innerBlockShapeX, innerBlockShapeY, innerBlockShapeZ) )
        self.opPixelFeatureCache.outerBlockShape.setValue( (outerBlockShapeX, outerBlockShapeY, outerBlockShapeZ) )

    def propagateDirty(self, slot, subindex, roi):
        # Output slots are directly connected to internal operators
        pass
    
    def execute(self, slot, subindex, rroi, result):
        if len(self.FeatureListFilename.value) == 0:
            return
       
        assert result.dtype == numpy.float32
        
        key = roiToSlice(rroi.start, rroi.stop)
            
        if slot == self.FeatureLayers:
            index = subindex[0]
            f = h5py.File(self._files[index], 'r')
            result[...,0] = f["data"][key[0:3]]
            return result
        elif slot == self.OutputImage or slot == self.CachedOutputImage:
            assert result.ndim == 4
            assert result.shape[-1] == len(self._files), "result.shape = %r" % result.shape 
            assert rroi.start == 0, "rroi = %r" % (rroi,)
            assert rroi.stop  == len(self._files), "rroi = %r" % (rroi,)
            
            j = 0
            for i in range(key[3].start, key[3].stop):
                f = h5py.File(self._files[i], 'r')
                r = f["data"][key[0:3]]
                assert r.dtype == numpy.float32
                assert r.ndim == 3
                f.close()
                result[:,:,:,j] = r 
                j += 1
            return result  
        pass
