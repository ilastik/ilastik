from context import *
import vigra, numpy,h5py


def hR(upperLeft,lowerRight,H):
    h,w,nc=H.shape    
    p1m,p2m=upperLeft
    p1p,p2p=lowerRight
    p1p-=1
    p2p-=1
    
    res=H[p1p,p2p].copy()#-H[p1m,p2p]-H[p1p,p2m]+H[p1m,p2m] 
    #print "here",res
    #res+=H[0,p2p,:]+H[p1p,0,:]-H[p1m,0,:]-H[p1m,0,:]+H[0,0]
    if p1m >0 and p2m>0:
        res=H[p1p,p2p]-H[p1m-1,p2p]-H[p1p,p2m-1]+H[p1m-1,p2m-1] 
            
    
    return res.astype(numpy.uint32)

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
    
    #####Check if the histogram works
    
    h=hR((0,0),(5,10),res)
    
    print hR
    
    
    


if __name__=="__main__":
    
    TestIntegralHistogram()