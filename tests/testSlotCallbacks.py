from builtins import object

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
import nose
from lazyflow.graph import Graph, Operator, InputSlot, OutputSlot
from lazyflow import stype
from lazyflow import operators
import numpy


class OpS(Operator):
    name = "OpA"

    Output1 = OutputSlot()
    Output2 = OutputSlot()
    Output3 = OutputSlot()
    Output4 = OutputSlot(level=1)

    def __init__(self, parent=None, graph=None):
        Operator.__init__(self, parent, graph)

    def setupOutputs(self):
        self._configured = True
        self.Output1.meta.shape = (1,)
        self.Output1.meta.dtype = numpy.float32
        self.Output2.meta.shape = (2,)
        self.Output2.meta.dtype = numpy.uint8
        self.Output3.meta.shape = (3,)
        self.Output3.meta.dtype = numpy.uint32

    def execute(self, slot, subindex, roi, result):
        pass


class OpA(Operator):
    name = "OpA"

    Input1 = InputSlot()  # required slot
    Input2 = InputSlot(optional=True)  # optional slot
    Input3 = InputSlot(value=3)  # required slot with default value, i.e. already connected
    Input4 = InputSlot(level=1)

    Output1 = OutputSlot()
    Output2 = OutputSlot()
    Output3 = OutputSlot()
    Output4 = OutputSlot(level=1)

    def __init__(self, parent=None, graph=None):
        Operator.__init__(self, parent=parent, graph=graph)
        self._configured = False

    def setupOutputs(self):
        self._configured = True
        self.Output1.meta.shape = self.Input1.meta.shape
        self.Output1.meta.dtype = self.Input1.meta.dtype
        self.Output2.meta.shape = self.Input2.meta.shape
        self.Output2.meta.dtype = self.Input2.meta.dtype
        self.Output3.meta.shape = self.Input3.meta.shape
        self.Output3.meta.dtype = self.Input3.meta.dtype
        self.Output4.meta.shape = self.Input4.meta.shape
        self.Output4.meta.dtype = self.Input4.meta.dtype

    def execute(self, slot, subindex, roi, result):
        pass

    def propagateDirty(self, inputSlot, subindex, roi):
        pass


class TestSlot_notifyConnect(object):
    def setup_method(self, method):
        self.g = Graph()

    def test_connect(self):
        # test that the notifyConnect callback is called
        # when the slot is connected
        ops = OpS(graph=self.g)
        opa = OpA(graph=self.g)
        opa.Input2.connect(ops.Output2)

        upval = [False]

        def callBack(slot):
            upval[0] = True

        # check the connect callback is called
        opa.Input1._notifyConnect(callBack)
        opa.Input1.connect(ops.Output1)
        assert upval[0] == True

        # check the connect callback is called for a slot with default value
        upval[0] = False
        opa.Input3._notifyConnect(callBack)
        opa.Input3.connect(ops.Output3)
        assert upval[0] == True

        # check the connect callback is called for a multi inputslot
        upval[0] = False
        opa.Input4._notifyConnect(callBack)
        opa.Input4.connect(ops.Output4)
        assert upval[0] == True

    def test_no_connect(self):
        ops = OpS(graph=self.g)
        opa = OpA(graph=self.g)

        upval = [False]

        def callBack(slot):
            upval[0] = True

        opa.Input1._notifyConnect(callBack)

        # check the connect callback is not called when reconnecting to the same slot
        opa.Input1.connect(ops.Output1)
        upval[0] = False
        opa.Input1.connect(ops.Output1)
        assert upval[0] == False

        # check the connect callback is not called when setting the same value again
        opa.Input1.disconnect()
        opa.Input1.setValue(10)
        upval[0] = False
        opa.Input1.setValue(10)
        assert upval[0] == False

    def test_unregister_connect(self):
        # check that unregistering a connect callback works
        ops = OpS(graph=self.g)
        opa = OpA(graph=self.g)

        upval = [False]

        def callBack(slot):
            upval[0] = True

        opa.Input1._notifyConnect(callBack)
        opa.Input1._unregisterConnect(callBack)

        opa.Input1.connect(ops.Output1)
        assert upval[0] == False


class TestSlot_notifyDisconnect(object):
    def setup_method(self, method):
        self.g = Graph()

    def test_disconnect(self):
        # test that the notifyConnect callback is called
        # when the slot is connected
        ops = OpS(graph=self.g)
        opa = OpA(graph=self.g)

        upval = [False]

        def callBack(slot):
            upval[0] = True

        # check the disconnect callback is called upon disconnect
        opa.Input1.connect(ops.Output1)
        opa.Input1.notifyDisconnect(callBack)
        opa.Input1.disconnect()
        assert upval[0] == True

        # check the disconnect callback is called upon reconnect
        opa.Input1.connect(ops.Output1)
        upval[0] = False
        opa.Input1.connect(ops.Output2)
        assert upval[0] == True

        # check the disconnect callback is called upon setValue when being already connected
        opa.Input1.connect(ops.Output1)
        upval[0] = False
        opa.Input1.disconnect()
        opa.Input1.setValue(19)
        assert upval[0] == True

    def test_no_disconnect(self):
        ops = OpS(graph=self.g)
        opa = OpA(graph=self.g)

        upval = [False]

        def callBack(slot):
            upval[0] = True

        opa.Input1.notifyDisconnect(callBack)

        # check the disconnect callback is not called when reconnecting to the same slot
        opa.Input1.connect(ops.Output1)
        upval[0] = False
        opa.Input1.connect(ops.Output1)
        assert upval[0] == False

        # check the disconnect callback is not called when setting the same value again
        opa.Input1.disconnect()
        opa.Input1.setValue(10)
        upval[0] = False
        opa.Input1.setValue(10)
        assert upval[0] == False

    def test_unregister_disconnect(self):
        # check that unregistering a disconnect callback works
        ops = OpS(graph=self.g)
        opa = OpA(graph=self.g)

        upval = [False]

        def callBack(slot):
            upval[0] = True

        opa.Input1.connect(ops.Output1)

        opa.Input1.notifyDisconnect(callBack)
        opa.Input1.unregisterDisconnect(callBack)

        opa.Input1.disconnect()

        assert upval[0] == False


class TestSlot_notifyMetaChanged(object):
    def setup_method(self, method):
        self.g = Graph()

    def test_inputslot_changed(self):
        # test that the changed callback is called
        # when the slot meta information changes
        ops = OpS(graph=self.g)
        opa = OpA(graph=self.g)

        upval = [False]

        def callBack(slot):
            upval[0] = True

        # test normal InputSlot
        opa.Input1.notifyMetaChanged(callBack)
        opa.Input1.connect(ops.Output1)
        assert upval[0] == True

        upval[0] = False
        opa.Input1.connect(ops.Output2)
        assert upval[0] == True

        # test InputSlot with default value
        upval[0] = False
        opa.Input3.notifyMetaChanged(callBack)
        opa.Input3.connect(ops.Output1)
        assert upval[0] == True

        upval[0] = False


if __name__ == "__main__":
    import sys
    import nose

    sys.argv.append("--nocapture")  # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture")  # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)
    if not ret:
        sys.exit(1)
