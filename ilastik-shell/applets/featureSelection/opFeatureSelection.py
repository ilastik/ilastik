from lazyflow.graph import Graph, Operator, InputSlot, OutputSlot, MultiInputSlot, MultiOutputSlot

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
    InputImages = MultiInputSlot()

    # The following input slots are applied uniformly to all input images
    Scales = InputSlot() # The list of possible scales to use when computing features
    FeatureIds = InputSlot() # The list of features to compute
    SelectionMatrix = InputSlot() # A matrix of bools indicating which features to output.
                         # The matrix rows correspond to feature types in the order specified by the FeatureIds input.
                         #  (See OpPixelFeaturesPresmoothed for the available feature types.)
                         # The matrix columns correspond to the scales provided in the Scales input,
                         #  which requires that the number of matrix columns must match len(Scales.value)
    
    # Features are presented in the channels of the output images
    # Output can be optionally accessed via an internal cache.
    # (Training a classifier benefits from caching, but predicting with an existing classifier does not.)
    OutputImages = MultiOutputSlot()
    CachedOutputImages = MultiOutputSlot()
    
    def __init__(self, graph):
        super(OpFeatureSelection, self).__init__(graph=graph)

        # List of internal pixel features operators
        self.internalFeatureOps = []

        # Cache operator
        self.internalCaches = OpBlockedArrayCache(parent=self)
        self.internalCaches.Input.connect(self.OutputImages) # Note: Cache is now "wrapped" with level=1
        self.internalCaches.innerBlockShape.setValue((1,32,32,32,16))
        self.internalCaches.outerBlockShape.setValue((1,128,128,128,64))
        self.internalCaches.fixAtCurrent.setValue(False)

        def inputResizeHandler( slot, oldsize, newsize ):
            if ( newsize == 0 ):
                self.OutputImages.resize(0)
                self.CachedOutputImages.resize(0)
        self.InputImages.notifyResized(inputResizeHandler)

    def setupOutputs(self):
        numInputs = len(self.InputImages)
        featureIds = self.FeatureIds.value
        
        # Ensure that we have the right number of internal operators
        # Add more if necessary
        while len(self.internalFeatureOps) < numInputs:
            self.internalFeatureOps.append( OpPixelFeaturesPresmoothed(parent=self, featureIds=featureIds) )

        # Remove some if necessary
        # TODO: This can be more efficient.  We should figure out which input index was 
        #       removed so the remaining internal operators can keep their existing 
        #       connections instead of being rewired.
        if len(self.internalFeatureOps) < numInputs:
            self.internalFeatureOps.resize( numInputs )

        # Ensure the proper number of outputs
        self.OutputImages.resize( numInputs )
        self.CachedOutputImages.resize( numInputs )

        # Clone all image inputs to the corresponding internal operator.
        # Also, clone the matrix and scale inputs to each of our internal operators
        for i in range( 0, numInputs ):
            self.internalFeatureOps[i].Input.connect( self.InputImages[i] )
            self.internalFeatureOps[i].Scales.connect( self.Scales )
            self.internalFeatureOps[i].Matrix.connect( self.SelectionMatrix )
        
            # Copy the metadata from the internal operators
            self.OutputImages[i].meta.dtype = self.internalFeatureOps[i].Output.meta.dtype
            self.OutputImages[i].meta.shape = self.internalFeatureOps[i].Output.meta.shape
            self.OutputImages[i].meta.axistags = copy.copy(self.internalFeatureOps[i].Output.meta.axistags)

            self.CachedOutputImages[i].meta.dtype = self.internalFeatureOps[i].Output.meta.dtype
            self.CachedOutputImages[i].meta.shape = self.internalFeatureOps[i].Output.meta.shape
            self.CachedOutputImages[i].meta.axistags = copy.copy(self.internalFeatureOps[i].Output.meta.axistags)

    def getSubOutSlot(self, slots, indexes, key, result):
        slot = slots[0]
        if slot.name == 'OutputImages':
            # Uncached result
            req = self.internalFeatureOps[indexes[0]].Output[key].writeInto(result)
            res = req.wait()
            return res
        elif slot.name == 'CachedOutputImages':
            # Cached result
            req = self.internalCaches.Output[indexes[0]][key].writeInto(result)
            res = req.wait()
            return res

#
# Simple test
#
if __name__ == "__main__":
    import numpy
    from applets.dataSelection.opInputDataReader import OpInputDataReader
    graph = Graph()
    
    # Define operators
    featureSelector = OpFeatureSelection(graph=graph)
    reader = OpInputDataReader(graph=graph)

    # Set input data
    reader.FilePath.setValue( '5d.npy' )

    # Connect input
    featureSelector.InputImages.resize(1)
    featureSelector.InputImages[0].connect( reader.Output )

    # Configure scales        
    scales = [0.3, 0.7, 1, 1.6, 3.5, 5.0, 10.0]
    featureSelector.Scales.setValue(scales)

    # Configure feature types
    featureIds = [ 'GaussianSmoothing',
                   'LaplacianOfGaussian',
                   'StructureTensorEigenvalues',
                   'HessianOfGaussianEigenvalues',
                   'GaussianGradientMagnitude',
                   'DifferenceOfGaussians' ]
    featureSelector.FeatureIds.setValue(featureIds)

    # Configure matrix
    featureSelectionMatrix = numpy.array(numpy.zeros((len(featureIds),len(scales))), dtype=bool)
    featureSelectionMatrix[0,0] = True
    featureSelectionMatrix[1,1] = True
    featureSelectionMatrix[2,2] = True
    featureSelectionMatrix[2,3] = True
    featureSelector.Matrix.setValue(featureSelectionMatrix)

    # Compute results for the top slice only
    topSlice = [0, slice(None), slice(None), 0, slice(None)]
    result = featureSelector.OutputImages[0][topSlice].allocate().wait()
    
    numFeatures = numpy.sum(featureSelectionMatrix)
    inputChannels = reader.Output.meta.shape[-1]
    outputChannels = result.shape[-1]
    assert outputChannels == inputChannels*numFeatures
    
    # Export the first slice of each channel of the results as a separate image for display purposes.
    import vigra
    numFeatures = result.shape[-1]
    for featureIndex in range(0, numFeatures):
        featureSlice = list(topSlice)
        featureSlice[-1] = featureIndex
        vigra.impex.writeImage(result[featureSlice], "test_feature" + str(featureIndex) + ".bmp")






























