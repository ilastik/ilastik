import numpy, vigra
import time
from lazyflow.graph import *
import gc
import lazyflow.roi
import threading

from lazyflow import operators

from lazyflow.operators import OpArrayCache, OpArrayPiper, OpMultiArrayPiper, OpMultiMultiArrayPiper
from lazyflow.operators import OpArrayBlockCache, OpArraySliceCache, OpArraySliceCacheBounding

__testing__ = False

from tests.mockOperators import OpA, OpB, OpC

Operators.registerOperatorSubclasses()

g = Graph()

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

opMulti = operators.Op5ToMulti(g)
opMulti.inputs["Input1"].connect(opa1.outputs["Output"])
opMulti.inputs["Input2"].connect(opa2.outputs["Output"])

opb.inputs["MultiInput"].connect(opMulti.outputs["Outputs"])


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


assert (ope.outputs["MultiOutput"][0][:].allocate().wait() == 1).all(), ope.outputs["MultiOutput"][0][:].allocate().wait()
assert (ope.outputs["MultiOutput"][1][:].allocate().wait() == 2).all(), ope.outputs["MultiOutput"][1][:].allocate().wait()

assert len(opb.outputs["MultiOutput"]) == 2, len(opb.outputs["MultiOutput"])
assert len(opc.outputs["Output"]) == 2, len(opc.outputs["Output"])
assert len(opd.outputs["Output"]) == 2, len(opd.outputs["Output"])
assert len(ope.outputs["MultiOutput"]) == 2, len(ope.outputs["MultiOutput"])

opMulti.inputs["Input3"].connect(source0.outputs["Output"])

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






g = Graph()

opList1 = operators.ListToMultiOperator(g)
opList1.inputs["List"].setValue(["ostrich.jpg"])
opList2 = operators.ListToMultiOperator(g)
opList2.inputs["List"].setValue(["ostrich.jpg","ostrich.jpg"])
opList3 = operators.ListToMultiOperator(g)
opList3.inputs["List"].setValue(["ostrich.jpg","ostrich.jpg","ostrich.jpg"])


opRead = operators.OpImageReader(g)
opRead.inputs["Filename"].connect(opList2.outputs["Items"])


opRead.outputs["Image"][0][:].allocate().wait()



opGauss = operators.OpGaussianSmoothing(g)
opGauss.inputs["sigma"].setValue(2.0)
opGauss.inputs["Input"].connect(opRead.outputs["Image"])

opGauss2 = operators.OpGaussianSmoothing(g)
opGauss2.inputs["sigma"].setValue(2.0)
opGauss2.inputs["Input"].connect(opGauss.outputs["Output"])

opMulti = operators.Op5ToMulti(g)
opMulti.inputs["Input1"].connect(opGauss.outputs["Output"])

opStack = operators.OpMultiArrayStacker(g)
opStack.inputs["Images"].connect(opMulti.outputs["Outputs"])
opStack.inputs["AxisFlag"].setValue('c')
opStack.inputs["AxisIndex"].setValue(2)

assert len(opGauss.outputs["Output"]) == 2
assert len(opRead.outputs["Image"]) == 2
assert len(opStack.outputs["Output"]) == 2

opRead.inputs["Filename"].connect(opList1.outputs["Items"])

assert len(opRead.outputs["Image"]) == 1, len(opRead.outputs["Image"])
assert len(opGauss.outputs["Output"]) == 1, len(opGauss.outputs["Output"])
assert len(opGauss2.outputs["Output"]) == 1, len(opGauss2.outputs["Output"])
print "XXXXXXXXXX", len(opStack.inputs["Images"])
assert len(opStack.outputs["Output"]) == 1, len(opStack.outputs["Output"])

print "UUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUU"
opRead.inputs["Filename"].connect(opList3.outputs["Items"])
print "UUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUU"

assert len(opRead.outputs["Image"]) == 3,len(opRead.outputs["Image"])
assert len(opStack.inputs["Images"]) == 3,len(opStack.Inputs["Images"])
assert len(opStack.outputs["Output"]) == 3,len(opStack.outputs["Output"])

#opRead.inputs["Filename"].disconnect()
#
#opRead.inputs["Filename"].setValue("ostrich.jpg")
#assert opRead.outputs["Image"].level == 0, opRead.outputs["Image"].level

g.finalize()
