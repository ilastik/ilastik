import numpy
import context

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
    
