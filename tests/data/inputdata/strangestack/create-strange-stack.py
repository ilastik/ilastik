import numpy
import vigra

#this creates an image stack with sizes that do not match

for i in range(15):
    a = (255*numpy.random.random((20+i, 25+i))).astype(numpy.uint8)
    vigra.impex.writeImage(a, "%02d.png" % i)
