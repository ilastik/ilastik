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

from lazyflow.operators.vigraOperators import *

img = vigra.impex.readImage("ostrich.jpg")

ostrichProvider = ArrayProvider("Ostrich_Input", shape=img.shape, dtype=img.dtype, axistags=img.axistags)
ostrichProvider.setData(img)

graph = graph.Graph(numThreads=2)

sigmaProvider = SingleValueProvider("Sigma", float)
sigmaProvider.setValue(float(10))

operators = [OpGaussianSmoothing,OpOpening, OpClosing,OpLaplacianOfGaussian]

for op in operators:
    
    operinstance = op(graph)
    operinstance.inputs["Input"].connect(ostrichProvider)
    operinstance.inputs["Sigma"].connect(sigmaProvider)
    result = operinstance.outputs["Output"][:,:,:].allocate()
    if result.shape[-1] > 3:
        result = result[...,0:3]
    
    a = operinstance.outputs["Output"].axistags
    result = result.view(vigra.VigraArray)
    result.axistags=a
    vigra.impex.writeImage(result, "ostrich_%s.png" %(op.name,))

graph.finalize()