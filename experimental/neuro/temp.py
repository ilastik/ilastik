import vigra
import h5py
import numpy
from lazyflow import operators
from lazyflow.graph import *

g = Graph()


f1 = h5py.File("/home/akreshuk/data/context/TEM_labels/bock_training_1024_2048_5_28_labels_from_ilastik.h5")
d1 = f1["/volume/data"]

f2 = h5py.File("/home/akreshuk/data/context/TEM_labels/temp_bock_training_1024_2048_5_28_labels.h5")
d2 = numpy.zeros((1,)+d1.shape+(1,), dtype = d1.dtype)
d2[0, :, :, :, 0] = d1[:]
f2.create_dataset("/volume/data", data=d2)
f2.close()
f1.close()

#fname = h5py.File("/home/akreshuk/data/context/50slices_down2_all_float_nowin_iter0.h5")
#fname = h5py.File("/home/akreshuk/data/context/50slices_down2_temp_iter1.h5")

#pmaps = fname["/volume/pmaps"]
#pmaps_ch2 = numpy.zeros(pmaps.shape[:-1]+(1,), dtype=numpy.uint8)
#print pmaps_ch2.shape
#pmaps_ch2[:] = pmaps[...,2:3]*255
#nz = pmaps_ch2.shape[2]
#for z in range(nz):
    #print z
    #image = pmaps_ch2[:, :, z, :]
    #print image.shape
    #vigra.impex.writeImage(image, "/home/akreshuk/data/context/testpred_old/image_"+str(z)+".png")




#features = fname["/volume/features"]
#print features.shape

#fileall = h5py.File("/home/akreshuk/data/context/features/all.h5", "w")
#featall = numpy.zeros((1,)+features.shape, dtype=numpy.float32)
#featall[0,...]=features[:]
#fileall.create_dataset("/volume/data", data=featall)
#fileall.close()

#file1 = h5py.File("/home/akreshuk/data/context/features/gaus35.h5", "w")
#gaus1 = numpy.zeros((1,)+features.shape[:-1]+(1,), dtype=numpy.float32)
#gaus1[0, ...]=features[...,0:1]
#file1.create_dataset("/volume/data", data=gaus1)
#file1.close()

#file2 = h5py.File("/home/akreshuk/data/context/features/gaus50.h5", "w")
#gaus2 = numpy.zeros((1,)+features.shape[:-1]+(1,), dtype=numpy.float32)
#gaus2[0, ...]=features[...,3:4]
#file2.create_dataset("/volume/data", data=gaus2)
#file2.close()


#bigfile = "/home/akreshuk/data/context/TEM_raw/50slices_down2.h5"
#f = h5py.File(bigfile)
#d = f["/volume/data"]

#smallfile = "/home/akreshuk/data/context/TEM_raw/50slices_down2_42.h5"
#fs = h5py.File(smallfile, "w")
#ds = numpy.zeros((1, 1, 100, 100, 1))
#ds[0, 0, :, :, 0] = d[0:100, 0:100, 42]
#fs.create_dataset("/volume/data", data=ds)
#fs.close()
#f.close()

