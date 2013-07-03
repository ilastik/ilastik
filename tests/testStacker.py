import copy
import vigra
import numpy
import threading
from lazyflow.graph import Graph, Operator, InputSlot, OutputSlot, OperatorWrapper, MetaDict
from lazyflow import operators
from lazyflow.operators import *

from lazyflow.operators.valueProviders import OpOutputProvider

from numpy.testing import *

import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

class OpTrackedOutputProvider(OpOutputProvider):
    """
    Simply provides access to an array, but records the requests it processes.
    """
    def __init__(self, *args, **kwargs):
        super( OpTrackedOutputProvider, self ).__init__( *args, **kwargs )
        self.requested_rois = []
        self._lock = threading.Lock()

    def execute(self, slot, subindex, roi, result):
        print "Requesting roi: {}".format(roi)
        with self._lock:
            self.requested_rois.append( copy.copy(roi) )
        super( OpTrackedOutputProvider, self ).execute( slot, subindex, roi, result )
    
def testMinimalRequest():
    """
    Make sure that unneeded slices are not requested by the stacker.
    """
    graph = Graph()
    ops = []
    for op in range(10):
        data = numpy.random.random( (100,100) )
        data = vigra.taggedView( data, 'yx' )
        meta = MetaDict( { 'shape' : data.shape, 
                 'dtype' : data.dtype, 
                 'axistags' : data.axistags } )
        opData = OpTrackedOutputProvider( data, meta, graph=graph )
        ops.append( opData )
    
    opStacker = OpMultiArrayStacker(graph=graph)    
    opStacker.AxisFlag.setValue('z')
    opStacker.AxisIndex.setValue(0)
    opStacker.Images.resize( len(ops) )
    for islot, opData in zip( opStacker.Images, ops ):
        islot.connect( opData.Output )
    
    assert opStacker.Output.meta.getTaggedShape()['z'] == len(ops)
    
    stacked_data = opStacker.Output[3:5,:,:].wait()
    assert stacked_data.shape == (2, 100, 100)                      
    stacked_data = vigra.taggedView( stacked_data, 'zyx' )
    expected_data = numpy.concatenate( (ops[3]._data[numpy.newaxis, :], ops[4]._data[numpy.newaxis, :]) )
    expected_data = vigra.taggedView( expected_data, 'zyx' )
    assert (stacked_data == expected_data).all(), "Stacker returned the wrong data"
    for index, op in enumerate(ops):
        assert len(op.requested_rois) == 0 or index in range(3,5), "Stacker requested more data than it needed."

def testFullAllocate():

    nx = 5
    ny = 10
    nz = 2
    nc = 7
    stack = vigra.VigraArray((nx, ny, nz, nc), axistags=vigra.defaultAxistags('xyzc'))
    stack[...] = numpy.random.rand(nx, ny, nz, nc)

    g = Graph()

    #assume that the slicer works
    slicerX = OpMultiArraySlicer(graph=g)
    slicerX.inputs["Input"].setValue(stack)
    slicerX.inputs["AxisFlag"].setValue('x')

    #insert the x dimension
    stackerX = OpMultiArrayStacker(graph=g)
    stackerX.inputs["AxisFlag"].setValue('x')
    stackerX.inputs["AxisIndex"].setValue(0)
    stackerX.inputs["Images"].connect(slicerX.outputs["Slices"])

    newdata = stackerX.outputs["Output"][:].wait()
    assert_array_equal(newdata, stack.view(numpy.ndarray))

    print "1st part ok................."
    #merge stuff that already has an x dimension
    stack2 = vigra.VigraArray((nx-1, ny, nz, nc), axistags=vigra.defaultAxistags('xyzc'))
    stack2[...] = numpy.random.rand(nx-1, ny, nz, nc)

    opMulti = Op5ToMulti(graph=g)
    opMulti.inputs["Input0"].setValue(stack)
    opMulti.inputs["Input1"].setValue(stack2)

    #print "OPMULTI: ", len(opMulti.outputs["Outputs"])

    stackerX2 = OpMultiArrayStacker(graph=g)

    stackerX2.inputs["Images"].connect(opMulti.outputs["Outputs"])
    stackerX2.inputs["AxisFlag"].setValue('x')
    stackerX2.inputs["AxisIndex"].setValue(0)

    #print "STACKER: ", stackerX2.outputs["Output"].meta.shape

    newdata = stackerX2.outputs["Output"][:].wait()
    bothstacks = numpy.concatenate((stack, stack2), axis=0)
    assert_array_equal(newdata, bothstacks.view(numpy.ndarray))
    #print newdata.shape, bothstacks.shape

    print "2nd part ok................."
    #print "------------------------------------------------------------"
    #print "------------------------------------------------------------"
    #print "------------------------------------------------------------"
    ##### channel

    #assume that the slicer works
    slicerC = OpMultiArraySlicer(graph=g)
    slicerC.inputs["Input"].setValue(stack)
    slicerC.inputs["AxisFlag"].setValue('c')

    #insert the c dimension

    stackerC = OpMultiArrayStacker(graph=g)
    stackerC.inputs["AxisFlag"].setValue('c')
    stackerC.inputs["AxisIndex"].setValue(3)
    stackerC.inputs["Images"].connect(slicerC.outputs["Slices"])

    newdata = stackerC.outputs["Output"][:].wait()
    assert_array_equal(newdata, stack.view(numpy.ndarray))

    print "3rd part ok................."
    #print "STACKER: ", stackerC.outputs["Output"].meta.shape

    #merge stuff that already has an x dimension
    stack3 = vigra.VigraArray((nx, ny, nz, nc-1), axistags=vigra.defaultAxistags('xyzc'))
    stack3[...] = numpy.random.rand(nx, ny, nz, nc-1)

    opMulti = Op5ToMulti(graph=g)
    opMulti.inputs["Input0"].setValue(stack)
    opMulti.inputs["Input1"].setValue(stack3)

    stackerC2 = OpMultiArrayStacker(graph=g)
    stackerC2.inputs["AxisFlag"].setValue('c')
    stackerC2.inputs["AxisIndex"].setValue(3)
    stackerC2.inputs["Images"].connect(opMulti.outputs["Outputs"])

    newdata = stackerC2.outputs["Output"][:].wait()
    bothstacks = numpy.concatenate((stack, stack3), axis=3)
    assert_array_equal(newdata, bothstacks.view(numpy.ndarray))
    print "4th part ok................."


def testPartialAllocate():

    nx = 15
    ny = 20
    nz = 17
    nc = 7
    stack = vigra.VigraArray((nx, ny, nz, nc), axistags=vigra.defaultAxistags('xyzc'))
    stack[...] = numpy.random.rand(nx, ny, nz, nc)

    g = Graph()

    #assume that the slicer works
    slicerX = OpMultiArraySlicer(graph=g)
    slicerX.inputs["Input"].setValue(stack)
    slicerX.inputs["AxisFlag"].setValue('x')

    #insert the x dimension
    stackerX = OpMultiArrayStacker(graph=g)
    stackerX.inputs["AxisFlag"].setValue('x')
    stackerX.inputs["AxisIndex"].setValue(0)
    stackerX.inputs["Images"].connect(slicerX.outputs["Slices"])

    key = (slice(2, 3, None), slice(15, 18, None), slice(12, 15, None), slice(0, 7, None))
    newdata = stackerX.outputs["Output"][key].wait()
    substack = stack[key]
    print newdata.shape, substack.shape
    assert_array_equal(newdata, substack.view(numpy.ndarray))


if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)
    if not ret: sys.exit(1)
