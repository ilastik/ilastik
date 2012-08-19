import os
import numpy
from lazyflow.graph import Graph, OperatorWrapper
from lazyflow.operators.ioOperators import OpInputDataReader
from ilastik.applets.featureSelection.opFeatureSelection import OpFeatureSelection

import ilastik.ilastik_logging
ilastik.ilastik_logging.default_config.init()

class TestOpFeatureSelection(object):
    def setUp(self):
        data = numpy.random.random((5,200,200,200,3))

        self.filePath = os.path.expanduser('~') + '/featureSelectionTestData.npy'
        numpy.save(self.filePath, data)
    
    def tearDown(self):
        try:
            os.remove(self.filePath)
        except:
            pass
    
    def test_basicFunctionality(self):
        graph = Graph()
        
        # Define operators
        featureSelector = OperatorWrapper( OpFeatureSelection(graph=graph) )
        reader = OpInputDataReader(graph=graph)
        
        # Set input data
        reader.FilePath.setValue( self.filePath )
        
        # Connect input
        featureSelector.InputImage.resize(1)
        featureSelector.InputImage[0].connect( reader.Output )
        
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
        result = featureSelector.OutputImage[0][topSlice].allocate().wait()
        
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
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
