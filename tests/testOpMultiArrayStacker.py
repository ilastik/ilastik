from __future__ import print_function
from builtins import zip
from builtins import range
###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the Lesser GNU General Public License
# as published by the Free Software Foundation; either version 2.1
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# See the files LICENSE.lgpl2 and LICENSE.lgpl3 for full text of the
# GNU Lesser General Public License version 2.1 and 3 respectively.
# This information is also available on the ilastik web site at:
#		   http://ilastik.org/license/
###############################################################################
import copy
import vigra
import numpy
import threading
from lazyflow.graph import Graph, Operator, InputSlot, OutputSlot, OperatorWrapper, MetaDict
from lazyflow import operators
from lazyflow.operators import *

from lazyflow.operators.valueProviders import OpOutputProvider

from numpy.testing import *

import unittest

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
        print("Requesting roi: {}".format(roi))
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

    print("1st part ok.................")
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

    print("2nd part ok.................")
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

    print("3rd part ok.................")
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
    print("4th part ok.................")


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
    print(newdata.shape, substack.shape)
    assert_array_equal(newdata, substack.view(numpy.ndarray))


class TestAxisIndex(unittest.TestCase):
    def setUp(self):
        vol = numpy.random.randint(0, 256, size=(100, 200, 300, 2))
        vol = vol.astype(numpy.uint8)
        vol = vigra.taggedView(vol, 'xyzc')
        self.vol = vol
        self.nc = vol.shape[-1]

    def testAxisIndex(self):
        pipers = []
        g = Graph()
        op = OpMultiArrayStacker(graph=g)
        op.AxisFlag.setValue('c')
        op.AxisIndex.setValue(0)
        op.Images.resize(self.nc)
        
        for i in range(self.nc):
            piper = OpArrayPiper(graph=g)
            piper.Input.setValue(self.vol[..., i])
            op.Images[i].connect(piper.Output)
            pipers.append(piper)
        
        out = op.Output[...].wait()
        out = vigra.taggedView(out, axistags='cxyz').withAxes(*'xyzc')
        assert_array_equal(out, self.vol)

        class OpCheckRoi(Operator):
            Input = InputSlot()
            def propagateDirty(self, slot, subindex, roi):
                print("also here")
                print(roi.stop)
                print(self.Input.meta.shape)
                assert len(roi.stop) == len(self.Input.meta.shape)
                for x, y in zip(roi.stop, self.Input.meta.shape):
                    assert x <= y, "{} > {}".format(x, y)

        check = OpCheckRoi(graph=g)
        check.Input.connect(op.Output)
        op.Images[0].setDirty(slice(None))


class TestOpMultiArrayStacker(unittest.TestCase):

    def setUp(self):
        self.g = Graph()
        vol = numpy.zeros((100,200,2))
        vol = vigra.taggedView(vol, axistags='xyz')
        self.vol = vol

    def testSimpleUsage(self):
        n = self.vol.shape[2]
        op = OpMultiArrayStacker(graph=self.g)
        op.AxisFlag.setValue('z')

        provider = OperatorWrapper(OpArrayPiper, graph=self.g)
        vol = self.vol

        op.Images.connect(provider.Output)
        provider.Input.resize(n)

        for i in range(n):
            provider.Input[i].setValue(vol[..., i])

        out = op.Output[...].wait()
        out = vigra.taggedView(out, axistags='xyz')
        numpy.testing.assert_array_equal(out, vol)

    def testIndexing(self):
        n = self.vol.shape[2]
        op = OpMultiArrayStacker(graph=self.g)
        op.AxisFlag.setValue('z')
        op.AxisIndex.setValue(0)

        provider = OperatorWrapper(OpArrayPiper, graph=self.g)
        vol = self.vol

        op.Images.connect(provider.Output)
        provider.Input.resize(n)

        for i in range(n):
            provider.Input[i].setValue(vol[..., i])

        out = op.Output[...].wait()
        out = vigra.taggedView(out, axistags='zxy')
        out = out.withAxes(*"xyz")
        numpy.testing.assert_array_equal(out, vol)


    ## slots could become unready after a while, the old implementation used to
    ## ignore this
    def testNonReady(self):
        n = self.vol.shape[2]
        op = OpMultiArrayStacker(graph=self.g)
        op.AxisFlag.setValue('z')
        op.AxisIndex.setValue(0)

        providers = [OpNonReady(graph=self.g),OpNonReady(graph=self.g)]
        provider = OperatorWrapper(OpArrayPiper, graph=self.g)
        provider.Input.resize(n)
        vol = self.vol

        op.Images.resize(n)

        for i in range(n):
            provider.Input[i].setValue(vol[..., i])
            providers[i].Input.connect(provider.Output[i])
            op.Images[i].connect(providers[i].Output)

        req = op.Output[...]
        req.notify_failed( lambda *args: None ) # Replace the default handler: dont' show a traceback
        out = req.wait()


        with self.assertRaises(InputSlot.SlotNotReadyError):
            providers[0].screwWithOutput()
            req = op.Output[...]
            req.notify_failed( lambda *args: None ) # Replace the default handler: dont' show a traceback
            out = req.wait()


class OpNonReady(Operator):
    Input = InputSlot()
    Output = OutputSlot()

    def setupOutputs(self):
        self.Output.meta.assignFrom(self.Input.meta)

    def execute(self, slot, subindex, roi, result):
        assert self.Output.ready()
        result[:] = 0

    def propagateDirty(self, slot, subindex, roi):
        newroi = roi.copy()
        self.Output.setDirty(roi)

    def screwWithOutput(self):
        self.Input.disconnect()
        self.Output.meta.NOTREADY = True



if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)
    if not ret: sys.exit(1)
