import numpy
import time
import sys
import h5py
from cylemon.segmentation import MSTSegmentor


import vigra
import numpy




def preprocess(inputf,outputf,sigma = 1.6):
    
    print "preprocessing file %s to outputfile %s" % (inputf, outputf)
    
    h5f = h5py.File(inputf,"r")
    
    volume = h5f["raw"][:35,:35,:35]
    
    print "input volume shape: ", volume.shape
    print "input volume size: ", volume.nbytes / 1024**2, "MB"
    fvol = volume.astype(numpy.float32)
    #volume_feat = vigra.filters.gaussianGradientMagnitude(fvol,sigma)
    
    volume_feat = vigra.filters.hessianOfGaussianEigenvalues(fvol,sigma)[:,:,:,0]
    
    volume_ma = numpy.max(volume_feat)
    volume_mi = numpy.min(volume_feat)
    volume_feat = (volume_feat - volume_mi) * 255.0 / (volume_ma-volume_mi)
    print "Watershed..."
    labelVolume = vigra.analysis.watersheds(volume_feat)[0].astype(numpy.int32)
    print labelVolume
    print labelVolume.shape, labelVolume.dtype
    mst = MSTSegmentor(labelVolume, volume_feat.astype(numpy.float32), edgeWeightFunctor = "minimum")
    mst.raw = volume
    mst.saveH5("C:/Users/Ben/Desktop/carvingData/unprecarv_part35.h5","graph")
    #mst2 = MSTSegmentor.loadH5("C:/Users/Ben/Desktop/carvingData/test1.ilp","preprocessing/graph")
    
    
#preprocess("C:/Users/Ben/Desktop/carvingData/unprecarv.h5","C:/Users/Ben/Desktop/carvingData/temp.h5",1)
