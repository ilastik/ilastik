import numpy, vigra
import time
from lazyflow.graph import *
import gc
import lazyflow.roi
import threading

from lazyflow import operators

from lazyflow.operators.operators import OpArrayCache, OpArrayPiper, OpMultiArrayPiper, OpMultiMultiArrayPiper
from lazyflow.operators.obsoleteOperators import OpArrayBlockCache, OpArraySliceCache, OpArraySliceCacheBounding

__testing__ = False

from tests.mockOperators import OpA, OpB, OpC

Operators.registerOperatorSubclasses()

g = Graph(numThreads = 2)

source0 = OpArrayPiper(g)
source0.inputs["Input"].setValue(numpy.zeros(shape = (200,100), dtype=numpy.uint8))

opa1 = OpA(g)
opa2 = OpB(g)

opb = OpMultiArrayPiper(g)
opc = OpB(g)
opd = OpArrayCache(g)
ope = OpMultiArrayPiper(g)


opa1.inputs["Input"].connect(source0.outputs["Output"])
opa2.inputs["Input"].connect(source0.outputs["Output"])

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


assert (ope.outputs["MultiOutput"][0][:,:].allocate().wait() == 1).all(), numpy.nonzero(ope.outputs["MultiOutput"][0][:].allocate().wait() - 1)
assert (ope.outputs["MultiOutput"][1][:,:].allocate().wait() == 2).all(), numpy.nonzero(ope.outputs["MultiOutput"][0][:].allocate().wait() - 2)

assert len(opb.outputs["MultiOutput"]) == 2, len(opb.outputs["MultiOutput"])
assert len(opc.outputs["Output"]) == 2, len(opc.outputs["Output"])
assert len(opd.outputs["Output"]) == 2, len(opd.outputs["Output"])
assert len(ope.outputs["MultiOutput"]) == 2, len(ope.outputs["MultiOutput"])

opb.inputs["MultiInput"].connectAdd(source0.outputs["Output"])

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

assert (ope.outputs["MultiOutput"][0][:,:].allocate().wait() == 1).all(), numpy.nonzero(ope.outputs["MultiOutput"][0][:].allocate().wait() - 1)
#assert (ope.outputs["MultiOutput"][1][:,:].allocate().wait() == 2).all(), numpy.nonzero(ope.outputs["MultiOutput"][2][:].allocate().wait() - 2)
#assert (ope.outputs["MultiOutput"][2][:,:].allocate().wait() == 1).all(), numpy.nonzero(ope.outputs["MultiOutput"][1][:].allocate().wait() - 1)

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

source0 = OpArrayPiper(g)
source0.inputs["Input"].setValue(numpy.zeros(shape = (200,100), dtype=numpy.uint8))

opb = OpMultiMultiArrayPiper(g)

for i in range(7):
    opas = []
    opas.append(OpA(g))
    opas.append(OpB(g))
    opb0 = OpMultiArrayPiper(g)
    
    opas[0].inputs["Input"].connect(source0.outputs["Output"])
    opas[1].inputs["Input"].connect(source0.outputs["Output"])
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
    assert (opb2.outputs["MultiOutput"][i][i % 2][:].allocate().wait() == 0).all()
    assert (opb2.outputs["MultiOutput"][i][(i + 1) % 2][:].allocate().wait() == 1).all()
    #assert (ope.outputs["MultiOutput"][i][0][:,:] == 1).all()
    #assert (ope.outputs["MultiOutput"][i][0][:,:] == 2).all()    

for i in range(7):
    print "Checking", i
    assert (ope.outputs["MultiOutput"][i][i % 2][:].allocate().wait() == 1).all()
    assert (ope.outputs["MultiOutput"][i][(i + 1) % 2][:].allocate().wait() == 2).all()

for i in range(7):
    print "Checking", i
    assert (ope.outputs["MultiOutput"][i][i % 2][:].allocate().wait() == 1).all()
    assert (ope.outputs["MultiOutput"][i][(i + 1) % 2][:].allocate().wait() == 2).all()


opd.inputs["Input"].disconnect()

assert not isinstance(opd.inputs["Input"], MultiInputSlot), opd.inputs["Input"].level
assert not isinstance(opd.outputs["Output"], MultiOutputSlot), opd.outputs["Output"].level



g.finalize()



g = Graph(numThreads = 2)

opList1 = operators.ListToMultiOperator(g)
opList1.inputs["List"].setValue(["ostrich.jpg"])
opList2 = operators.ListToMultiOperator(g)
opList2.inputs["List"].setValue(["ostrich.jpg","ostrich.jpg"])
opList3 = operators.ListToMultiOperator(g)
opList3.inputs["List"].setValue(["ostrich.jpg","ostrich.jpg","ostrich.jpg"])


opRead = operators.OpImageReader(g)
opRead.inputs["Filename"].connect(opList2.outputs["Items"])


opRead.outputs["Image"][0][:].allocate().wait()

assert len(opRead.outputs["Image"]) == 2

opRead.inputs["Filename"].connect(opList1.outputs["Items"])
assert len(opRead.outputs["Image"]) == 1

opRead.inputs["Filename"].connect(opList3.outputs["Items"])
assert len(opRead.outputs["Image"]) == 3


print "UUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUU"
opRead.inputs["Filename"].disconnect()
print "UUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUU"
opRead.inputs["Filename"].setValue("ostrich.jpg")
assert opRead.outputs["Image"].level == 0, opRead.outputs["Image"].level

g.finalize()