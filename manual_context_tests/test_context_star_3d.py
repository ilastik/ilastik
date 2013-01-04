import numpy
import vigra
import context

#make the program quit on Ctrl+C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

nx = 5
ny = 5
nz = 2
nc = 2
dummypred = numpy.random.rand(nx, ny, nz, nc)
#dummypred = numpy.arange(nx*ny*nc)
dummypred = dummypred.reshape((nx, ny, nz, nc))
dummypred = dummypred.astype(numpy.float32)

dummy = vigra.VigraArray(dummypred.shape, axistags=vigra.VigraArray.defaultAxistags(4)).astype(dummypred.dtype)
dummy[:]=dummypred[:]

#print dummypred[:, :, 0]
print dummy.shape, dummy.dtype

sizes = numpy.zeros((1, 3), dtype=numpy.uint32)
sizes[0,:]=[1, 1, 1]
#sizes = numpy.zeros((5, 3), dtype=numpy.uint32)
#sizes[0, :] = [1, 1, 1]
#sizes[1, :] = [2, 2, 1]
#sizes[2, :] = [3, 3, 1]
#sizes[3, :] = [1, 1, 2]
#sizes[4, :] = [2, 2, 2]

print sizes.shape, sizes.dtype

resshape = (dummypred.shape[0], dummypred.shape[1], dummypred.shape[2], sizes.shape[0]*26*nc)

res = vigra.VigraArray(resshape, axistags=vigra.VigraArray.defaultAxistags(4)).astype(numpy.float32)

print res.shape, res.dtype

res = context.starContext3Dnew(sizes, dummy, res)

print res.shape

print dummy[0:5, 0:5, 0, 0]
print
print res[1, 1, 0, 0:26]
