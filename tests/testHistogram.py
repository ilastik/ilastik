from context import *
import vigra, numpy,h5py


def TestIntegralHistogram():
    
    print "This only check if the result"
    data=numpy.reshape(numpy.arange(50),(5,10)).astype(numpy.float32).T
    data=data-data.min()
    data=data/data.max()
    data.shape=data.shape+(1,)
    
    
    data=data.view(vigra.VigraArray)
    data.axistags=vigra.VigraArray.defaultAxistags(3)
    
    res=intHistogram2D(data,3)
    print res,type(res)
    assert res.shape==(10,5,3), "shape mismatch"
    
    """
    import h5py
    file=h5py.File('test.h5','w')
    g=file.create_group('TestIntegralHistogram')
    d=g.create_dataset('data1',res.shape,res.dtype)
    d[:]=res[:]
    file.close()
    """
    h=h5py.File('test.h5','r')
    desired=h['TestIntegralHistogram/data1'][:]
    
    numpy.testing.assert_array_equal(res.view(numpy.ndarray), desired, verbose=True)
    
    
    
    
    


if __name__=="__main__":
    
    TestIntegralHistogram()