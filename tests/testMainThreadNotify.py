import numpy, vigra
import time
from lazyflow.graph import *
import gc
from lazyflow import roi
import threading

from lazyflow.operators.operators import OpArrayCache, OpArrayPiper, OpMultiArrayPiper, OpMultiMultiArrayPiper
from lazyflow.operators.obsoleteOperators import OpArrayBlockCache, OpArraySliceCache, OpArraySliceCacheBounding

from lazyflow import operators

__testing__ = False

from tests.mockOperators import OpA, OpB, OpC


g = Graph(numThreads = 2)

source0 = OpArrayPiper(g)
source0.inputs["Input"].setValue(numpy.zeros(shape = (200,100), dtype=numpy.uint8))

opa1 = OpA(g)
opa1.inputs["Input"].connect(source0.outputs["Output"])

print "Starting wait request..."
opa1.outputs["Output"][:].allocate().wait()
print "... wait request finished"


obc = operators.Op5ToMulti(g)

obc.inputs["Input0"].connect(opa1.outputs["Output"])


print "FFFFFFFFFFFFFFFF", obc.outputs["Outputs"], len(obc.outputs["Outputs"])

def closure(result, fuchs):
    print "...notify request finished"
    print "Result:", result
    print "Fuchs:", fuchs

print "Starting notify request..."
opa1.outputs["Output"][:].allocate().notify(closure, fuchs = "Foxxy")
print "other stuff in mainthread"
import time
time.sleep(3)


g.finalize()