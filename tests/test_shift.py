import context
from lazyflow.graph import *
from lazyflow import operators

import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)


shape = (10, 10)
dummy = numpy.zeros(shape)
for i in range(shape[0]):
    dummy[i, :] = i
    
dummyva = vigra.VigraArray(dummy, axistags=vigra.VigraArray.defaultAxistags(len(shape))) 

g = Graph(numThreads = 1, softMaxMem = 2000*1024**2)

opShift = operators.OpShift(g)
opShift.inputs["Input"].setValue(dummyva)
opShift.inputs["AxisFlag"].setValue("x")
opShift.inputs["ShiftValue"].setValue(2)

shifted = opShift.outputs["Output"][:].allocate().wait()

#print
print shifted

#test negative
#opShift.inputs["ShiftValue"].setValue(-2)
#shifted = opShift.outputs["Output"][3:8, 3:8].allocate().wait()