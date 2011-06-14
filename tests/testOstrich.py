import numpy, vigra
import time
from lazyflow import graph
import gc
from lazyflow import roi
import sys
import copy

from lazyflow.operators.operators import OpArrayCache, OpArrayPiper, OpMultiArrayPiper, OpMultiMultiArrayPiper
from tests.mockOperators import ArrayProvider, SingleValueProvider
from lazyflow.graph import MultiInputSlot

from test_classification_1 import OpGaussianSmooting

img = vigra.impex.readImage("ostrich.jpg")

ostrichProvider = ArrayProvider("Ostrich_Input", shape=img.shape, dtype=img.dtype, axistags=img.axistags)
ostrichProvider.setData(img)

graph = graph.Graph(numThreads=2)

sigmaProvider = SingleValueProvider("Sigma", float)
sigmaProvider.setValue(float(5))

gaussianSmoother = OpGaussianSmooting(graph)

gaussianSmoother.inputs["Input"].connect(ostrichProvider)
gaussianSmoother.inputs["Sigma"].connect(sigmaProvider)

smoothedOstrich = gaussianSmoother.outputs["Output"][:,:,:].allocate()
a = gaussianSmoother.outputs["Output"].axistags
smoothedOstrich = smoothedOstrich.view(vigra.VigraArray)
smoothedOstrich.axistags=a
vigra.impex.writeImage(smoothedOstrich, "smoothed_ostrich.png")

graph.finalize()