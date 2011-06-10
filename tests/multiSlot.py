import numpy, vigra
import time
from graph import *
import gc
import roi
import threading

from operators.operators import OpArrayCache, OpArrayPiper, OpMultiArrayPiper
from operators.obsoleteOperators import OpArrayBlockCache, OpArraySliceCache, OpArraySliceCacheBounding

__testing__ = False

from tests.mockOperators import OpA, OpB, OpC, ArrayProvider

g = Graph(numThreads = 2)

source0 = ArrayProvider( "Zeros", shape = (200,100), dtype=numpy.uint8)
source0.setData(numpy.zeros(source0.shape,dtype = source0.dtype))

source1 = ArrayProvider( "Zeros", shape = (300,50), dtype=numpy.uint8)
source1.setData(numpy.zeros(source1.shape,dtype = source1.dtype))


opa = OpMultiArrayPiper(g)
opb = OpMultiArrayPiper(g)
opc = OpMultiArrayPiper(g)

opd = OpA(g)
ope = OpB(g)
ope2 = OpB(g)

opa.inputs["MultiInput"].resize(2)
opa.inputs["MultiInput"].connect(source0)
opa.inputs["MultiInput"].connect(source1)

opb.inputs["MultiInput"].connect(opa.outputs["MultiOutput"])
assert len(opb.outputs["MultiOutput"]) == 2, len(opb.outputs["MultiOutput"])

opd.inputs["Input"].connect(opb.outputs["MultiOutput"][0])
ope.inputs["Input"].connect(opb.outputs["MultiOutput"][1])
ope2.inputs["Input"].connect(ope.outputs["Output"])

assert (opa.outputs["MultiOutput"][0][:,:].allocate() == 0).all()
assert (opa.outputs["MultiOutput"][1][:,:].allocate() == 0).all()

assert (opb.outputs["MultiOutput"][0][:,:].allocate() == 0).all()
assert (opb.outputs["MultiOutput"][0][:,:].allocate() == 0).all()

assert (opd.outputs["Output"][:,:].allocate() == 0).all()
assert (ope.outputs["Output"][:,:].allocate() == 1).all()

opc.inputs["MultiInput"].resize(2)
opc.inputs["MultiInput"][0].connect(opd.outputs["Output"])
opc.inputs["MultiInput"][1].connect(ope2.outputs["Output"])

print "aksjdkajsdkjad", len(opc.outputs["MultiOutput"])

assert (opc.outputs["MultiOutput"][0][:,:].allocate() == 0).all(), numpy.nonzero(opc.outputs["MultiOutput"][0][:,:].allocate())
assert (opc.outputs["MultiOutput"][1][:,:].allocate() == 2).all(), numpy.nonzero(opc.outputs["MultiOutput"][0][:,:].allocate() - 2)

g.finalize()