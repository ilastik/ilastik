import numpy
import context
import vigra

im = numpy.zeros((5, 5, 2), dtype=numpy.float32)
intimage = numpy.zeros((5, 5, 2), dtype=numpy.float32)
im[0,0, 0]=1
im[1,1, 0]=1
im[2,2, 0]=1
im[3,3, 0]=1
im[4,4, 0]=2
im[0,0, 1]=1
im[1,1, 1]=1
im[2,2, 1]=1
im[3,3, 1]=1
im[4,4, 1]=2

''' expected result:
[[ 1.  1.  1.  1.  1.]
 [ 1.  2.  2.  2.  2.]
 [ 1.  2.  3.  3.  3.]
 [ 1.  2.  3.  4.  4.]
 [ 1.  2.  3.  4.  6.]]
[[ 1.  1.  1.  1.  1.]
 [ 1.  2.  2.  2.  2.]
 [ 1.  2.  3.  3.  3.]
 [ 1.  2.  3.  4.  4.]
 [ 1.  2.  3.  4.  6.]]
'''


intimage = context.integralImage(im, intimage)
if numpy.any(intimage[0, :, :]!=1) or numpy.any(intimage[:, 0, :]!=1):
    print "wrong1"
    print intimage[:, :, 0]
    print intimage[:, :, 1]
    
    
if numpy.any(intimage[1:4, 1, 0]!=2) or numpy.any(intimage[1, 1:4, 1]!=2):
    print "wrong2"
    print intimage[:, :, 0]
    print intimage[:, :, 1]
    
if numpy.any(intimage[2:4, 2, 0]!=3) or numpy.any(intimage[2, 2:4, 1]!=3):
    print "wrong3"
    
if intimage[3, 4, 0]!=4 or intimage[3, 4, 1]!=4 or intimage[4, 3, 0]!=4 or intimage[4, 3, 1]!=4 or intimage[3, 3, 0]!=4 or intimage[3, 3, 1]!=4:
    print "wrong4"

if intimage[4, 4, 0]!=6 or intimage[4, 4, 1]!=6:
    print "wrong5"

nx = 7
ny = 10
nc = 2

#dummypred = numpy.random.rand(nx, ny, nc)
dummypred = numpy.arange(nx*ny*nc)
dummypred = dummypred.reshape((nx, ny, nc))
dummypred = dummypred.astype(numpy.float32)

dummy = vigra.VigraArray(dummypred.shape, axistags=vigra.VigraArray.defaultAxistags(3)).astype(dummypred.dtype)
dummy[:]=dummypred[:]

#intimage = numpy.zeros(dummypred.shape, dtype=numpy.float32)
intimage = vigra.VigraArray(dummypred.shape, axistags=vigra.VigraArray.defaultAxistags(3)).astype(dummypred.dtype)
#dummyint[:]=intimage[:]

intimage = context.integralImage(dummy, intimage)
sum_row00 = numpy.sum(dummypred[0, :, 0])
sum_row01 = numpy.sum(dummypred[0, :, 1])
if (abs(sum_row00-intimage[0, ny-1, 0])>1E-5 or abs(sum_row01-intimage[0, ny-1, 1])>1E-5):
    print "sum of row 0, channel 0:", sum_row00, "computed as: ", intimage[0, intimage.shape[1]-1, 0]
    print "sum of row 0, channel 1:", sum_row01, "computed as: ", intimage[0, intimage.shape[1]-1, 1]
    
print
print dummypred[0, :, 0]
print intimage[0, :, 0]

