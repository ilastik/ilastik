import numpy
import context
import vigra

#test average prediction computation by comparing 
#with numpy average and numpy sum
#this includes normal average for the first radius and
#average in (r2-r1) rectangle without a middle for r2
#!!! TODO: this test assumes neighborhood radii to be [1, 2] !!!
#!!! because I'm too lazy to make it generic

nx = 7
ny = 7
nc = 2
dummypred = numpy.random.rand(nx, ny, nc)
#dummypred = numpy.arange(nx*ny*nc)
dummypred = dummypred.reshape((nx, ny, nc))
dummypred = dummypred.astype(numpy.float32)

dummy = vigra.VigraArray(dummypred.shape, axistags=vigra.VigraArray.defaultAxistags(3)).astype(dummypred.dtype)
dummy[:]=dummypred[:]
#print dummypred[:, :, 0]

sizes = numpy.array([1, 2], dtype=numpy.uint32)
resshape = (nx, ny, nc*sizes.shape[0])
res = numpy.zeros(resshape, dtype=numpy.float32)

print sizes.dtype, dummypred.dtype, res.dtype
print sizes.shape, dummypred.shape, res.shape

res = context.avContext2Dmulti(sizes, dummy, res)

#test correctness of border conditions
if (numpy.any(res[0, :, :]!=1./nc)):
    print "border [0, :, :] wrong!"
if (numpy.any(res[:, 0, :]!=1./nc)):
    print "border [:, 0, :] wrong!"
if (numpy.any(res[nx-1, :, :]!=1./nc)):
    print "border [nx-1, :, :] wrong"
if (numpy.any(res[:, ny-1, :]!=1./nc)):
    print "border [:, ny-1, :] wrong"
    
if (numpy.any(res[1, :, 1]!=1./nc)):
    print "border [1, :, 1] wrong!"
if (numpy.any(res[:, 1, 1]!=1./nc)):
    print "border [:, 1, 1] wrong!"
if (numpy.any(res[nx-2, :, 1]!=1./nc)):
    print "border [nx-2, :, 1] wrong"
if (numpy.any(res[:, ny-2, 1]!=1./nc)):
    print "border [:, ny-2, 1] wrong"    


#test correctness of simple averages
av110 = numpy.average(dummypred[0:3, 0:3, 0])
if (abs(av110-res[1, 1, 0])>1E-5):
    print "av110 wrong:", av110, res[1, 1, 0]

av111 = numpy.average(dummypred[0:3, 0:3, 1])
if (abs(av111-res[1, 1, 2])>1E-5):
    print "av111 wrong:", av111, res[1, 1, 2]


av220 = numpy.average(dummypred[1:4, 1:4, 0])
if (abs(av220-res[2, 2, 0])>1E-5):
    print "av220 wrong:", av220, res[2, 2, 0]

av221 = numpy.average(dummypred[1:4, 1:4, 1])
if (abs(av221-res[2, 2, 2])>1E-5):
    print "av221 wrong:", av221, res[2, 2, 2]

av330 = numpy.average(dummypred[2:5, 2:5, 0])
if (abs(av330-res[3, 3, 0])>1E-5):
    print "av330 wrong:", av330, res[3, 3, 0]

av331 = numpy.average(dummypred[2:5, 2:5, 1])
if (abs(av331-res[3, 3, 2])>1E-5):
    print "av331 wrong:", av331, res[3, 3, 2]


#test correctness of averages in rectangles without middle
#print dummypred[0:5, 0:5, 0]
sum2 = numpy.sum(dummypred[0:5, 0:5, 0])
sum1 = numpy.sum(dummypred[1:4, 1:4, 0])
if (abs((sum2-sum1)/16 - res[2, 2, 1])>1E-5):
    print "res[2, 2, 1] wrong:", (sum2-sum1)/16, res[2, 2, 1]

sum2 = numpy.sum(dummypred[1:6, 1:6, 0])
sum1 = numpy.sum(dummypred[2:5, 2:5, 0])
if (abs((sum2-sum1)/16 - res[3, 3, 1])>1E-5):
    print "res[3, 3, 1] wrong:", (sum2-sum1)/16, res[3, 3, 1]

