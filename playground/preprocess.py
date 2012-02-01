import numpy, vigra
import time
from lazyflow.graph import *
import gc
import lazyflow.roi
import threading
from lazyflow import operators
import sys
import scipy.ndimage as ndimage

import pyximport; pyximport.install()
import adjacencyGraph


def detect_local_minima(arr):
    # http://stackoverflow.com/questions/3684484/peak-detection-in-a-2d-array/3689710#3689710
    """
    Takes an array and detects the troughs using the local maximum filter.
    Returns a boolean mask of the troughs (i.e. 1 when
    the pixel's value is the neighborhood maximum, 0 otherwise)
    """
    # define an connected neighborhood
    # http://www.scipy.org/doc/api_docs/SciPy.ndimage.morphology.html#generate_binary_structure
    neighborhood = ndimage.morphology.generate_binary_structure(len(arr.shape),2)
    # apply the local minimum filter; all locations of minimum value 
    # in their neighborhood are set to 1
    # http://www.scipy.org/doc/api_docs/SciPy.ndimage.filters.html#minimum_filter
    local_min = (ndimage.filters.minimum_filter(arr, footprint=neighborhood)==arr)
    # local_min is a mask that contains the peaks we are 
    # looking for, but also the background.
    # In order to isolate the peaks we must remove the background from the mask.
    # 
    # we create the mask of the background
    background = (arr==0)
    # 
    # a little technicality: we must erode the background in order to 
    # successfully subtract it from local_min, otherwise a line will 
    # appear along the background border (artifact of the local minimum filter)
    # http://www.scipy.org/doc/api_docs/SciPy.ndimage.morphology.html#binary_erosion
    eroded_background = ndimage.morphology.binary_erosion(
        background, structure=neighborhood, border_value=1)
    # 
    # we obtain the final mask, containing only peaks, 
    # by removing the background from the local_min mask
    detected_minima = local_min - eroded_background
    return numpy.where(detected_minima)       
print "Preprocessing"

if len(sys.argv) >= 2:
  inputf = sys.argv[1]             
else:
  inputf="/home/cstraehl/Projects/PHD/benchmarks/denk-block-200/d-carving-200.h5"

g = Graph()

reader = operators.OpH5Reader(g)
feature = operators.OpHessianOfGaussianEigenvalues(g)
cache = operators.OpArrayCache(g)


reader.connect(Filename = inputf, hdf5Path = "volume/data")
feature.connect(Input = reader.outputs["Image"], scale = 1.6)
cache.connect(Input = feature.outputs["Output"])



volumeFeatures = cache.outputs["Output"][:].allocate().wait()[0,:,:,:,0]
import scipy.ndimage
minima = scipy.ndimage.minimum_filter(volumeFeatures, size=2)
local_min = numpy.where(volumeFeatures == minima, 1, 0)


local_min_label, label_count = scipy.ndimage.measurements.label(local_min)

#local_min_ws = scipy.ndimage.watershed_ift(result,local_min_label)
labelVolume = adjacencyGraph.seededTurboWS(local_min_label,volumeFeatures)
#print local_min_ws


g = adjacencyGraph.CooGraph()
g.fromLabelVolume(labelVolume, volumeFeatures)

ag = g.toAdj()
ag.seededWS(numpy.array([[3,1],[1000,2]]).astype(numpy.int32))

print "Finished"
#adjacencyGraph.buildGraphFromCOO(g[0],g[1],g[2])
print "Finished2"
