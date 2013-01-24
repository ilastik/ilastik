import vigra
import numpy
from lazyflow.operators import OpPixelFeaturesInterpPresmoothed, OpPixelFeaturesPresmoothed
from lazyflow.operators.ioOperators import OpInputDataReader
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
        
        self.randomData = (numpy.random.random((self.nx, self.ny, self.nz, 1))).astype(numpy.float32)
        self.randomDataInterp = vigra.sampling.resizeVolumeSplineInterpolation(self.randomData.squeeze(), \
                                                                               shape = (self.nx, self.ny, newRangeZ))
        self.randomDataInterp = self.randomDataInterp.reshape(self.randomDataInterp.shape+(1,))
        
        self.randomData = self.randomData.view(vigra.VigraArray).astype(numpy.float32)
        self.randomData.axistags = vigra.defaultAxistags(4)
        self.randomDataInterp = self.randomDataInterp.view(vigra.VigraArray)
        self.randomDataInterp.axistags = vigra.defaultAxistags(4)
        
        #data without channels
        self.dataNoChannels = self.randomData.squeeze()
        self.dataNoChannels = self.dataNoChannels.view(vigra.VigraArray)
        self.dataNoChannels.axistags = vigra.defaultAxistags(3, noChannels=True)
        
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
                
    def aaaAssert(self):
        g = graph.Graph()
        data = numpy.zeros((self.nx, self.ny, self.nz), dtype=numpy.float32)
        for i in range(self.data3d.shape[2]):
            data[:, :, i]=i
        data = data.view(vigra.VigraArray)
        data.axistags = vigra.VigraArray.defaultAxistags(3)
        opFeaturesInterp = OpPixelFeaturesInterpPresmoothed(graph=g)
        opFeaturesInterp.Input.setValue(data)
        opFeaturesInterp.Scales.setValue(self.scales)
        opFeaturesInterp.FeatureIds.setValue(self.featureIds)
        opFeaturesInterp.InterpolationScaleZ.setValue(self.scaleZ)
        opFeaturesInterp.Matrix.setValue(self.selectedFeatures[0])
        
        out = opFeaturesInterp.Output[:].wait()
        
        print "passed"
        
    def testInterpolated(self):
        self.runFeatures(self.data3d, self.data3dInterp)
        #print "TEST ONE DONE"
        self.runFeatures(self.randomData, self.randomDataInterp)
    
    def aaaSlices(self):
        g = graph.Graph()
        opFeatures = OpPixelFeaturesPresmoothed(graph=g)
        opFeatures.Scales.setValue(self.scales)
        opFeatures.FeatureIds.setValue(self.featureIds)
        opFeatures.Input.setValue(self.dataNoChannels)
        for i, imatrix in enumerate(self.selectedFeatures):
            opFeatures.Matrix.setValue(imatrix)
            #compute in one piece
            dataOne = opFeatures.Output[:].wait()
            
            #compute slice-wise
            for z in range(self.nz):
                dataSlice = opFeatures.Output[:, :, z:z+1].wait()
                try:
                    assert_array_almost_equal(dataOne[:, :, z:z+1], dataSlice, 2)
                except AssertionError:
                    print "wrong for matrix:", imatrix
                    print "wrong for slice:", z
                    print dataOne[:, :, z:z+1]
                    print dataSlice
                    raise AssertionError
                    
    def aaaNumpyFile(self):
        g =graph.Graph()
        npfile = "/home/akreshuk/data/synapse_small_4d.npy"
        reader = OpInputDataReader(graph=g)
        reader.FilePath.setValue(npfile)
        #out = reader.Output[:].wait()
        #print out.shape
        
        opFeatures = OpPixelFeaturesPresmoothed(graph=g)
        opFeatures.Scales.setValue(self.scales)
        opFeatures.FeatureIds.setValue(self.featureIds)
        opFeatures.Input.connect(reader.Output)
        opFeatures.Matrix.setValue(self.selectedFeatures[5])
        out = opFeatures.Output[:].wait()
        print out.shape
        
        opFeaturesInterp = OpPixelFeaturesInterpPresmoothed(graph=g)
        opFeaturesInterp.Scales.setValue(self.scales)
        opFeaturesInterp.FeatureIds.setValue(self.featureIds)
        opFeaturesInterp.Input.connect(reader.Output)
        opFeaturesInterp.Matrix.setValue(self.selectedFeatures[5])
        opFeaturesInterp.InterpolationScaleZ.setValue(2)
        out = opFeaturesInterp.Output[:].wait()
        
        print out.shape
        
            
    def runFeatures(self, data, dataInterp):
        g = graph.Graph()
        opFeatures = OpPixelFeaturesPresmoothed(graph=g)
        opFeaturesInterp = OpPixelFeaturesInterpPresmoothed(graph=g)
        
        opFeatures.Input.setValue(dataInterp)
        opFeaturesInterp.Input.setValue(data)
        
        opFeatures.Scales.setValue(self.scales)
        opFeaturesInterp.Scales.setValue(self.scales)
        
        opFeatures.FeatureIds.setValue(self.featureIds)
        opFeaturesInterp.FeatureIds.setValue(self.featureIds)
        
        opFeaturesInterp.InterpolationScaleZ.setValue(self.scaleZ)
        
        #for i, imatrix in enumerate(self.selectedFeatures[0:1]):
        for i, imatrix in enumerate(self.selectedFeatures):
            opFeatures.Matrix.setValue(imatrix)
            opFeaturesInterp.Matrix.setValue(imatrix)
            outputInterpData = opFeatures.Output[:].wait()
            outputInterpFeatures = opFeaturesInterp.Output[:].wait()
            
            for iz in range(self.nz):
            #for iz in range(2, 3):
                #print iz, iz*self.scaleZ
                try:
                    outputInterpDataSlice = opFeatures.Output[:, :, iz*self.scaleZ:iz*self.scaleZ+1, :].wait()
                    outputInterpFeaturesSlice = opFeaturesInterp.Output[:, :, iz, :].wait()
                    assert_array_almost_equal(outputInterpDataSlice, outputInterpFeaturesSlice, 1)
                    assert_array_almost_equal(outputInterpData[:, :, iz*self.scaleZ, 0], outputInterpFeatures[:, :, iz, 0], 1)
                    #assert_array_almost_equal(outputInterpDataSlice[:, :, 0, :], outputInterpData[:, :, iz*self.scaleZ, :], 3)
                    assert_array_almost_equal(outputInterpFeatures[:, :, iz, :], outputInterpFeaturesSlice[:, :, 0, :], 1)
                except AssertionError:
                    print "failed for feature:", imatrix, i
                    print "failed for slice:", iz
                    print "inter data:", outputInterpData[:, :, iz*self.scaleZ, 0]
                    print "inter features:", outputInterpFeatures[:, :, iz, 0]
                    print "inter data slice:", outputInterpDataSlice[:, :, 0, 0]
                    print "inter features:", outputInterpFeaturesSlice[:, :, 0, 0]
                    raise AssertionError
            
        

if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)