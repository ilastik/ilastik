import os
import numpy
from lazyflow.roi import sliceToRoi
from lazyflow.graph import Graph, OperatorWrapper
from lazyflow.operators.ioOperators import OpInputDataReader
from ilastik.applets.featureSelection.opFeatureSelection import OpFeatureSelection

import ilastik.ilastik_logging
ilastik.ilastik_logging.default_config.init()

class TestOpFeatureSelection(object):
    def setUp(self):
        data = numpy.random.random((2,100,100,100,3))

        self.filePath = os.path.expanduser('~') + '/featureSelectionTestData.npy'
        numpy.save(self.filePath, data)
    
        graph = Graph()
        
        # Define operators
        opFeatures = OperatorWrapper( OpFeatureSelection(graph=graph) )
        opReader = OpInputDataReader(graph=graph)
        
        # Set input data
        opReader.FilePath.setValue( self.filePath )
        
        # Connect input
        opFeatures.InputImage.resize(1)
        opFeatures.InputImage[0].connect( opReader.Output )
        
        # Configure scales        
        scales = [0.3, 0.7, 1, 1.6, 3.5, 5.0, 10.0]
        opFeatures.Scales.setValue(scales)
        
        # Configure feature types
        featureIds = [ 'GaussianSmoothing',
                       'LaplacianOfGaussian',
                       'StructureTensorEigenvalues',
                       'HessianOfGaussianEigenvalues',
                       'GaussianGradientMagnitude',
                       'DifferenceOfGaussians' ]
        opFeatures.FeatureIds.setValue(featureIds)

        # Configure matrix
        #                    sigma:   0.3    0.7    1.0    1.6    3.5    5.0   10.0
        selections = numpy.array( [[True,  False, False, False, False, False, False],   # Gaussian
                                   [False,  True, False, False, False, False, False],   # L of G
                                   [False, False,  True, False, False, False, False],   # ST EVs
                                   [False, False, False, False, False, False, False],   # H of G EVs
                                   [False, False, False, False, False, False, False],   # GGM
                                   [False, False, False, False, False, False, False]] ) # Diff of G
        opFeatures.SelectionMatrix.setValue(selections)

        self.opFeatures = opFeatures
        self.opReader = opReader
        
    def tearDown(self):
        try:
            os.remove(self.filePath)
        except:
            pass
    
    def test_basicFunctionality(self):
        opFeatures = self.opFeatures
                
        # Compute results for the top slice only
        topSlice = [0, slice(None), slice(None), 0, slice(None)]
        result = opFeatures.OutputImage[0][topSlice].allocate().wait()
        
        numFeatures = numpy.sum(opFeatures.SelectionMatrix.value)
        outputChannels = result.shape[-1]

        # Input has 3 channels, and one of our features outputs a 3D vector
        assert outputChannels == 15 # (3 + 3 + 9)
        
        # Debug only -- Inspect the resulting images
        if False:
            # Export the first slice of each channel of the results as a separate image for display purposes.
            import vigra
            numFeatures = result.shape[-1]
            for featureIndex in range(0, numFeatures):
                featureSlice = list(topSlice)
                featureSlice[-1] = featureIndex
                vigra.impex.writeImage(result[featureSlice], "test_feature" + str(featureIndex) + ".bmp")

    def testDirtyPropagation(self):
        opFeatures = self.opFeatures

        dirtyRois = []
        def handleDirty( slot, roi ):
            dirtyRois.append( roi )
        opFeatures.OutputImage[0].notifyDirty( handleDirty )

        # Change the matrix        
        selections = numpy.array( [[True,  False, False, False, False, False, False],   # Gaussian
                                   [False,  True, False, False, False, False, False],   # L of G
                                   [False, False,  True, False, False, False, False],   # ST EVs
                                   [False, False, False, True, False, False, False],   # H of G EVs
                                   [False, False, False, False, False, False, False],   # GGM
                                   [False, False, False, False, False, False, False]] ) # Diff of G
        print "About to change matrix."
        opFeatures.SelectionMatrix.setValue(selections)
        print "Matrix changed."
        
        assert len(dirtyRois) == 1
        assert (dirtyRois[0].start, dirtyRois[0].stop) == sliceToRoi( slice(None), self.opFeatures.OutputImage[0].shape )

if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
