from context import *
import vigra, numpy,h5py
from numpy.testing import assert_array_equal as equal

def hR(upperLeft,lowerRight,H):
    """This function extracts the actual histogram from the integral histogram"""
    
    h,w,nc=H.shape    
    p1m,p2m=upperLeft
    p1p,p2p=lowerRight
    p1p-=1
    p2p-=1
    print p1p,p2p,H.shape
    res=H[p1p,p2p,:].copy()#-H[p1m,p2p]-H[p1p,p2m]+H[p1m,p2m] 
    #print "here",res
    #res+=H[0,p2p,:]+H[p1p,0,:]-H[p1m,0,:]-H[p1m,0,:]+H[0,0]
    if p1m >0 and p2m>0:
        res=H[p1p,p2p,:]-H[p1m-1,p2p,:]-H[p1p,p2m-1,:]+H[p1m-1,p2m-1,:] 
            
    
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
    
    equal(res.view(numpy.ndarray), desired, verbose=True)
    
    #####Check if the histogram works 
    reduced=numpy.squeeze(data.view(numpy.ndarray)).view(numpy.ndarray)
    print (data[:,:,0]*50).astype(numpy.uint8)
    print ""
    print (reduced[:,:]*50).astype(numpy.uint8)
    
    h=hR((0,0),(10,5),res).view(numpy.ndarray)
    assert (h==numpy.histogram(reduced, 3)[0]).all()
    
    
    h=hR((0,0),(7,3),res).view(numpy.ndarray)
    equal(h,numpy.histogram(data[:7,:3], 3,(0,1))[0])    
    
    h=hR((1,2),(7,3),res).view(numpy.ndarray)
    equal(h,numpy.histogram(data[1:7,2:3], 3,(0,1))[0])    
    
    


def TestSimpleHistogram():
    data=vigra.impex.readImage('ostrich.jpg')
    data=data.view(numpy.ndarray).astype(numpy.float32)
    data=data-data.min()
    data=data/data.max()
    
    res=histogram2D(data,3)
    
    assert res.shape==(data.shape[0],data.shape[1],data.shape[2]*3)
    
    


if __name__=="__main__":
    
    TestIntegralHistogram()
    TestSimpleHistogram()