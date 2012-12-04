import vigra
import h5py
import numpy

infile = h5py.File("/home/akreshuk/data/training_old/dbock/substack_05_41_aligned_elastic.h5")
ddd = numpy.asarray(infile["/volume/data"]).astype(numpy.float32)
ddd = ddd.squeeze()

newshape = (ddd.shape[0], ddd.shape[1], 3*ddd.shape[2])

newddd = vigra.sampling.resizeVolumeSplineInterpolation(ddd, shape=newshape)
print "done interpolating!"

outfile=h5py.File("/home/akreshuk/data/training_old/dbock/substack_05_41_aligned_elastic_interp3.h5", "w")
d = outfile.create_dataset("/volume/data", data=newddd)
outfile.close()

print "done"
