import numpy
import time
import sys
import h5py
import pyximport; pyximport.install()
from cylemon.segmentation import MSTSegmentor


import vigra
import scipy.ndimage
import numpy

if len(sys.argv) > 1:
  inputf = sys.argv[1]
else:
  inputf="/home/cstraehl/Projects/PHD/benchmarks/denk-block-200/d-carving-200.h5" 

if len(sys.argv) > 2:
  outputf = sys.argv[2]
else:
  outputf = "test.graph5"


print "preprocessing file %s to outputfile %s" % (inputf, outputf)

sigma = 1.6

h5f = h5py.File(inputf,"r")

#volume = h5f["volume/data"][0,:,:,:,0]
volume = h5f["sbfsem"][:,:450,:450]

print "input volume shape: ", volume.shape
print "input volume size: ", volume.nbytes / 1024**2, "MB"
fvol = volume.astype(numpy.float32)
volume_feat = vigra.filters.hessianOfGaussianEigenvalues(fvol,sigma)[:,:,:,0]
volume_ma = numpy.max(volume_feat)
volume_mi = numpy.min(volume_feat)
volume_feat = (volume_feat - volume_mi) * 255.0 / (volume_ma-volume_mi)
print "Watershed..."
labelVolume = vigra.analysis.watersheds(volume_feat)[0].astype(numpy.int32)

print labelVolume.shape, labelVolume.dtype
mst = MSTSegmentor(labelVolume, volume_feat.astype(numpy.float32), edgeWeightFunctor = "minimum")
mst.raw = volume

mst.saveH5(outputf,"graph")

