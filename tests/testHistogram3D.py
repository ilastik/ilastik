import context
import numpy
import vigra
from numpy.testing import assert_equal, assert_almost_equal, assert_array_equal


def testIntegralHisto():
    print "testing integral Histo 3D"
    nx = 7
    ny = 10
    nz = 2
    nc = 1
    
    nbins = 4
    dummypred = numpy.arange(nx*ny*nz*nc)
    
    dummypred = dummypred/float(max(dummypred))
    dummypred = dummypred.reshape((nx, ny, nz, nc))
    dummypred = dummypred.astype(numpy.float32)
    dummy = vigra.VigraArray(dummypred.shape, axistags = vigra.VigraArray.defaultAxistags(4)).astype(dummypred.dtype)
    dummy[:] = dummypred[:]
    
    resshape = (nx, ny, nz, nc*nbins)
    res = vigra.VigraArray(resshape, axistags = vigra.VigraArray.defaultAxistags(4)).astype(numpy.float32)
    
    res = context.intHistogram3D(dummy, res, 4)
    
    temp = dummy[:, :, 0, :]
    hist, edges = numpy.histogram(temp, 4, (0, 1))
    #print "h=", hist
    #print "res=", inthist[nx-1, ny-1, 0, :]
    
    inthist2 = context.intHistogram2D(temp, 4)
    #print "res2=", inthist2[nx-1, ny-1, :]
    #print hist.shape, res[nx-1, ny-1, 0, :].shape
    #print hist
    #print res[nx-1, ny-1, 0, :]
    assert_array_equal(hist, numpy.array(res[nx-1, ny-1, 0, :]))
    
    hist, edges = numpy.histogram(dummy, 4, (0, 1))
    #print "h=", hist
    #print "res=", res[nx-1, ny-1, 1, :]
    assert_array_equal(hist, numpy.array(res[nx-1, ny-1, 1, :]))



def testHisto():
    
    print "testing a histogram of 3D neighborhood of anisotropic size"
        
    nx = 7
    ny = 10
    nz = 8
    nc = 2
    nbins = 4
    dummypred = numpy.arange(nx*ny*nz*nc)
    #dummypred = numpy.random.rand(nx, ny, nz, nc)
    m = max(dummypred)
    dummypred = dummypred/float(m)
    dummypred = dummypred.reshape((nx, ny, nz, nc))
    dummypred = dummypred.astype(numpy.float32)
    dummy = vigra.VigraArray(dummypred.shape, axistags=vigra.VigraArray.defaultAxistags(4)).astype(dummypred.dtype)
    dummy[:]=dummypred[:]
    sizes = numpy.zeros((2, 3), dtype = numpy.uint32)
    
    sizes[0, 0] = 2
    sizes[0, 1] = 2
    sizes[0, 2] = 1
    sizes[1, 0] = 3
    sizes[1, 1] = 3
    sizes[1, 2] = 2
    
    nr = sizes.shape[0]
    
    resshape = (nx, ny, nz, nc*nbins*nr)
    res = vigra.VigraArray(resshape, axistags=vigra.VigraArray.defaultAxistags(4)).astype(numpy.float32)
    res = context.contextHistogram3D(sizes, nbins, dummy, res)
    
    temp = dummy[0:5, 0:5, 0:3, 0]
    #print temp.shape
    #print temp
    h, edges = numpy.histogram(temp, nbins, range = (0, 1))
    
    #print "h:", h
    #print "res:", res[2, 2, 1, 0:nbins]
    assert_array_equal(h, numpy.array(res[2, 2, 1, 0:nbins]))
    
    #test the first radius, should be the same as normal histogram
    for x in range(sizes[0, 0], nx-sizes[0, 0]):
        for y in range(sizes[0, 1], ny-sizes[0, 1]):
            for z in range(sizes[0, 2], nz-sizes[0, 2]):
                for c in range(nc):
                    temp = dummy[x-sizes[0,0]:x+sizes[0,0]+1, y-sizes[0,1]:y+sizes[0,1]+1, z-sizes[0,2]:z+sizes[0,2]+1, c]
                    #print x, y, z
                    #print temp.shape
                    h, edges = numpy.histogram(temp, nbins, (0, 1))
                    #print "h=", h
                    #print "res=", res[x, y, z, 0:nbins]
                    assert_array_equal(h, numpy.array(res[x, y, z, c*nbins:c*nbins+nbins]))
                    
    #test the second radius
    for x in range(sizes[1, 0], nx-sizes[1, 0]):
        for y in range(sizes[1, 1], ny-sizes[1, 1]):
            for z in range(sizes[1, 2], nz-sizes[1, 2]):
                for c in range(nc):
                    tempsmall = dummy[x-sizes[0,0]:x+sizes[0,0]+1, y-sizes[0,1]:y+sizes[0,1]+1, z-sizes[0,2]:z+sizes[0,2]+1, c]
                    tempbig = dummy[x-sizes[1,0]:x+sizes[1,0]+1, y-sizes[1,1]:y+sizes[1,1]+1, z-sizes[1,2]:z+sizes[1,2]+1, c]
                    #print x, y, z
                    #print temp.shape
                    hsmall, edges = numpy.histogram(tempsmall, nbins, (0, 1))
                    hbig, edges = numpy.histogram(tempbig, nbins, (0, 1))
                    htot = hbig - hsmall
                    #print "hbig=", hbig
                    #print "htot=", htot
                    #print "res=", res[x, y, z, nc*nbins+c*nbins:nc*nbins+c*nbins+nbins]
                    assert_array_equal(htot, numpy.array(res[x, y, z, nc*nbins+c*nbins:nc*nbins+c*nbins+nbins]))
                    
    
    
if __name__=="__main__":
    testHisto()
    testIntegralHisto()
    