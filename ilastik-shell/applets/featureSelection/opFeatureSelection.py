from lazyflow.graph import Graph, Operator, OperatorWrapper, InputSlot, OutputSlot, MultiInputSlot, MultiOutputSlot

from lazyflow.operators import OpPixelFeaturesPresmoothed, OpBlockedArrayCache
import copy

class OpFeatureSelection(Operator):
    """
    The top-level operator for the feature selection applet.
    MultiInputSlot for images, but only single input slots for feature selection matrix and set of scales.
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
    
    # Features are presented in the channels of the output image
    # Output can be optionally accessed via an internal cache.
    # (Training a classifier benefits from caching, but predicting with an existing classifier does not.)
    OutputImage = OutputSlot()
    CachedOutputImage = OutputSlot()

    FeatureNames = OutputSlot() # The name of each feature used is also provided as a list of strings
    
    def __init__(self, *args, **kwargs):
        super(OpFeatureSelection, self).__init__(*args, **kwargs)

        # Two internal operators: features and cache
        self.opPixelFeatures = OpPixelFeaturesPresmoothed(parent=self)
        self.opPixelFeatureCache = OpBlockedArrayCache(parent=self)
        self.opPixelFeatureCache.name = "opPixelFeatureCache"

        # Connect the cache to the feature output
        self.opPixelFeatureCache.Input.connect(self.opPixelFeatures.Output)
        self.opPixelFeatureCache.fixAtCurrent.setValue(False)

        # Connect our internal operators to our external inputs 
        self.opPixelFeatures.Scales.connect( self.Scales )
        self.opPixelFeatures.FeatureIds.connect( self.FeatureIds )
        self.opPixelFeatures.Matrix.connect( self.SelectionMatrix )
        self.opPixelFeatures.Input.connect( self.InputImage )
        
        # Connect our external outputs to our internal operators
        self.FeatureNames.connect( self.opPixelFeatures.FeatureNames )
        self.OutputImage.connect( self.opPixelFeatures.Output )
        self.CachedOutputImage.connect( self.opPixelFeatureCache.Output )        

    def setupOutputs(self):        
        # We choose block shapes that have only 1 channel because the channels may be 
        #  coming from different features (e.g different filters) and probably shouldn't be cached together.
        blockDims = { 't' : (1,1),
                      'z' : (1,1),
                      'y' : (32,128),
                      'x' : (32,128),
                      'c' : (1,1) }

        axisOrder = [ tag.key for tag in self.InputImage.meta.axistags ]
        innerBlockShape = tuple( blockDims[k][0] for k in axisOrder )
        outerBlockShape = tuple( blockDims[k][1] for k in axisOrder )

        # Configure the cache        
        self.opPixelFeatureCache.innerBlockShape.setValue(innerBlockShape)
        self.opPixelFeatureCache.outerBlockShape.setValue(outerBlockShape)






















