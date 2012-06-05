import numpy, vigra
import time
from lazyflow.graph import *
import gc
from lazyflow import roi
import threading

from lazyflow import operators
from lazyflow.operators import *

from lazyflow import operators

__testing__ = False

from tests.mockOperators import OpA, OpB, OpC


g = Graph()

source0 = OpArrayPiper(g)
source0.inputs["Input"].setValue(numpy.zeros(shape = (200,100), dtype=numpy.uint8))

opa1 = OpA(g)
opa1.inputs["Input"].connect(source0.outputs["Output"])

print "Starting wait request..."
opa1.outputs["Output"][:].allocate().wait()
print "... wait request finished"


obc = operators.Op5ToMulti(g)

obc.inputs["Input0"].connect(opa1.outputs["Output"])


def dirtyCallback(key, fuchs):
    print "i am a ", fuchs, "and region became dirty in area", key

source0.outputs["Output"].registerDirtyCallback(dirtyCallback,fuchs = "fox")
source0.inputs["Input"][10:20,5:15] = 17



def closure(result, req, fuchs):
    req.wait()
    print "...notify request finished"
    print "Result:", result
    print "Fuchs:", fuchs

req1 = opa1.outputs["Output"][:].allocate()
req2 = opa1.outputs["Output"][:].allocate()


print "Starting notify request..."
req1.notify(closure, req = req1, fuchs = "Foxxy")
req2.notify(closure, req = req2, fuchs = "Even more Foxxy")
req1.cancel()
print "other stuff in mainthread"
import time
time.sleep(3)


g.finalize()
