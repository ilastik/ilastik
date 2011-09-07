import numpy, vigra
import time
from lazyflow import graph
import gc
from lazyflow import roi
import sys
import copy

from lazyflow.operators.operators import OpArrayCache, OpArrayPiper, OpMultiArrayPiper, OpMultiMultiArrayPiper

from lazyflow.graph import MultiInputSlot

from lazyflow.operators.vigraOperators import *


graph = graph.Graph()

ostrichProvider = OpImageReader(graph)
ostrichProvider.inputs["Filename"].setValue("ostrich.jpg")


ostrichWriter = OpImageWriter(graph)
ostrichWriter.inputs["Filename"].setValue("ostrich_piped.jpg")
ostrichWriter.inputs["Image"].connect(ostrichProvider.outputs["Image"])


operators = [OpGaussianSmoothing,OpOpening, OpClosing, OpHessianOfGaussian]

print "Beginning vigra operator tests..."
for op in operators:
    
    operinstance = op(graph)
    operinstance.inputs["Input"].connect(ostrichProvider.outputs["Image"])
    operinstance.inputs["sigma"].setValue(float(10)) #connect(sigmaProvider)
    result = operinstance.outputs["Output"][:,:,:].allocate().wait()
    if result.shape[-1] > 3:
        result = result[...,0:3]
    
    a = operinstance.outputs["Output"].axistags
    result = result.view(vigra.VigraArray)
    result.axistags=a
    vigra.impex.writeImage(result, "ostrich_%s.png" %(op.name,))



g1 = OpHessianOfGaussian(graph)
g1.inputs["Input"].connect(ostrichProvider.outputs["Image"])
g1.inputs["sigma"].setValue(float(30)) #connect(sigmaProvider)

print "JJJJJJJJJJ1", g1.outputs["Output"].shape


g4 = OpGaussianSmoothing(graph)
g4.inputs["Input"].connect(ostrichProvider.outputs["Image"])
g4.inputs["sigma"].setValue(float(30)) #connect(sigmaProvider)

#g4.outputs["Output"][:,:,:].allocate().wait()

print "JJJJJJJJJJ4", g4.outputs["Output"].shape


g2 = Op5ToMulti(graph)
g2.inputs["Input0"].connect(ostrichProvider.outputs["Image"])
g2.inputs["Input1"].connect(g4.outputs["Output"])

g2.outputs["Outputs"][0][:,:,:].allocate().wait()

print "JJJJJJJJJJ1", g2.outputs["Outputs"][0].shape
print "JJJJJJJJJJ2", g2.outputs["Outputs"][1].shape

g3 = OpGaussianSmoothing(graph)
g3.inputs["Input"].connect(g2.outputs["Outputs"])
g3.inputs["sigma"].setValue(float(30)) #connect(sigmaProvider)

g3.outputs["Output"][0][:,:,:].allocate().wait()

print "JJJJJJJJJJ3", g3.outputs["Output"][0].shape

print "Assert that stacker does not change features"
for i in range(1,2):
    print "Checking slice",i
    time.sleep(1)
    r1  = g4.outputs["Output"][:,:,1].allocate().wait()
    r2 = g3.outputs["Output"][0][:,:,1].allocate().wait()
    
    assert (r1[:] == r2[:]).all(), i


requests = []
for i in range(100):
    r = g3.outputs["Output"][0][:,:,:].allocate()
    requests.append(r)
    
import gc

i= 0
while len(requests) > 0:
    r = requests.pop(0)
    r.wait()
    del r
    gc.collect()
    print "request", i, "finished"
    i += 1

graph.finalize()