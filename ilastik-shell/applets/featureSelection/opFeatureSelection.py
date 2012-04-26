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

    # Multiple images
    InputImages = MultiInputSlot()

    # Same set of selections applied to all images
    Matrix = InputSlot()
    Scales = InputSlot()
    
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

    def setupOutputs(self):
        numInputs = len(self.InputImages)
        # Ensure that we have the right number of internal operators
        # Add more if necessary
        while len(self.internalFeatureOps) < numInputs:
            self.internalFeatureOps.append( OpPixelFeaturesPresmoothed(parent=self) )

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
            self.internalFeatureOps[i].Matrix.connect( self.Matrix )
        
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
            req = self.internalCaches[indexes[0]][key].Output.writeInto(result)
            res = req.wait()
            return res

#
# Simple test
#
if __name__ == "__main__":
    import numpy
    from applets.dataSelection.opMultiInputDataReader import OpMultiInputDataReader
    graph = Graph()

    # Define operators
    featureSelector = OpFeatureSelection(graph=graph)
    reader = OpMultiInputDataReader(graph=graph)    

    # Set input data
    reader.FileNames.setValues( ['5d.npy'] )

#    Convert to grayscale?    
#    from lazyflow.operators import OpRgbToGrayscale
#    converter = OpRgbToGrayscale(graph=graph)
#    converter.input.connect(reader.Outputs)

    # Connect input
    featureSelector.InputImages.connect( reader.Outputs )

    # Configure scales        
    scales = [0.3, 0.7, 1, 1.6, 3.5, 5.0, 10.0]
    featureSelector.Scales.setValue(scales)

    # Configure matrix
    featureSelectionMatrix = numpy.array(numpy.zeros((6,7)), dtype=bool)
    featureSelectionMatrix[0,0] = True
    featureSelectionMatrix[1,1] = True
    featureSelectionMatrix[2,2] = True
    featureSelectionMatrix[2,3] = True
    featureSelector.Matrix.setValue(featureSelectionMatrix)

    # Compute results
    result = featureSelector.OutputImages[0][:].allocate().wait()
    
    numFeatures = numpy.sum(featureSelectionMatrix)
    inputChannels = reader.Outputs[0].meta.shape[-1]
    outputChannels = result.shape[-1]
    assert outputChannels == inputChannels*numFeatures
    
    # Export each channel of the results as a separate image for display purposes.
    import vigra
    numFeatures = result.shape[-1]
    for feature in range(0, numFeatures):
        vigra.impex.writeImage(result[0, :, :, 0, feature], "test_feature" + str(feature) + ".bmp")






























