import vigra
import numpy
from lazyflow.operators import OpPixelFeaturesInterpPresmoothed, OpPixelFeaturesPresmoothed
from lazyflow import graph
from numpy.testing import assert_array_almost_equal

class TestInterpolatedFeatures():
    def setUp(self):
        self.scaleZ = 2
        self.scales = [0.3, 0.7, 1, 1.6, 3.5, 5.0, 10.0]
        self.featureIds = [ 'GaussianSmoothing', 'LaplacianOfGaussian',\
                   'GaussianGradientMagnitude',
                   'DifferenceOfGaussians',
                   'StructureTensorEigenvalues',
                   'HessianOfGaussianEigenvalues' ]
        
        #setup the data
        self.nx = 5
        self.ny = 5
        self.nz = 5
        self.data3d = numpy.zeros((self.nx, self.ny, self.nz, 1), dtype=numpy.float32)
        for i in range(self.data3d.shape[2]):
            self.data3d[:, :, i, 0]=i
            
        newRangeZ = self.scaleZ*(self.nz-1)+1
        self.data3dInterp = vigra.sampling.resizeVolumeSplineInterpolation(self.data3d.squeeze(), \
                                                       shape=(self.nx, self.ny, newRangeZ))
        
        self.data3dInterp = self.data3dInterp.reshape(self.data3dInterp.shape + (1,))

        self.data3d = self.data3d.view(vigra.VigraArray)
        self.data3d.axistags =  vigra.VigraArray.defaultAxistags(4)
        self.data3dInterp = self.data3dInterp.view(vigra.VigraArray)
        self.data3dInterp.axistags =  vigra.VigraArray.defaultAxistags(4)
        
        #setup the feature selection
        rows = 6
        cols = 7
        self.selectedFeatures = []
        #only test 1 feature 1 sigma setup for now
        for i in range(rows):
            for j in range(cols):
                features = numpy.zeros((rows,cols), dtype=bool)
                features[i, j]=True
                self.selectedFeatures.append(features)

    def testFeatures(self):
        g = graph.Graph()
        opFeatures = OpPixelFeaturesPresmoothed(graph=g)
        opFeaturesInterp = OpPixelFeaturesInterpPresmoothed(graph=g)
        
        opFeatures.Input.setValue(self.data3dInterp)
        opFeaturesInterp.Input.setValue(self.data3d)
        
        opFeatures.Scales.setValue(self.scales)
        opFeaturesInterp.Scales.setValue(self.scales)
        
        opFeatures.FeatureIds.setValue(self.featureIds)
        opFeaturesInterp.FeatureIds.setValue(self.featureIds)
        
        opFeaturesInterp.InterpolationScaleZ.setValue(self.scaleZ)
        
        for i, imatrix in enumerate(self.selectedFeatures[30:31]):
            opFeatures.Matrix.setValue(imatrix)
            opFeaturesInterp.Matrix.setValue(imatrix)
            
            
            
            for iz in range(self.nz):
                #print iz, iz*self.scaleZ
                try:
                    outputInterpData = opFeatures.Output[:, :, iz*self.scaleZ:iz*self.scaleZ+1, 0].wait()
                    outputInterpFeatures = opFeaturesInterp.Output[:, :, iz, 0].wait()
                    assert_array_almost_equal(outputInterpData, outputInterpFeatures)
                    #assert_array_almost_equal(outputInterpData[:, :, iz*self.scaleZ, 0], outputInterpFeatures[:, :, iz, 0], 2)
                except AssertionError:
                    print "failed for feature:", imatrix, i
                    print "failed for slice:", iz
                    print "inter data:", outputInterpData[3, 3, 0, 0]
                    print "inter features:", outputInterpFeatures[3, 3, 0, 0]
                    raise AssertionError

        

if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)