import vigra
import numpy

a = (255*numpy.random.random((200,300))).astype(numpy.uint16)+1000
vigra.impex.writeImage(a, "16bit_offset1000.tiff")
