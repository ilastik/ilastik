from lazyflow.graph import Graph

import numpy as np
import vigra
from lazyflow.operators.opInterpMissingData import OpInterpMissingData, \
        OpInterpolate, OpDetectMissing

import unittest
from numpy.testing import assert_array_almost_equal, assert_array_equal

try:
    from scipy.interpolate import UnivariateSpline
    haveScipy = True
except ImportError:
    haveScipy = False


np.set_printoptions(precision=3, linewidth=80)

_testDescriptions = ['large block empty', 'single layer empty', 'last layer empty', 'first block empty', \
                    'second to last layer empty', 'second layer empty', 'first layer empty', \
                    'multiple blocks empty', 'all layers empty', \
                    'different regions empty', \
                    ]


def _getTestVolume(description, method):
    
    if description == 'large block empty':
        expected_output = _volume(nz=100, method=method)
        volume = vigra.VigraArray(expected_output)
        missing = vigra.VigraArray(expected_output, dtype=np.uint8)
        volume[:,:,30:50] = 0
        missing[:] = 0
        missing[:,:,30:50] = 1
    elif description == 'single layer empty':
        (volume, missing, expected_output) = _singleMissingLayer(layer=30, method=method)
    elif description == 'last layer empty':
        (volume, missing, expected_output) = _singleMissingLayer(nz=100, layer=99)
        # expect constant interpolation at border
        expected_output[:,:,-1] = volume[:,:,-2]
    elif description == 'second to last layer empty':
        (volume, missing, expected_output) = _singleMissingLayer(nz=100, layer=98, method='linear')
    elif description == 'first layer empty':
        (volume, missing, expected_output) = _singleMissingLayer(nz=100, layer=0)
        # expect constant interpolation at border
        expected_output[:,:,0] = volume[:,:,1]
    elif description == 'second layer empty':
        (volume, missing, expected_output) = _singleMissingLayer(nz=100, layer=1, method='linear')
    elif description == 'first block empty':
        expected_output = _volume(method=method)
        volume = vigra.VigraArray(expected_output)
        missing = vigra.VigraArray(expected_output, dtype=np.uint8)
        volume[:,:,0:10] = 0
        missing[:] = 0
        missing[:,:,0:10] = 1
        # expect constant interpolation at border
        expected_output[...,0:10] = volume[...,10].withAxes(*'xyz')
    elif description == 'multiple blocks empty':
        expected_output = _volume(method=method)
        volume = vigra.VigraArray(expected_output)
        missing = vigra.VigraArray(expected_output, dtype=np.uint8)
        volume[:,:,[10,11,30,31]] = 0
        missing[:] = 0
        missing[:,:,[10,11,30,31]] = 1
    elif description == 'all layers empty':
        expected_output = _volume(method=method)*0
        volume = vigra.VigraArray(expected_output)
        missing = vigra.VigraArray(expected_output, dtype=np.uint8)
        missing[:,:,[10,11,30,31]] = 1
    elif description == 'different regions empty':
        (volume, missing, expected_output) = _singleMissingLayer(layer=30, method=method)
        
        (volume2, missing2, expected_output2) = _singleMissingLayer(layer=60, method=method)
        volume2 = 256 - volume2
        volume2[np.where(missing2>0)] = 0
        expected_output2 = 256 - expected_output2
        
        volume[...,45:] = volume2[...,45:]
        expected_output[...,45:] = expected_output2[...,45:]
        missing += missing2
        
    else:
        raise NotImplementedError("test cube '{}' not available.".format(description))
    
    return (volume, missing, expected_output)

def _volume(nx=64,ny=64,nz=100,method='linear'):
    b = vigra.VigraArray( np.ones((nx,ny,nz)), axistags=vigra.defaultAxistags('xyz') )
    if method == 'linear':
        for i in range(b.shape[2]): b[:,:,i]*=(i+1)+50
    elif method == 'cubic':
        s = nz/3
        for z in range(b.shape[2]): b[:,:,z]= (z-s)**2*z*150.0/(nz*(nz-s)**2) + 30
    elif method == 'constant':
        b[:] = 124
    else:
        raise NotImplementedError("unknown method '{}'.".format(method))
    
    return b

def _singleMissingLayer(layer=30, nx=64,ny=64,nz=100,method='linear'):
    expected_output = _volume(nx=nx, ny=ny, nz=nz, method=method)
    volume = vigra.VigraArray(expected_output)
    missing = vigra.VigraArray(np.zeros(volume.shape), axistags = volume.axistags, dtype=np.uint8)
    volume[:,:,layer] = 0
    missing[:] = 0
    missing[:,:,layer] = 1 
    return (volume, missing, expected_output)


class TestDetection(unittest.TestCase):
    def setUp(self):
        self.op = OpDetectMissing(graph=Graph())
        self.op.PatchSize.setValue(64)
        self.op.HaloSize.setValue(0)
        #self.op.DetectionMethod.setValue('svm')
        
    def testClassicDetection(self):
        self.op.DetectionMethod.setValue('classic')
        self.op.PatchSize.setValue(1)
        self.op.HaloSize.setValue(0)
        (v,m,_) = _singleMissingLayer(layer=15, nx=1,ny=1,nz=50,method='linear')
        self.op.InputVolume.setValue(v)
        
        assert_array_equal(self.op.Output[:].wait().view(type=np.ndarray),\
                                m.view(type=np.ndarray),\
                                err_msg="input with single black layer")
    def testSVMDetection(self):
        try:
            import sklearn
        except ImportError:
            return
        self.op.DetectionMethod.setValue('svm')
        self.op.PatchSize.setValue(1)
        self.op.HaloSize.setValue(0)
        (v,m,_) = _singleMissingLayer(layer=15, nx=1,ny=1,nz=50,method='linear')
        self.op.InputVolume.setValue(v)
        
        assert_array_equal(self.op.Output[:].wait().view(type=np.ndarray),\
                                m.view(type=np.ndarray),\
                                err_msg="input with single black layer")
                            
    def testSVMWithHalo(self):
        try:
            import sklearn
        except ImportError:
            return
        self.op.DetectionMethod.setValue('svm')
        self.op.PatchSize.setValue(2)
        self.op.HaloSize.setValue(1)
        (v,m,_) = _singleMissingLayer(layer=15, nx=4,ny=4,nz=50,method='linear')
        self.op.InputVolume.setValue(v)
        
        assert_array_equal(self.op.Output[:].wait().view(type=np.ndarray),\
                                m.view(type=np.ndarray),\
                                err_msg="input with single black layer")
    
    def testSingleMissingLayer(self):
        (v,m,_) = _singleMissingLayer(layer=15, nx=64,ny=64,nz=50,method='linear')
        self.op.InputVolume.setValue(v)
        
        assert_array_equal(self.op.Output[:].wait().view(type=np.ndarray),\
                                m.view(type=np.ndarray),\
                                err_msg="input with single black layer")
                            
    def testDoubleMissingLayer(self):
        (v,m,_) = _singleMissingLayer(layer=15, nx=64,ny=64,nz=50,method='linear')
        (v2,m2,_) = _singleMissingLayer(layer=35, nx=64,ny=64,nz=50,method='linear')
        m2[np.where(m2==1)] = 2
        self.op.InputVolume.setValue(np.sqrt(v*v2))
        
        assert_array_equal(self.op.Output[:].wait().view(type=np.ndarray)>0,\
                                (m+m2).view(type=np.ndarray)>0,\
                                err_msg="input with two black layers")
                            
                            
    def test4D(self):
        self.op.PatchSize.setValue(64)
        vol = vigra.VigraArray( np.ones((10,64,64,3)), axistags=vigra.defaultAxistags('cxyz') )
        self.op.InputVolume.setValue(vol)
        self.op.Output[:].wait()
                            
    
    def test5D(self):
        self.op.PatchSize.setValue(64)
        vol = vigra.VigraArray( np.ones((15,64,10,3,64)), axistags=vigra.defaultAxistags('cxzty') )
        self.op.InputVolume.setValue(vol)
        self.op.Output[:].wait()
            
    
    def testPersistence(self):
        dumpedString = self.op.dumps()
        self.op.loads(dumpedString)
    
class TestInterpolation(unittest.TestCase):
    '''
    tests for the interpolation
    '''
    
    
    def setUp(self):
        g=Graph()
        op = OpInterpolate(graph = g)
        self.op = op
    
    def testLinearAlgorithm(self):
        (v,m,orig) = _singleMissingLayer(layer=15, nx=1,ny=1,nz=50,method='linear')
        v[:,:,10:15] = 0
        m[:,:,10:15] = 1
        interpolationMethod = 'linear'
        
        self.op.InputVolume.setValue(v)
        self.op.Missing.setValue(m)
        self.op.InterpolationMethod.setValue(interpolationMethod)
        self.op.InputVolume.setValue( v )
        
        assert_array_almost_equal(self.op.Output[:].wait().view(np.ndarray),\
                                orig.view(np.ndarray), decimal=3,\
                                err_msg="direct comparison to linear data")
        
    
    def testCubicAlgorithm(self):
        (v,m,orig) = _singleMissingLayer(layer=15, nx=1,ny=1,nz=50,method='cubic')
        v[:,:,10:15] = 0
        m[:,:,10:15] = 1
        interpolationMethod = 'cubic'
        self.op.InputVolume.setValue(v)
        self.op.Missing.setValue(m)
        self.op.InterpolationMethod.setValue(interpolationMethod)
        self.op.InputVolume.setValue( v )
        
        # natural comparison
        assert_array_almost_equal(self.op.Output[:].wait().view(np.ndarray),\
                                orig.view(np.ndarray), decimal=3,\
                                err_msg="direct comparison to cubic data")
        
        if not haveScipy:
            return 
            
        # scipy spline interpolation
        x = np.zeros(v.shape)
        x[:,:,:] = np.arange(v.shape[2])
        (i,j,k) = np.where(m==0)
        xs = x[i,j,k]
        ys = v.view(np.ndarray)[i,j,k]
        spline = UnivariateSpline(x[:,:,[8, 9, 16, 17]], v[:,:,[8,9,16,17]], k=3, s=0)
        e = spline(np.arange(v.shape[2]))
        
        assert_array_almost_equal(self.op.Output[:].wait()[:,:,10:15].squeeze().view(np.ndarray),\
                                e[10:15], decimal=3, err_msg="scipy.interpolate.UnivariateSpline comparison")
                            
                                
    def test4D(self):
        vol = vigra.VigraArray( np.ones((50,50,10,3)), axistags=vigra.defaultAxistags('cxyz') )
        miss = vigra.VigraArray(vol)
        miss[:,:,3,2] = 1
        self.op.InputVolume.setValue(vol)
        self.op.Missing.setValue(miss)
        
        self.op.Output[:].wait()
                            
    
    def test5D(self):
        vol = vigra.VigraArray( np.ones((50,50,10,3,7)), axistags=vigra.defaultAxistags('cxzty') )
        miss = vigra.VigraArray(vol)
        miss[:,:,3,2,4] = 1
        self.op.InputVolume.setValue(vol)
        self.op.Missing.setValue(miss)
        
        self.op.Output[:].wait()
        
        
    def testNothingToInterpolate(self):
        vol = vigra.VigraArray( np.ones((50,50,10,3,7)), axistags=vigra.defaultAxistags('cxzty') )
        miss = vigra.VigraArray(vol)*0
        
        self.op.InputVolume.setValue(vol)
        self.op.Missing.setValue(miss)
        
        
        assert_array_equal( self.op.Output[:].wait(), vol.view(np.ndarray), err_msg="interpolation where nothing had to be interpolated")
        
        
    def testIntegerRange(self):
        '''
        test if the output is in the right integer range
        in particular, too large values should be set to max and too small 
        values to min
        '''
        v = np.zeros((1,1,5), dtype=np.uint8)
        v[0,0,:] = [220,255,0,255,220]
        v =  vigra.VigraArray(v, axistags=vigra.defaultAxistags('xyz'), dtype=np.uint8)
        m = vigra.VigraArray(v, axistags=vigra.defaultAxistags('xyz'), dtype=np.uint8)
        m[:] = 0
        m[0,0,2] = 1
        
        for interpolationMethod in ['cubic']:
            self.op.InputVolume.setValue(v)
            self.op.Missing.setValue(m)
            self.op.InterpolationMethod.setValue(interpolationMethod)
            self.op.InputVolume.setValue( v )
            out = self.op.Output[:].wait().view(np.ndarray)
            # natural comparison
            self.assertEqual(out[0,0,2], 255)
        
        v = np.zeros((1,1,5), dtype=np.uint8)
        v[0,0,:] = [220,255,0,255,220]
        v = 255 - vigra.VigraArray(v, axistags=vigra.defaultAxistags('xyz'), dtype=np.uint8)
        m = vigra.VigraArray(v, axistags=vigra.defaultAxistags('xyz'), dtype=np.uint8)
        m[:] = 0
        m[0,0,2] = 1
        
        for interpolationMethod in ['cubic']:
            self.op.InputVolume.setValue(v)
            self.op.Missing.setValue(m)
            self.op.InterpolationMethod.setValue(interpolationMethod)
            self.op.InputVolume.setValue( v )
            out = self.op.Output[:].wait().view(np.ndarray)
            # natural comparison
            self.assertEqual(out[0,0,2], 0)
            
    


class TestInterpMissingData(unittest.TestCase):
    '''
    tests for the whole detection/interpolation workflow
    '''
    
    
    def setUp(self):
        g=Graph()
        op = OpInterpMissingData(graph = g)
        self.op = op
    
    def testLinearBasics(self):
        self.op.InputSearchDepth.setValue(0)
        
        interpolationMethod = 'linear'
        self.op.InterpolationMethod.setValue(interpolationMethod)

        for desc in _testDescriptions:
            (volume, _, expected) = _getTestVolume(desc, interpolationMethod)
            self.op.InputVolume.setValue( volume )
            self.op.PatchSize.setValue( volume.shape[0] )
            assert_array_almost_equal(self.op.Output[:].wait().view(np.ndarray), expected.view(np.ndarray), decimal=2, err_msg="method='{}', test='{}'".format(interpolationMethod, desc))
        
    
    def testCubicBasics(self):
        self.op.InputSearchDepth.setValue(0)
        
        interpolationMethod = 'cubic'
        self.op.InterpolationMethod.setValue(interpolationMethod)
        
        for desc in _testDescriptions:
            (volume, _, expected) = _getTestVolume(desc, interpolationMethod)
            self.op.InputVolume.setValue( volume )
            self.op.PatchSize.setValue( volume.shape[0] )
            assert_array_almost_equal(self.op.Output[:].wait().view(np.ndarray), expected.view(np.ndarray), decimal=2, err_msg="method='{}', test='{}'".format(interpolationMethod, desc))

    def testSwappedAxesLinear(self):
        self.op.InputSearchDepth.setValue(0)
        
        interpolationMethod = 'linear'
        self.op.InterpolationMethod.setValue(interpolationMethod)

        for desc in _testDescriptions:
            (volume, _, expected) = _getTestVolume(desc, interpolationMethod)
            self.op.PatchSize.setValue( volume.shape[0] )
            volume = volume.transpose()
            expected = expected.transpose()
            self.op.InputVolume.setValue( volume )
            
            assert_array_almost_equal(self.op.Output[:].wait().view(np.ndarray), expected.view(np.ndarray), decimal=2, err_msg="method='{}', test='{}'".format(interpolationMethod, desc))
    
    def testSwappedAxesCubic(self):
        self.op.InputSearchDepth.setValue(0)
        
        interpolationMethod = 'cubic'
        self.op.InterpolationMethod.setValue(interpolationMethod)

        for desc in _testDescriptions:
            (volume, _, expected) = _getTestVolume(desc, interpolationMethod)
            self.op.PatchSize.setValue( volume.shape[0] )
            volume = volume.transpose()
            expected = expected.transpose()
            self.op.InputVolume.setValue( volume )
            
            assert_array_almost_equal(self.op.Output[:].wait().view(np.ndarray), expected.view(np.ndarray), decimal=2, err_msg="method='{}', test='{}'".format(interpolationMethod, desc))
    
    def testDepthSearch(self):
        #TODO extend
        nz = 30
        interpolationMethod = 'cubic'
        self.op.InterpolationMethod.setValue(interpolationMethod)
        (vol, _, exp) = _singleMissingLayer(layer=nz,method=interpolationMethod)

        self.op.InputVolume.setValue( vol )
        self.op.InputSearchDepth.setValue(15)
        self.op.PatchSize.setValue( vol.shape[0] )
        
        result = self.op.Output[:,:,nz].wait()
        
        assert_array_almost_equal(result.squeeze(), exp[:,:,nz].view(np.ndarray).squeeze(), decimal=3)
        
    def testRoi(self):
        nz = 30
        interpolationMethod = 'cubic'
        self.op.InterpolationMethod.setValue(interpolationMethod)
        (vol, _, exp) = _singleMissingLayer(layer=nz,method=interpolationMethod)
        (vol2,_,_) = _singleMissingLayer(layer=nz+1,method=interpolationMethod)
        vol = np.sqrt(vol*vol2)

        self.op.InputVolume.setValue( vol )
        self.op.InputSearchDepth.setValue(5)
        self.op.PatchSize.setValue( vol.shape[0] )
        
        result = self.op.Output[:,:,nz+1].wait()
        
        assert_array_almost_equal(result.squeeze(), exp[:,:,nz+1].view(np.ndarray).squeeze(), decimal=3)
        pass
    
    def testBadImageSize(self):
        #TODO implement
        pass
    
    def testHaloSize(self):
        #TODO implement
        pass



if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)
    if not ret: sys.exit(1)
    

