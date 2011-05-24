import numpy, vigra
import time
from graph import *
import gc
import roi
import threading

from operators.operators import OpArrayCache, OpArrayPiper, OpMultiArrayPiper, OpMultiMultiArrayPiper
from operators.obsoleteOperators import OpArrayBlockCache, OpArraySliceCache, OpArraySliceCacheBounding

__testing__ = False

from tests.mockOperators import OpA, OpB, OpC, ArrayProvider

g = Graph(numThreads = 2)

source0 = ArrayProvider( "Zeros", shape = (200,100), dtype=numpy.uint8)
source0.setData(numpy.zeros(source0.shape,dtype = source0.dtype))

opa1 = OpA(g)
opa2 = OpB(g)

opb = OpMultiArrayPiper(g)
opc = OpB(g)
opd = OpArrayCache(g)
ope = OpMultiArrayPiper(g)


opa1.inputs["Input"].connect(source0)
opa2.inputs["Input"].connect(source0)

opb.inputs["MultiInput"].connectAdd(opa1.outputs["Output"])
opb.inputs["MultiInput"].connectAdd(opa2.outputs["Output"])

opc.inputs["Input"].connect(opb.outputs["MultiOutput"])
opd.inputs["Input"].connect(opc.outputs["Output"])
ope.inputs["MultiInput"].connect(opd.outputs["Output"])

print "inputs:"
print len(opb.inputs["MultiInput"])
print  len(opc.inputs["Input"])
print len(opd.inputs["Input"])
print len(ope.inputs["MultiInput"])

print "outputs:"
print len(opb.outputs["MultiOutput"])
print len(opc.outputs["Output"])
print len(opd.outputs["Output"])
print len(ope.outputs["MultiOutput"])


assert (ope.outputs["MultiOutput"][0][:,:].allocate() == 1).all(), numpy.nonzero(ope.outputs["MultiOutput"][0][:].allocate() - 1)
assert (ope.outputs["MultiOutput"][1][:,:].allocate() == 2).all(), numpy.nonzero(ope.outputs["MultiOutput"][0][:].allocate() - 2)

assert len(opb.outputs["MultiOutput"]) == 2, len(opb.outputs["MultiOutput"])
assert len(opc.outputs["Output"]) == 2, len(opc.outputs["Output"])
assert len(opd.outputs["Output"]) == 2, len(opd.outputs["Output"])
assert len(ope.outputs["MultiOutput"]) == 2, len(ope.outputs["MultiOutput"])

opb.inputs["MultiInput"].connectAdd(source0)

print "Added other input"
print "inputs:"
print len(opb.inputs["MultiInput"])
print  len(opc.inputs["Input"])
print len(opd.inputs["Input"])
print len(ope.inputs["MultiInput"])

print "outputs:"
print len(opb.outputs["MultiOutput"])
print len(opc.outputs["Output"])
print len(opd.outputs["Output"])
print len(ope.outputs["MultiOutput"])

assert len(opb.inputs["MultiInput"]) == 3, len(opb.inputs["MultiInput"])
assert len(opc.inputs["Input"]) == 3,  len(opc.inputs["Input"])
assert len(opd.inputs["Input"]) == 3,  len(opd.inputs["Input"])
assert len(ope.inputs["MultiInput"]) == 3, len(ope.inputs["MultiInput"])


assert len(opb.outputs["MultiOutput"]) == 3, len(opb.outputs["MultiOutput"])
assert len(opc.outputs["Output"]) == 3, len(opc.outputs["Output"])
assert len(opd.outputs["Output"]) == 3, len(opd.outputs["Output"])
assert len(ope.outputs["MultiOutput"]) == 3, len(ope.outputs["MultiOutput"])

assert (ope.outputs["MultiOutput"][0][:,:].allocate() == 1).all(), numpy.nonzero(ope.outputs["MultiOutput"][0][:].allocate() - 1)
#assert (ope.outputs["MultiOutput"][1][:,:].allocate() == 2).all(), numpy.nonzero(ope.outputs["MultiOutput"][2][:].allocate() - 2)
#assert (ope.outputs["MultiOutput"][2][:,:].allocate() == 1).all(), numpy.nonzero(ope.outputs["MultiOutput"][1][:].allocate() - 1)

opb.inputs["MultiInput"].removeSlot(1)
#opb.inputs["MultiInput"].removeSlot(1)

print "Removed input"
print "inputs:"
print len(opb.inputs["MultiInput"])
print  len(opc.inputs["Input"])
print len(opd.inputs["Input"])
print len(ope.inputs["MultiInput"])

print "outputs:"
print len(opb.outputs["MultiOutput"])
print len(opc.outputs["Output"])
print len(opd.outputs["Output"])
print len(ope.outputs["MultiOutput"])





assert len(opb.outputs["MultiOutput"]) == 2, len(opb.outputs["MultiOutput"])
assert len(opc.outputs["Output"]) == 2, len(opc.outputs["Output"])
assert len(opd.outputs["Output"]) == 2, len(opd.outputs["Output"])
assert len(ope.outputs["MultiOutput"]) == 2, len(ope.outputs["MultiOutput"])

g.finalize()





g = Graph(numThreads = 2)

source0 = ArrayProvider( "Zeros", shape = (200,100), dtype=numpy.uint8)
source0.setData(numpy.zeros(source0.shape,dtype = source0.dtype))

opb = OpMultiMultiArrayPiper(g)

for i in range(7):
    opas = []
    opas.append(OpA(g))
    opas.append(OpB(g))
    opb0 = OpMultiArrayPiper(g)
    
    opas[0].inputs["Input"].connect(source0)
    opas[1].inputs["Input"].connect(source0)
    0
    opb0.inputs["MultiInput"].connectAdd(opas[i % 2].outputs["Output"])
    opb0.inputs["MultiInput"].connectAdd(opas[(i + 1) % 2].outputs["Output"])
    
    opb.inputs["MultiInput"].connectAdd(opb0.outputs["MultiOutput"])

print opb.inputs["MultiInput"].level, len(opb.inputs["MultiInput"])

opb2 = OpMultiArrayPiper(g)
opc = OpB(g)
opd = OpArrayCache(g)
ope = OpMultiArrayPiper(g)

opb2.inputs["MultiInput"].connect(opb.outputs["MultiOutput"])

print "B2in: ",opb2.inputs["MultiInput"].level, len(opb2.inputs["MultiInput"])
print "B2Out: ", opb2.outputs["MultiOutput"].level, len(opb2.outputs["MultiOutput"])

opc.inputs["Input"].connect(opb.outputs["MultiOutput"])
print "Done connecting C"

opd.inputs["Input"].connect(opc.outputs["Output"])
ope.inputs["MultiInput"].connect(opd.outputs["Output"])


print "Bin: ",opb.inputs["MultiInput"].level, len(opb.inputs["MultiInput"])
print "BOut: ", opb.outputs["MultiOutput"].level, len(opb.outputs["MultiOutput"])

print "Cin: ",opc.inputs["Input"].level, len(opc.inputs["Input"])
print "COut: ", opc.outputs["Output"].level, len(opc.outputs["Output"])

print "Din: ",opd.inputs["Input"].level, len(opd.inputs["Input"])
print "DOut: ", opd.outputs["Output"].level, len(opd.outputs["Output"])

print "Ein: ",ope.inputs["MultiInput"].level, len(ope.inputs["MultiInput"])
print "EOut: ", ope.outputs["MultiOutput"].level, len(ope.outputs["MultiOutput"])

for i in range(7):
    print "Checking b2, ", i
    assert (opb2.outputs["MultiOutput"][i][i % 2][:].allocate() == 0).all()
    assert (opb2.outputs["MultiOutput"][i][(i + 1) % 2][:].allocate() == 1).all()
    #assert (ope.outputs["MultiOutput"][i][0][:,:] == 1).all()
    #assert (ope.outputs["MultiOutput"][i][0][:,:] == 2).all()    

for i in range(7):
    print "Checking", i
    assert (ope.outputs["MultiOutput"][i][i % 2][:].allocate() == 1).all()
    assert (ope.outputs["MultiOutput"][i][(i + 1) % 2][:].allocate() == 2).all()

for i in range(7):
    print "Checking", i
    assert (ope.outputs["MultiOutput"][i][i % 2][:].allocate() == 1).all()
    assert (ope.outputs["MultiOutput"][i][(i + 1) % 2][:].allocate() == 2).all()


opd.inputs["Input"].disconnect()

assert not isinstance(opd.inputs["Input"], MultiInputSlot), opd.inputs["Input"].level
assert not isinstance(opd.inputs["Output"], MultiInputSlot), opd.outputs["Output"].level