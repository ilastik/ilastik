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

assert(len(sys.argv)==3,"please specify input.h5 and output.h5 !")
inputf = sys.argv[1]             
outputf = sys.argv[2]

g = Graph()

reader = operators.OpH5Reader(g)
writer = operators.OpH5Writer(g)

feature = operators.OpHessianOfGaussianEigenvalues(g)
cache = operators.OpArrayCache(g)


reader.connect(Filename = inputf, hdf5Path = "volume/data")
feature.connect(Input = reader.outputs["Image"], scale = 1.6)
cache.connect(Input = feature.outputs["Output"])
writer.connect(Image = cache.outputs["Output"], Filename = outputf, hdf5Path = "volume/data", blockShape = 88)

writer.outputs["WriteImage"][0].allocate().wait()

print
print
print "Input has shape=%r, output shape=%r" % (reader.outputs["Image"].shape, feature.outputs["Output"].shape)
print



result = cache.outputs["Output"][:].allocate().wait()
import scipy.ndimage
print "A0"
minima = scipy.ndimage.minimum_filter(result, size=2)
print "A1"
local_min = numpy.where(result == minima, 1, 0)

print "A2"

local_min_label, label_count = scipy.ndimage.measurements.label(local_min)

print "A3"
#local_min_ws = scipy.ndimage.watershed_ift(result,local_min_label)
local_min_ws = adjacencyGraph.seededTurboWS(local_min_label[0,:,:,:,0],result[0,:,:,:,0])
#print local_min_ws


print "A4"
tresult = result[0,:,:,:,0]
tlocal_min_ws = local_min_ws
g = adjacencyGraph.buildAdjacencyGraph(tlocal_min_ws, tresult)

print "Finished"
adjacencyGraph.buildGraphFromCOO(g[0],g[1],g[2])
print "Finished2"
