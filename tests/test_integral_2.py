import numpy
import context
import vigra


nx = 7
ny = 10
nc = 2

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
