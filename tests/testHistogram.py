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


def TestSimplestHistogram():
    print
    print "TestSimplestHistogram------------"
    data = numpy.ones((5, 5, 1), dtype = (numpy.float32))
    data = data.view(vigra.VigraArray)
    data.axistags = vigra.VigraArray.defaultAxistags(3)
    nbins = 4
    integral = intHistogram2D(data, nbins)
    newshape = (data.shape[0], data.shape[1], nbins)
    assert newshape==integral.shape, "shape mismatch"

    #print integral

    newhist = getHistOfRegion((0, 0), (2, 2), integral)
    subset = data[0:2, 0:2, :].squeeze()
    truehist = numpy.histogram(subset, bins=nbins, range=(0, 1))[0]
    equal(newhist,truehist)
    print "first good"
    print
    
    newhist = getHistOfRegion((1, 1), (4, 4), integral)
    subset = data[1:4, 1:4, :].squeeze()
    truehist = numpy.histogram(subset, bins=nbins, range=(0, 1))[0]
    equal(newhist,truehist)
    print "second good"
    print
    newhist = getHistOfRegion((0, 1), (5, 5), integral)
    #print newhist
    subset = data[0:5, 1:5, :].squeeze()
    truehist = numpy.histogram(subset, bins=nbins, range=(0, 1))[0]
    #print truehist
    equal(newhist, truehist)
    print "third good"
    print
    
    newhist = getHistOfRegion((1, 1), (5, 5), integral)
    #print newhist
    subset = data[1:5, 1:5, :].squeeze()
    truehist = numpy.histogram(subset, bins=nbins, range=(0, 1))[0]
    #print truehist
    equal(newhist, truehist)
    print "last good"

def TestIntegralHistogram():
    
    print
    print "TestIntegralHistogram---------------"
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
    
    h=getHistOfRegion((0,0),(10,5),res).view(numpy.ndarray)
    assert (h==numpy.histogram(reduced, 3)[0]).all()
    
    
    h=getHistOfRegion((0,0),(7,3),res).view(numpy.ndarray)
    equal(h,numpy.histogram(data[:7,:3], 3,(0,1))[0])    
    
    h=getHistOfRegion((1,2),(7,3),res).view(numpy.ndarray)
    equal(h,numpy.histogram(data[1:7,2:3], 3,(0,1))[0])
    
    
    
    
    data=numpy.reshape(numpy.arange(2500),(50,50)).astype(numpy.float32).T
    data=data-data.min()
    data=data/data.max()
    data.shape=data.shape+(1,)
    
    
    data=data.view(vigra.VigraArray)
    data.axistags=vigra.VigraArray.defaultAxistags(3)
    
    res=intHistogram2D(data,3)
    
    assert res.shape==(50,50,3), "shape mismatch"
    
    reduced=numpy.squeeze(data.view(numpy.ndarray)).view(numpy.ndarray)
    
    h=getHistOfRegion((8,8),(13,13),res).view(numpy.ndarray)
    equal(h,numpy.histogram(reduced[8:13,8:13],3,(0,1))[0])

    print "good"

def TestSimpleHistogram():
    print
    print "TestSimpleHistogram---------------"
    data=vigra.impex.readImage('ostrich.jpg')
    data=data.view(numpy.ndarray).astype(numpy.float32)
    data=data-data.min()
    data=data/data.max()
    
    res=histogram2D(data,3)
    res=res.view(numpy.ndarray)
    assert res.shape==(data.shape[0],data.shape[1],data.shape[2]*3)
    
    def hist(data,pos,bins,range):
        y,x=pos
        ch0=numpy.histogram(data[y,x,0], bins, range)[0]
        ch1=numpy.histogram(data[y,x,1], bins, range)[0]
        ch2=numpy.histogram(data[y,x,2], bins, range)[0]
        return numpy.concatenate([ch0,ch1,ch2])
    
   
    equal(hist(data,(0,0),3,(0,1)),res[0,0])
    
    equal(hist(data,(10,20),3,(0,1)),res[20,10])
    equal(hist(data,(11,12),3,(0,1)),res[12,11])
    equal(hist(data,(9,100),3,(0,1)),res[100,9])
    print "good"

def TestOverlappingHistogram():
    
    data=vigra.impex.readImage('ostrich.jpg')
    data=data.view(numpy.ndarray).astype(numpy.float32)
    data=data-data.min()
    data=data/data.max()
    
    bins=4
    
    
    #check if we get the same case of not overlap
    res=overlappingHistogram2D(data,bins,0)
    res=res.view(numpy.ndarray)
    assert res.shape==(data.shape[0],data.shape[1],data.shape[2]*bins)
    
    def hist(data,pos,bins,range):
        y,x=pos
        ch0=numpy.histogram(data[y,x,0], bins, range)[0]
        ch1=numpy.histogram(data[y,x,1], bins, range)[0]
        ch2=numpy.histogram(data[y,x,2], bins, range)[0]
        return numpy.concatenate([ch0,ch1,ch2])
    
    equal(hist(data,(0,0),bins,(0,1)),res[0,0])
    
    equal(hist(data,(10,20),bins,(0,1)),res[20,10])
    equal(hist(data,(11,12),bins,(0,1)),res[12,11])
    equal(hist(data,(9,100),bins,(0,1)),res[100,9])
    
    print "This only check if the result does not give segfaults"
    
    
    bins=20
    res=overlappingHistogram2D(data,bins,0.9999999)
    
    bins=2
    res=overlappingHistogram2D(data,bins,0.01)
    
 
 
def TestHistContext():
    
    
    data=numpy.reshape(numpy.arange(2500),(50,50)).astype(numpy.float32).T
    data=data-data.min()
    data=data/data.max()
    data.shape=data.shape+(1,)
    
    
    data=data.view(vigra.VigraArray)
    data.axistags=vigra.VigraArray.defaultAxistags(3)
    
    res=intHistogram2D(data,3)
    
    assert res.shape==(50,50,3), "shape mismatch"
    
    """
    import h5py
    file=h5py.File('test.h5','w')
    g=file.create_group('TestIntegralHistogram')
    d=g.create_dataset('data1',res.shape,res.dtype)
    d[:]=res[:]
    file.close()
    """

    a=histContext([1,2],res)
    print a[:,:,0].T
    
    print res[:,:,0]
   
   
    reduced=numpy.squeeze(data.view(numpy.ndarray)).view(numpy.ndarray)
    desired=numpy.histogram(reduced[8:13,8:13], 3,(0,1))[0]-numpy.histogram(reduced[9:12,9:12], 3,(0,1))[0]
    
    equal(a[10,10],desired)
 
 
if __name__=="__main__":
    TestSimplestHistogram()
    #TestHistContext()
    TestIntegralHistogram()
    TestSimpleHistogram()
    #TestOverlappingHistogram()
    