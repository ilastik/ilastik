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
# 		   http://ilastik.org/license/
###############################################################################
import copy
import vigra
import numpy
import threading
from lazyflow.graph import Graph, Operator, InputSlot, OutputSlot, OperatorWrapper, MetaDict
from lazyflow import operators
from lazyflow.operators import *
from lazyflow.roi import roiToSlice, sliceToRoi

from lazyflow.operators.valueProviders import OpOutputProvider

from numpy.testing import assert_array_equal

import unittest

import signal

signal.signal(signal.SIGINT, signal.SIG_DFL)


class OpMultiArraySlicer_REDUCE_DIM(Operator):
    """
    Produces a list of image slices along the given axis.
    Same as the slicer operator below, but reduces the dimensionality of the data.
    The sliced axis is discarded in the output image shape.
    """

    Input = InputSlot()
    AxisFlag = InputSlot()
    Slices = OutputSlot(level=1)

    name = "Multi Array Slicer"
    category = "Misc"

    def setupOutputs(self):
        flag = self.inputs["AxisFlag"].value

        indexAxis = self.inputs["Input"].meta.axistags.index(flag)
        outshape = list(self.inputs["Input"].meta.shape)
        n = outshape.pop(indexAxis)
        outshape = tuple(outshape)

        if self.Input.meta.ideal_blockshape:
            ideal_blockshape = list(self.Input.meta.ideal_blockshape)
            ideal_blockshape.pop(indexAxis)
            ideal_blockshape = tuple(ideal_blockshape)

        if self.Input.meta.max_blockshape:
            max_blockshape = list(self.Input.meta.max_blockshape)
            max_blockshape.pop(indexAxis)
            max_blockshape = tuple(max_blockshape)

        outaxistags = copy.copy(self.inputs["Input"].meta.axistags)
        del outaxistags[flag]

        self.outputs["Slices"].resize(n)

        for o in self.outputs["Slices"]:
            # Output metadata is a modified copy of the input's metadata
            o.meta.assignFrom(self.Input.meta)
            o.meta.axistags = outaxistags
            o.meta.shape = outshape
            if self.Input.meta.drange is not None:
                o.meta.drange = self.Input.meta.drange

            if self.Input.meta.ideal_blockshape:
                o.meta.ideal_blockshape = ideal_blockshape

            if self.Input.meta.max_blockshape:
                o.meta.max_blockshape = max_blockshape

    def execute(self, slot, subindex, rroi, result):
        key = roiToSlice(rroi.start, rroi.stop)
        index = subindex[0]
        # print "SLICER: key", key, "indexes[0]", indexes[0], "result", result.shape
        start, stop = sliceToRoi(key, self.outputs["Slices"][index].meta.shape)

        start = list(start)
        stop = list(stop)

        flag = self.inputs["AxisFlag"].value
        indexAxis = self.inputs["Input"].meta.axistags.index(flag)

        start.insert(indexAxis, index)
        stop.insert(indexAxis, index + 1)

        newKey = roiToSlice(numpy.array(start), numpy.array(stop))

        ttt = self.inputs["Input"][newKey].wait()

        writeKey = [slice(None, None, None) for k in key]
        writeKey.insert(indexAxis, 0)
        writeKey = tuple(writeKey)

        return ttt[writeKey]  # + (0,)]

    def propagateDirty(self, slot, subindex, roi):
        if slot == self.AxisFlag:
            for i, s in enumerate(self.Slices):
                s.setDirty(slice(None))
        elif slot == self.Input:
            key = roi.toSlice()
            reducedKey = list(key)
            inputTags = self.Input.meta.axistags
            flag = self.AxisFlag.value
            axisSlice = reducedKey.pop(inputTags.index(flag))

            axisStart, axisStop = axisSlice.start, axisSlice.stop
            if axisStart is None:
                axisStart = 0
            if axisStop is None:
                axisStop = len(self.Slices)

            for i in range(axisStart, axisStop):
                self.Slices[i].setDirty(reducedKey)
        else:
            assert False, "Unknown dirty input slot"


class OpTrackedOutputProvider(OpOutputProvider):
    """
    Simply provides access to an array, but records the requests it processes.
    """

    def __init__(self, *args, **kwargs):
        super(OpTrackedOutputProvider, self).__init__(*args, **kwargs)
        self.requested_rois = []
        self._lock = threading.Lock()

    def execute(self, slot, subindex, roi, result):
        print("Requesting roi: {}".format(roi))
        with self._lock:
            self.requested_rois.append(copy.copy(roi))
        super(OpTrackedOutputProvider, self).execute(slot, subindex, roi, result)


def testMinimalRequest():
    """
    Make sure that unneeded slices are not requested by the stacker.
    """
    graph = Graph()
    ops = []
    for op in range(10):
        data = numpy.random.random((100, 100))
        data = vigra.taggedView(data, "yx")
        meta = MetaDict({"shape": data.shape, "dtype": data.dtype, "axistags": data.axistags})
        opData = OpTrackedOutputProvider(data, meta, graph=graph)
        ops.append(opData)

    opStacker = OpMultiArrayStacker(graph=graph)
    opStacker.AxisFlag.setValue("z")
    opStacker.AxisIndex.setValue(0)
    opStacker.Images.resize(len(ops))
    for islot, opData in zip(opStacker.Images, ops):
        islot.connect(opData.Output)

    assert opStacker.Output.meta.getTaggedShape()["z"] == len(ops)

    stacked_data = opStacker.Output[3:5, :, :].wait()
    assert stacked_data.shape == (2, 100, 100)
    stacked_data = vigra.taggedView(stacked_data, "zyx")
    expected_data = numpy.concatenate((ops[3]._data[numpy.newaxis, :], ops[4]._data[numpy.newaxis, :]))
    expected_data = vigra.taggedView(expected_data, "zyx")
    assert (stacked_data == expected_data).all(), "Stacker returned the wrong data"
    for index, op in enumerate(ops):
        assert len(op.requested_rois) == 0 or index in range(3, 5), "Stacker requested more data than it needed."


def testFullAllocate():

    nx = 5
    ny = 10
    nz = 2
    nc = 7
    stack = vigra.VigraArray((nx, ny, nz, nc), axistags=vigra.defaultAxistags("xyzc"))
    stack[...] = numpy.random.rand(nx, ny, nz, nc)

    g = Graph()

    # assume that the slicer works
    slicerX = OpMultiArraySlicer_REDUCE_DIM(graph=g)
    slicerX.inputs["Input"].setValue(stack)
    slicerX.inputs["AxisFlag"].setValue("x")

    # insert the x dimension
    stackerX = OpMultiArrayStacker(graph=g)
    stackerX.inputs["AxisFlag"].setValue("x")
    stackerX.inputs["AxisIndex"].setValue(0)
    stackerX.inputs["Images"].connect(slicerX.outputs["Slices"])

    newdata = stackerX.outputs["Output"][:].wait()
    assert_array_equal(newdata, stack.view(numpy.ndarray))

    print("1st part ok.................")
    # merge stuff that already has an x dimension
    stack2 = vigra.VigraArray((nx - 1, ny, nz, nc), axistags=vigra.defaultAxistags("xyzc"))
    stack2[...] = numpy.random.rand(nx - 1, ny, nz, nc)

    stackerX2 = OpMultiArrayStacker(graph=g)

    stackerX2.Images.resize(2)

    ap1 = operators.OpArrayPiper(graph=g)
    ap2 = operators.OpArrayPiper(graph=g)
    ap1.Input.setValue(stack)
    ap2.Input.setValue(stack2)
    stackerX2.Images[0].connect(ap1.Output)
    stackerX2.Images[1].connect(ap2.Output)

    stackerX2.inputs["AxisFlag"].setValue("x")
    stackerX2.inputs["AxisIndex"].setValue(0)

    # print "STACKER: ", stackerX2.outputs["Output"].meta.shape

    newdata = stackerX2.outputs["Output"][:].wait()
    bothstacks = numpy.concatenate((stack, stack2), axis=0)
    assert_array_equal(newdata, bothstacks.view(numpy.ndarray))
    # print newdata.shape, bothstacks.shape

    print("2nd part ok.................")
    # print "------------------------------------------------------------"
    # print "------------------------------------------------------------"
    # print "------------------------------------------------------------"
    ##### channel

    # assume that the slicer works
    slicerC = OpMultiArraySlicer_REDUCE_DIM(graph=g)
    slicerC.inputs["Input"].setValue(stack)
    slicerC.inputs["AxisFlag"].setValue("c")

    # insert the c dimension

    stackerC = OpMultiArrayStacker(graph=g)
    stackerC.inputs["AxisFlag"].setValue("c")
    stackerC.inputs["AxisIndex"].setValue(3)
    stackerC.inputs["Images"].connect(slicerC.outputs["Slices"])

    newdata = stackerC.outputs["Output"][:].wait()
    assert_array_equal(newdata, stack.view(numpy.ndarray))

    print("3rd part ok.................")
    # print "STACKER: ", stackerC.outputs["Output"].meta.shape

    # merge stuff that already has an x dimension
    stack3 = vigra.VigraArray((nx, ny, nz, nc - 1), axistags=vigra.defaultAxistags("xyzc"))
    stack3[...] = numpy.random.rand(nx, ny, nz, nc - 1)

    ap3 = operators.OpArrayPiper(graph=g)
    ap3.Input.setValue(stack3)

    stackerC2 = OpMultiArrayStacker(graph=g)
    stackerC2.inputs["AxisFlag"].setValue("c")
    stackerC2.inputs["AxisIndex"].setValue(3)
    stackerC2.Images.resize(2)
    stackerC2.Images[0].connect(ap1.Output)
    stackerC2.Images[1].connect(ap3.Output)

    newdata = stackerC2.outputs["Output"][:].wait()
    bothstacks = numpy.concatenate((stack, stack3), axis=3)
    assert_array_equal(newdata, bothstacks.view(numpy.ndarray))
    print("4th part ok.................")


def testPartialAllocate():

    nx = 15
    ny = 20
    nz = 17
    nc = 7
    stack = vigra.VigraArray((nx, ny, nz, nc), axistags=vigra.defaultAxistags("xyzc"))
    stack[...] = numpy.random.rand(nx, ny, nz, nc)

    g = Graph()

    # assume that the slicer works
    slicerX = OpMultiArraySlicer_REDUCE_DIM(graph=g)
    slicerX.inputs["Input"].setValue(stack)
    slicerX.inputs["AxisFlag"].setValue("x")

    # insert the x dimension
    stackerX = OpMultiArrayStacker(graph=g)
    stackerX.inputs["AxisFlag"].setValue("x")
    stackerX.inputs["AxisIndex"].setValue(0)
    stackerX.inputs["Images"].connect(slicerX.outputs["Slices"])

    key = (slice(2, 3, None), slice(15, 18, None), slice(12, 15, None), slice(0, 7, None))
    newdata = stackerX.outputs["Output"][key].wait()
    substack = stack[key]
    print(newdata.shape, substack.shape)
    assert_array_equal(newdata, substack.view(numpy.ndarray))


class TestAxisIndex(unittest.TestCase):
    def setup_method(self, method):
        vol = numpy.random.randint(0, 256, size=(100, 200, 300, 2))
        vol = vol.astype(numpy.uint8)
        vol = vigra.taggedView(vol, "xyzc")
        self.vol = vol
        self.nc = vol.shape[-1]

    def testAxisIndex(self):
        pipers = []
        g = Graph()
        op = OpMultiArrayStacker(graph=g)
        op.AxisFlag.setValue("c")
        op.AxisIndex.setValue(0)
        op.Images.resize(self.nc)

        for i in range(self.nc):
            piper = OpArrayPiper(graph=g)
            piper.Input.setValue(self.vol[..., i])
            op.Images[i].connect(piper.Output)
            pipers.append(piper)

        out = op.Output[...].wait()
        out = vigra.taggedView(out, axistags="cxyz").withAxes(*"xyzc")
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
    def setup_method(self, method):
        self.g = Graph()
        vol = numpy.zeros((100, 200, 2))
        vol = vigra.taggedView(vol, axistags="xyz")
        self.vol = vol

    def testSimpleUsage(self):
        n = self.vol.shape[2]
        op = OpMultiArrayStacker(graph=self.g)
        op.AxisFlag.setValue("z")

        provider = OperatorWrapper(OpArrayPiper, graph=self.g)
        vol = self.vol

        op.Images.connect(provider.Output)
        provider.Input.resize(n)

        for i in range(n):
            provider.Input[i].setValue(vol[..., i])

        out = op.Output[...].wait()
        out = vigra.taggedView(out, axistags="xyz")
        numpy.testing.assert_array_equal(out, vol)

    def testIndexing(self):
        n = self.vol.shape[2]
        op = OpMultiArrayStacker(graph=self.g)
        op.AxisFlag.setValue("z")
        op.AxisIndex.setValue(0)

        provider = OperatorWrapper(OpArrayPiper, graph=self.g)
        vol = self.vol

        op.Images.connect(provider.Output)
        provider.Input.resize(n)

        for i in range(n):
            provider.Input[i].setValue(vol[..., i])

        out = op.Output[...].wait()
        out = vigra.taggedView(out, axistags="zxy")
        out = out.withAxes(*"xyz")
        numpy.testing.assert_array_equal(out, vol)

    ## slots could become unready after a while, the old implementation used to
    ## ignore this
    def testNonReady(self):
        n = self.vol.shape[2]
        op = OpMultiArrayStacker(graph=self.g)
        op.AxisFlag.setValue("z")
        op.AxisIndex.setValue(0)

        providers = [OpNonReady(graph=self.g), OpNonReady(graph=self.g)]
        provider = OperatorWrapper(OpArrayPiper, graph=self.g)
        provider.Input.resize(n)
        vol = self.vol

        op.Images.resize(n)

        for i in range(n):
            provider.Input[i].setValue(vol[..., i])
            providers[i].Input.connect(provider.Output[i])
            op.Images[i].connect(providers[i].Output)

        req = op.Output[...]
        req.notify_failed(lambda *args: None)  # Replace the default handler: dont' show a traceback
        out = req.wait()

        with self.assertRaises(InputSlot.SlotNotReadyError):
            providers[0].screwWithOutput()
            req = op.Output[...]
            req.notify_failed(lambda *args: None)  # Replace the default handler: dont' show a traceback
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

    sys.argv.append("--nocapture")  # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture")  # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)
    if not ret:
        sys.exit(1)
