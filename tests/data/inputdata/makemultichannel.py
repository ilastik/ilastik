import h5py
import numpy

a = (255*numpy.random.random((1,100,80,90,6))).astype(numpy.uint8)
f = h5py.File("multichannel.h5", 'w')
f.create_dataset("data", data=a)
f.close()
