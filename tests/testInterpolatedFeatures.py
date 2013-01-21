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
        self.nx = 50
        self.ny = 50
        self.nz = 50
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

    def aaaVigraStructureTensor(self):
        roi_small = ((0, 0, 2), (5, 5, 3))
        roi_full = ((0, 0, 0), (5, 5, 9))
        import h5py
        f = h5py.File("/home/anna/data/temptestimage1.h5")
        data1= numpy.asarray(f["/volume/data"])
        f2 = h5py.File("/home/anna/data/temptestimage2.h5")
        data2 = numpy.asarray(f2["/volume/data"])
        
        st1 = vigra.filters.structureTensor(data2, innerScale=1., outerScale=0.5, sigma_d=0, step_size=1,\
                                            window_size=2, roi=roi_small)
        st2 = vigra.filters.structureTensor(data1, innerScale=1., outerScale=0.5, sigma_d=0, step_size=1,\
                                            window_size=2, roi=roi_full)
        assert_array_almost_equal(st1, st2[:, :, 2:3, :], 3)
    
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
        
        #for i, imatrix in enumerate(self.selectedFeatures[30:31]):
        for i, imatrix in enumerate(self.selectedFeatures):
            opFeatures.Matrix.setValue(imatrix)
            opFeaturesInterp.Matrix.setValue(imatrix)
            outputInterpData = opFeatures.Output[:].wait()
            #outputInterpFeatures = opFeaturesInterp.Output[:].wait()
            
            
            
            for iz in range(self.nz):
            #for iz in range(2, 3):
                #print iz, iz*self.scaleZ
                try:
                    outputInterpDataSlice = opFeatures.Output[:, :, iz*self.scaleZ:iz*self.scaleZ+1, :].wait()
                    #outputInterpFeaturesSlice = opFeaturesInterp.Output[:, :, iz, :].wait()
                    #assert_array_almost_equal(outputInterpDataSlice, outputInterpFeaturesSlice, 3)
                    #assert_array_almost_equal(outputInterpData[:, :, iz*self.scaleZ, 0], outputInterpFeatures[:, :, iz, 0], 2)
                    assert_array_almost_equal(outputInterpDataSlice[:, :, 0, :], outputInterpData[:, :, iz*self.scaleZ, :], 3)
                except AssertionError:
                    print "failed for feature:", imatrix, i
                    print "failed for slice:", iz
                    print "inter data:", outputInterpData[:, :, iz*self.scaleZ, 0]
                    print "inter data slice:", outputInterpDataSlice[:, :, 0, 0]
                    #print "inter features:", outputInterpFeatures[3, 3, 0, 0]
                    raise AssertionError
            
        

if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)