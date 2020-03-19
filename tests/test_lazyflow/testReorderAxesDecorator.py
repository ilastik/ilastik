###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2018, the ilastik developers
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
#          http://ilastik.org/license/
###############################################################################
import logging
import os
import vigra
import tempfile

from lazyflow.graph import Graph, Operator, OperatorWrapper, InputSlot, OutputSlot
from lazyflow.stype import ArrayLike
from lazyflow.tools.schematic import generateSvgFileForOperator
from lazyflow.utility.timer import timeLogged

from lazyflow.utility import reorder_options, reorder


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

outer_order = "tczyx"
outer_shape = (1, 2, 3, 4, 5)
inner_order = "zyxct"
inner_shape = tuple([outer_shape[outer_order.find(x)] for x in inner_order])
test_args = ["arg0", 1, False]


class OpSum(Operator):
    InputA = InputSlot()
    InputB = InputSlot()

    Output = OutputSlot()

    def setupOutputs(self):
        assert self.InputA.meta.getAxisKeys() == list(inner_order)
        assert self.InputA.meta.shape == self.InputB.meta.shape, "Can't add images of different shapes!"
        self.Output.meta.assignFrom(self.InputA.meta)

    def execute(self, slot, subindex, roi, result):
        a = self.InputA.get(roi).wait()
        b = self.InputB.get(roi).wait()
        result[...] = a + b
        return result

    def propagateDirty(self, slot, subindex, roi):
        self.Output.setDirty(roi)


@reorder
@reorder_options(inner_order, [], outer_order)
class LazyOp(Operator):
    """ test op """

    name = "LazyOp"

    in_a = InputSlot(stype=ArrayLike)
    in_b = InputSlot(stype=ArrayLike)

    out_a = OutputSlot(stype=ArrayLike)
    out_b = OutputSlot(stype=ArrayLike)

    def __init__(self, inner_order, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.inner_order = inner_order
        self.opSum = OpSum(parent=self)

    def meth(self, *args):
        assert isinstance(self, LazyOp)
        assert len(args) == len(test_args)
        for test, got in zip(test_args, args):
            assert test == got

    @classmethod
    def class_meth(cls, *args):
        assert isinstance(cls, type)
        assert len(args) == len(test_args), (args, test_args)
        for test, got in zip(test_args, args):
            assert test == got

    @staticmethod
    def static_meth(*args):
        assert len(args) == len(test_args)
        for test, got in zip(test_args, args):
            assert test == got

    @property
    def property_meth(self):
        assert isinstance(self, LazyOp)

    def except_meth(self, *args):
        assert isinstance(self, LazyOp)
        assert len(args) == len(test_args)
        for test, got in zip(test_args, args):
            assert test == got

    def setupOutputs(self):
        # out_a pass-through of in_a
        self.out_a.connect(self.in_a)

        # out_b, sum of in_a and in_b
        self.opSum.InputA.connect(self.in_a)
        self.opSum.InputB.connect(self.in_b)
        self.out_b.connect(self.opSum.Output)

    def propagateDirty(self, slot, subindex, roi):
        self.out_b.setDirty(roi)
        if slot == self.in_a:
            self.out_a.setDirty(roi)


# embed tests in trivial parent operator
class OpParent(Operator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lazyOp1 = LazyOp(inner_order=inner_order, parent=self)
        self.lazyOp2 = LazyOp(inner_order="txyzc", parent=self)

    def setupOutputs(self):
        tags = vigra.defaultAxistags(outer_order)
        a = vigra.VigraArray(outer_shape, value=1, axistags=tags)
        b = vigra.VigraArray(outer_shape, value=2, axistags=tags)
        self.lazyOp1.in_a.setValue(a)
        self.lazyOp1.in_b.setValue(b)

        self.lazyOp1.setupOutputs()
        self.lazyOp2.setupOutputs()

        self.lazyOp2.in_a.connect(self.lazyOp1.out_a)
        self.lazyOp2.in_b.connect(self.lazyOp1.out_b)


class TestReorderAxesDecorator:
    dir = tempfile.mkdtemp()
    # dir = os.path.expanduser('~/Desktop/tmp')  # uncommmet for easier debugging

    svg_dir = tempfile.mkdtemp()

    @classmethod
    def setup_class(cls):
        tags = vigra.defaultAxistags(outer_order)
        cls.a = vigra.VigraArray(outer_shape, value=1, axistags=tags)
        cls.b = vigra.VigraArray(outer_shape, value=2, axistags=tags)

    @classmethod
    def teardown_class(cls):
        pass

    @timeLogged(logger)
    def test_svg_creation_simple(self):
        lazyOp = LazyOp(graph=Graph(), inner_order=inner_order)
        lazyOp.setupOutputs()
        generateSvgFileForOperator(os.path.join(self.svg_dir, "lazyOp.svg"), lazyOp, 5)

    @timeLogged(logger)
    def test_svg_creation_with_parent(self):
        opParent = OpParent(graph=Graph())
        opParent.setupOutputs()
        generateSvgFileForOperator(os.path.join(self.svg_dir, "opParent.svg"), opParent, 5)

    @timeLogged(logger)
    def test_svg_creation_wrapped(self):
        opParent = OpParent(graph=Graph())
        lazyWrap = OperatorWrapper(
            LazyOp,
            broadcastingSlotNames=["in_a", "in_b"],
            operator_kwargs={"inner_order": inner_order},
            parent=opParent,
        )
        lazyWrap.out_a.resize(2)

        lazyWrap.in_a.setValue(self.a)
        lazyWrap.in_b.setValue(self.b)

        assert lazyWrap.out_a[0][:].wait().shape == outer_shape
        assert lazyWrap.out_b[0][:].wait().shape == outer_shape
        assert lazyWrap.out_a[1][:].wait().shape == outer_shape
        assert lazyWrap.out_b[1][:].wait().shape == outer_shape

        generateSvgFileForOperator(os.path.join(self.svg_dir, "lazyWrap.svg"), lazyWrap, 5)

    @timeLogged(logger)
    def test_reorderd_ops_in_parent_op(self):
        opParent = OpParent(graph=Graph())
        opParent.setupOutputs()
        # check that method types are treated correctly (actual tests in LazyOp)
        opParent.lazyOp1.meth(*test_args)
        opParent.lazyOp1.class_meth(*test_args)
        opParent.lazyOp1.static_meth(*test_args)
        opParent.lazyOp1.property_meth
        opParent.lazyOp1.except_meth(*test_args)

        # when accessing the child's operators they should conform with the outside order. Here, the shape of the
        # resulting numpy.ndarray is tested to make sure we are not just checking meta data.
        assert opParent.lazyOp1.out_a[:].wait().shape == outer_shape
        assert opParent.lazyOp1.out_b[:].wait().shape == outer_shape

        tags = vigra.defaultAxistags(outer_order)
        expect = vigra.VigraArray(outer_shape, value=3, axistags=tags)

        assert (expect == opParent.lazyOp1.out_b[:].wait()).all()
        assert expect.axistags == opParent.lazyOp1.out_b.meta.axistags
        assert expect.shape == opParent.lazyOp1.out_b.meta.shape

        assert opParent.lazyOp2.in_a[:].wait().shape == outer_shape
        assert opParent.lazyOp2.in_b[:].wait().shape == outer_shape
        assert opParent.lazyOp2.out_a[:].wait().shape == outer_shape
        assert opParent.lazyOp2.out_b[:].wait().shape == outer_shape

        tags = vigra.defaultAxistags(outer_order)
        expect = vigra.VigraArray(outer_shape, value=4, axistags=tags)
        assert (expect == opParent.lazyOp2.out_b[:].wait()).all()
        assert expect.axistags == opParent.lazyOp2.out_b.meta.axistags
        assert expect.shape == opParent.lazyOp2.out_b.meta.shape

        # checking inner shapes by pretending to make inner calls
        opParent.lazyOp2._inner_call = True
        assert opParent.lazyOp2.in_a[:].wait().shape == inner_shape
        assert opParent.lazyOp2.in_b[:].wait().shape == inner_shape
        assert opParent.lazyOp2.out_a[:].wait().shape == inner_shape
        assert opParent.lazyOp2.out_b[:].wait().shape == inner_shape


if __name__ == "__main__":
    import nose
    import sys

    # make the program quit on Ctrl+C
    import signal

    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nocapture")
    # Don't set the logging level to DEBUG.  Leave it alone.
    sys.argv.append("--nologcapture")
    nose.run(defaultTest=__file__)
