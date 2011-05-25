import numpy, vigra
import time
import graph
import gc
import roi
import sys
import copy

from operators.operators import OpArrayCache, OpArrayPiper, OpMultiArrayPiper, OpMultiMultiArrayPiper
from mockOperators import ArrayProvider, SingleValueProvider
from graph import MultiInputSlot

from test_classification_1 import OpGaussianSmooting

img = vigra.impex.readImage("ostrich.jpg")

ostrichProvider = ArrayProvider("Ostrich_Input", shape=img.shape, dtype=img.dtype, axistags=img.axistags)
ostrichProvider.setData(img)
print "dfkdajfkajkfa", img.axistags.axisTypeCount(vigra.AxisType.Channels)
print img.shape[img.axistags.channelIndex]

graph = graph.Graph(numThreads=2)

sigmaProvider = SingleValueProvider("Sigma", float)
sigmaProvider.setValue(float(5))

gaussianSmoother = OpGaussianSmooting(graph)

gaussianSmoother.inputs["Input"].connect(ostrichProvider)
gaussianSmoother.inputs["Sigma"].connect(sigmaProvider)

smoothedOstrich = gaussianSmoother.outputs["Output"][:,:,:].allocate()

vigra.impex.writeImage(smoothedOstrich, "smoothed_ostrich.png")

graph.finalize()