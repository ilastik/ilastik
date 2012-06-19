import os
import numpy
from lazyflow.graph import Graph
from lazyflow.operators.ioOperators import OpInputDataReader
from applets.featureSelection.opFeatureSelection import OpFeatureSelection

class TestOpFeatureSelection(object):
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
    
    def test_basicFunctionality(self):
        graph = Graph()
        
        # Define operators
        featureSelector = OpFeatureSelection(graph=graph)
        reader = OpInputDataReader(graph=graph)
        
        # Set input data
        # Note: Assumes that a samplef file called 5d.npy exists three directories up
        filePath = os.getcwd() + '/../../../5d.npy'
        assert os.path.exists(filePath)
        
        reader.FilePath.setValue( filePath )
        
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
        featureSelector.SelectionMatrix.setValue(featureSelectionMatrix)
        
        # Compute results for the top slice only
        topSlice = [0, slice(None), slice(None), 0, slice(None)]
        result = featureSelector.OutputImages[0][topSlice].allocate().wait()
        
        numFeatures = numpy.sum(featureSelectionMatrix)
        inputChannels = reader.Output.meta.shape[-1]
        outputChannels = result.shape[-1]
        assert outputChannels == inputChannels*numFeatures
        
        # Debug only -- Inspect the resulting images
        if False:
            # Export the first slice of each channel of the results as a separate image for display purposes.
            import vigra
            numFeatures = result.shape[-1]
            for featureIndex in range(0, numFeatures):
                featureSlice = list(topSlice)
                featureSlice[-1] = featureIndex
                vigra.impex.writeImage(result[featureSlice], "test_feature" + str(featureIndex) + ".bmp")

if __name__ == "__main__":
    import nose
    nose.main(defaultTest=__file__)
