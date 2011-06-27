import numpy, vigra
import time
from lazyflow import graph
import gc
from lazyflow import roi
import sys
import copy

from lazyflow.operators.operators import OpArrayCache, OpArrayPiper, OpMultiArrayPiper, OpMultiMultiArrayPiper
from lazyflow.operators.valueProviders import ArrayProvider, SingleValueProvider
from lazyflow.graph import MultiInputSlot

from lazyflow.operators.vigraOperators import *


graph = graph.Graph(numThreads=2)

fileNameProvider = SingleValueProvider("Filename", object)
fileNameProvider.setValue("ostrich.jpg")

ostrichProvider = OpImageReader(graph)
ostrichProvider.inputs["Filename"].connect(fileNameProvider)


fileNameProvider2 = SingleValueProvider("Filename", object)
fileNameProvider2.setValue("ostrich_piped.jpg")


ostrichWriter = OpImageWriter(graph)
ostrichWriter.inputs["Filename"].connect(fileNameProvider2)
ostrichWriter.inputs["Image"].connect(ostrichProvider.outputs["Image"])

sigmaProvider = SingleValueProvider("Sigma", float)
sigmaProvider.setValue(float(10))

operators = [OpGaussianSmoothing,OpOpening, OpClosing,OpLaplacianOfGaussian]

for op in operators:
    
    operinstance = op(graph)
    operinstance.inputs["Input"].connect(ostrichProvider.outputs["Image"])
    operinstance.inputs["Sigma"].setValue(float(10)) #connect(sigmaProvider)
    result = operinstance.outputs["Output"][:,:,:].allocate().wait()
    if result.shape[-1] > 3:
        result = result[...,0:3]
    
    a = operinstance.outputs["Output"].axistags
    result = result.view(vigra.VigraArray)
    result.axistags=a
    vigra.impex.writeImage(result, "ostrich_%s.png" %(op.name,))

graph.finalize()