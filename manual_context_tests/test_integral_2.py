import numpy
import context
import vigra
from numpy.testing import assert_array_equal

def testIntegralImage():
    
    nx = 7
    ny = 10
    nc = 2

    print "testing integral image on an array of size:", nx, ny, nz

    dummypred = numpy.random.rand(nx, ny, nc)
    #dummypred = numpy.arange(nx*ny*nc)
    dummypred = dummypred.reshape((nx, ny, nc))
    dummypred = dummypred.astype(numpy.float32)

    dummy = vigra.VigraArray(dummypred.shape, axistags=vigra.VigraArray.defaultAxistags(3)).astype(dummypred.dtype)
    dummy[:]=dummypred[:]

    intimage = vigra.VigraArray(dummypred.shape, axistags=vigra.VigraArray.defaultAxistags(3)).astype(dummypred.dtype)

    intimage = context.integralImage(dummy, intimage)
    sum_row00 = numpy.sum(dummypred[0, :, 0])
    sum_row01 = numpy.sum(dummypred[0, :, 1])
    if (abs(sum_row00-intimage[0, ny-1, 0])>1E-5 or abs(sum_row01-intimage[0, ny-1, 1])>1E-5):
        print "sum of row 0, channel 0:", sum_row00, "computed as: ", intimage[0, ny-1, 0]
        print "sum of row 0, channel 1:", sum_row01, "computed as: ", intimage[0, ny-1, 1]
        
    sum_col00 = numpy.sum(dummypred[:, 0, 0])
    sum_col01 = numpy.sum(dummypred[:, 0, 1])
    if (abs(sum_col00-intimage[nx-1, 0, 0])>1E-5 or abs(sum_col01-intimage[nx-1, 0, 1])>1E-5):
        print "sum of col 0, channel 0:", sum_col00, "computed as: ", intimage[nx-1, 0, 0]
        print "sum of col 0, channel 1:", sum_col01, "computed as: ", intimage[nx-1, 0, 1]

    sum35_0 = numpy.sum(dummypred[0:4, 0:6, 0])
    sum35_1 = numpy.sum(dummypred[0:4, 0:6, 1])

    if (abs(sum35_0-intimage[3, 5, 0])>1E-5 or abs(sum35_1-intimage[3, 5, 1])>1E-5):
        print "sum of row 3, col 5, channel 0:", sum35_0, "computed as: ", intimage[3, 5, 0]
        print "sum of row 3, col 5, channel 1:", sum35_1, "computed as: ", intimage[3, 5, 1]
        
    sum_final0 = numpy.sum(dummypred[:, :, 0])
    sum_final1 = numpy.sum(dummypred[:, :, 1])

    if (abs(sum_final0-intimage[nx-1, ny-1, 0])>1E-5 or abs(sum_final1-intimage[nx-1, ny-1, 1])>1E-5):
        print "final sum, channel 0:", sum_final0, "computed as: ", intimage[nx-1, ny-1, 0]
        print "final sum, channel 1:", sum_final1, "computed as: ", intimage[nx-1, ny-1, 1]

def testIntegralVolume():
    print "testing integral volume"
    nx = 7
    ny = 10
    nc = 2
    
    #with nz = 1, should be equal to integral image
    nz = 1
    dummypred = numpy.random.rand(nx, ny, nc)
    #dummypred = numpy.arange(nx*ny*nz*nc)
    dummypred = dummypred.reshape((nx, ny, nz, nc))
    dummypred = dummypred.astype(numpy.float32)
    #we shouldn't have to recast to a vigra array anymore. keep it here just in case.
    
    dummyimage = vigra.VigraArray((nx, ny, nc), axistags=vigra.VigraArray.defaultAxistags(3)).astype(dummypred.dtype)
    dummyimage[:]=dummypred.squeeze()[:]

    dummyvolume = vigra.VigraArray((nx, ny, nz, nc), axistags=vigra.VigraArray.defaultAxistags(4)).astype(dummypred.dtype)
    dummyvolume[:]=dummypred[:]
    
    intimage = vigra.VigraArray((nx, ny, nc), axistags=vigra.VigraArray.defaultAxistags(3)).astype(dummypred.dtype)
    intvolume = vigra.VigraArray((nx, ny, nz, nc), axistags=vigra.VigraArray.defaultAxistags(4)).astype(dummypred.dtype)
    
    intimage = context.integralImage(dummyimage, intimage)
    intvolume = context.integralVolume(dummyvolume, intvolume)

    print intimage.shape
    print intvolume.shape
    assert_array_equal(intimage, intvolume.squeeze())
    
    dummyvolume2 = vigra.VigraArray((nx, ny, 2*nz, nc), axistags=vigra.VigraArray.defaultAxistags(4)).astype(dummypred.dtype)
    dummyvolume2[:, :, 0, :]=dummypred[:, :, 0, :]
    dummyvolume2[:, :, 1, :]=dummypred[:, :, 0, :]
    
    intvolume2 = vigra.VigraArray((nx, ny, 2*nz, nc), axistags=vigra.VigraArray.defaultAxistags(4)).astype(dummypred.dtype)
    intvolume2 = context.integralVolume(dummyvolume2, intvolume2)
    
    assert_array_equal(intimage, intvolume2[:, :, 0, :])
    intimage2 = intimage + intimage
    assert_array_equal(intimage2, intvolume2[:, :, 1, :])
    
    

if __name__ =="__main__":
    testIntegralImage()
    testIntegralVolume()
    