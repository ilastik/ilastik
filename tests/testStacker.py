import vigra
import numpy
import threading
from lazyflow.graph import *
from lazyflow import operators
from lazyflow.operators import *

from numpy.testing import *

import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)


def testFullAllocate():

    nx = 5
    ny = 10
    nz = 2
    nc = 7
    stack = numpy.random.rand(nx, ny, nz, nc)

    g = Graph()

    #assume that the slicer works
    slicerX = OpMultiArraySlicer(g)
    slicerX.inputs["Input"].setValue(stack)
    slicerX.inputs["AxisFlag"].setValue('x')

    #insert the x dimension
    stackerX = OpMultiArrayStacker(g)
    stackerX.inputs["AxisFlag"].setValue('x')
    stackerX.inputs["AxisIndex"].setValue(0)
    stackerX.inputs["Images"].connect(slicerX.outputs["Slices"])

    newdata = stackerX.outputs["Output"][:].allocate().wait()
    assert_array_equal(newdata, stack)

    print "1st part ok................."
    #merge stuff that already has an x dimension
    stack2 = numpy.random.rand(nx-1, ny, nz, nc)

    opMulti = Op5ToMulti(g)
    opMulti.inputs["Input0"].setValue(stack)
    opMulti.inputs["Input1"].setValue(stack2)

    #print "OPMULTI: ", len(opMulti.outputs["Outputs"])

    stackerX2 = OpMultiArrayStacker(g)

    stackerX2.inputs["Images"].connect(opMulti.outputs["Outputs"])
    stackerX2.inputs["AxisFlag"].setValue('x')
    stackerX2.inputs["AxisIndex"].setValue(0)

    #print "STACKER: ", stackerX2.outputs["Output"].shape

    newdata = stackerX2.outputs["Output"][:].allocate().wait()
    bothstacks = numpy.concatenate((stack, stack2), axis=0)
    assert_array_equal(newdata, bothstacks)
    #print newdata.shape, bothstacks.shape

    print "2nd part ok................."
    #print "------------------------------------------------------------"
    #print "------------------------------------------------------------"
    #print "------------------------------------------------------------"
    ##### channel

    #assume that the slicer works
    slicerC = OpMultiArraySlicer(g)
    slicerC.inputs["Input"].setValue(stack)
    slicerC.inputs["AxisFlag"].setValue('c')

    #insert the c dimension

    stackerC = OpMultiArrayStacker(g)
    stackerC.inputs["AxisFlag"].setValue('c')
    stackerC.inputs["AxisIndex"].setValue(3)
    stackerC.inputs["Images"].connect(slicerC.outputs["Slices"])

    newdata = stackerC.outputs["Output"][:].allocate().wait()
    assert_array_equal(newdata, stack)

    print "3rd part ok................."
    #print "STACKER: ", stackerC.outputs["Output"].shape

    #merge stuff that already has an x dimension
    stack3 = numpy.random.rand(nx, ny, nz, nc-1)

    opMulti = Op5ToMulti(g)
    opMulti.inputs["Input0"].setValue(stack)
    opMulti.inputs["Input1"].setValue(stack3)

    stackerC2 = OpMultiArrayStacker(g)
    stackerC2.inputs["AxisFlag"].setValue('c')
    stackerC2.inputs["AxisIndex"].setValue(3)
    stackerC2.inputs["Images"].connect(opMulti.outputs["Outputs"])

    newdata = stackerC2.outputs["Output"][:].allocate().wait()
    bothstacks = numpy.concatenate((stack, stack3), axis=3)
    assert_array_equal(newdata, bothstacks)
    print "4th part ok................."

    g.finalize()


def testPartialAllocate():

    nx = 15
    ny = 20
    nz = 17
    nc = 7
    stack = numpy.random.rand(nx, ny, nz, nc)

    g = Graph()

    #assume that the slicer works
    slicerX = OpMultiArraySlicer(g)
    slicerX.inputs["Input"].setValue(stack)
    slicerX.inputs["AxisFlag"].setValue('x')

    #insert the x dimension
    stackerX = OpMultiArrayStacker(g)
    stackerX.inputs["AxisFlag"].setValue('x')
    stackerX.inputs["AxisIndex"].setValue(0)
    stackerX.inputs["Images"].connect(slicerX.outputs["Slices"])

    key = (slice(2, 3, None), slice(15, 18, None), slice(12, 15, None), slice(0, 7, None))
    newdata = stackerX.outputs["Output"][key].allocate().wait()
    substack = stack[key]
    print newdata.shape, substack.shape
    assert_array_equal(newdata, substack)

if __name__=="__main__":
    testFullAllocate()
    testPartialAllocate()
