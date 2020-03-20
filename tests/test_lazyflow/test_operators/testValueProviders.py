from builtins import range
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
import time
import random
import threading
from functools import partial
import numpy
import vigra
import lazyflow.graph
from lazyflow.operators import OpBlockedArrayCache
from lazyflow.operators.valueProviders import (
    OpMetadataInjector,
    OpOutputProvider,
    OpMetadataSelector,
    OpValueCache,
    OpMetadataMerge,
    OpZeroDefault,
)


class TestOpMetadataInjector(object):
    def test(self):
        g = lazyflow.graph.Graph()
        op = OpMetadataInjector(graph=g)

        additionalMetadata = {"layertype": 7}
        op.Metadata.setValue(additionalMetadata)
        op.Input.setValue("Hello")

        # Output value should match input value
        assert op.Output.value == op.Input.value

        # Make sure all input metadata was copied to the output
        assert all(((k, v) in list(op.Output.meta.items())) for k, v in list(op.Input.meta.items()))

        # Check that the additional metadata was added to the output
        assert op.Output.meta.layertype == 7

        # Make sure dirtyness gets propagated to the output.
        dirtyList = []

        def handleDirty(*args):
            dirtyList.append(True)

        op.Output.notifyDirty(handleDirty)
        op.Input.setValue(8)
        assert len(dirtyList) == 1


class TestOpOutputProvider(object):
    def test(self):
        from lazyflow.graph import Graph, MetaDict

        g = Graph()

        # Create some data to give
        shape = (1, 2, 3, 4, 5)
        data = numpy.indices(shape, dtype=int).sum(0)
        meta = MetaDict()
        meta.axistags = vigra.defaultAxistags("xtycz")
        meta.shape = shape
        meta.dtype = int

        opProvider = OpOutputProvider(data, meta, graph=g)
        assert (opProvider.Output[0:1, 1:2, 0:3, 2:4, 3:5].wait() == data[0:1, 1:2, 0:3, 2:4, 3:5]).all()
        for k, v in list(meta.items()):
            if k != "_ready" and k != "_dirty":
                assert opProvider.Output.meta[k] == v


class TestOpMetadataSelector(object):
    def test(self):
        from lazyflow.graph import Graph, MetaDict

        g = Graph()

        # Create some data to give
        shape = (1, 2, 3, 4, 5)
        data = numpy.indices(shape, dtype=int).sum(0)
        meta = MetaDict()
        meta.axistags = vigra.defaultAxistags("xtycz")
        meta.shape = shape
        meta.dtype = int

        opProvider = OpOutputProvider(data, meta, graph=g)

        op = OpMetadataSelector(graph=g)
        op.Input.connect(opProvider.Output)

        op.MetadataKey.setValue("shape")
        assert op.Output.value == shape

        op.MetadataKey.setValue("axistags")
        assert op.Output.value == meta.axistags


class TestOpMetadataMerge(object):
    def test(self):
        from lazyflow.graph import Graph, MetaDict
        from lazyflow.operators import OpArrayPiper

        graph = Graph()
        opDataSource = OpArrayPiper(graph=graph)
        opDataSource.Input.setValue(numpy.ndarray((9, 10), dtype=numpy.uint8))

        # Create some metadata
        shape = (1, 2, 3, 4, 5)
        data = numpy.indices(shape, dtype=int).sum(0)
        meta = MetaDict()
        meta.specialdata = "Salutations"
        meta.notsospecial = "Hey"

        opProvider = OpOutputProvider(data, meta, graph=graph)

        op = OpMetadataMerge(graph=graph)
        op.Input.connect(opDataSource.Output)
        op.MetadataSource.connect(opProvider.Output)
        op.FieldsToClone.setValue(["specialdata"])

        assert op.Output.ready()
        assert op.Output.meta.shape == opDataSource.Output.meta.shape
        assert op.Output.meta.dtype == opDataSource.Output.meta.dtype
        assert op.Output.meta.specialdata == meta.specialdata
        assert op.Output.meta.notsospecial is None


class TestOpValueCache(object):
    class OpSlowComputation(lazyflow.graph.Operator):
        Input = lazyflow.graph.InputSlot()
        Output = lazyflow.graph.OutputSlot()

        def __init__(self, *args, **kwargs):
            super(TestOpValueCache.OpSlowComputation, self).__init__(*args, **kwargs)
            self.executionCount = 0

        def setupOutputs(self):
            self.Output.meta.assignFrom(self.Input.meta)

        def execute(self, slot, subindex, roi, result):
            self.executionCount += 1
            time.sleep(2)
            result[...] = self.Input.value

        def propagateDirty(self, inputSlot, subindex, roi):
            self.Output.setDirty(roi)

    def test_basic(self):
        graph = lazyflow.graph.Graph()
        op = OpValueCache(graph=graph)
        op.Input.setValue("Hello")
        assert op._dirty
        assert op.Output.value == "Hello"

        outputDirtyCount = [0]

        def handleOutputDirty(slot, roi):
            outputDirtyCount[0] += 1

        op.Output.notifyDirty(handleOutputDirty)

        op.forceValue("Goodbye")
        # The cache itself isn't dirty (won't ask input for value)
        assert not op._dirty
        assert op.Output.value == "Goodbye"

        # But the cache notified downstream slots that his value changed
        assert outputDirtyCount[0] == 1

    def test_multithread(self):
        graph = lazyflow.graph.Graph()
        opCompute = TestOpValueCache.OpSlowComputation(graph=graph)
        opCache = OpValueCache(graph=graph)

        opCompute.Input.setValue(100)
        opCache.Input.connect(opCompute.Output)

        def checkOutput():
            assert opCache.Output.value == 100

        threads = []
        for i in range(100):
            threads.append(threading.Thread(target=checkOutput))

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        assert opCompute.executionCount == 1
        assert opCache._dirty == False
        assert opCache._request is None
        assert opCache.Output.value == 100

    def test_cancel(self):
        """
        This ensures that the Output can be acessed from multiple
        threads, even if one thread cancels its request.
        The OpValueCache must handle Request.InvalidRequestException errors correctly.
        """
        n = 20
        graph = lazyflow.graph.Graph()
        opCompute = TestOpValueCache.OpSlowComputation(graph=graph)
        opCache = OpValueCache(graph=graph)

        opCompute.Input.setValue(100)
        opCache.Input.connect(opCompute.Output)

        s = 0
        while s in (0, n):
            # don't want to cancel all requests
            should_cancel = numpy.random.random(n) < 0.2
            s = should_cancel.sum()

        def checkOutput(i):
            req = opCache.Output[:]
            req.submit()
            if should_cancel[i]:
                value = req.wait()[0]
                assert value == 100
            else:
                # Cancel the request and mark the data dirty
                # (forces the next request to restart it.
                req.cancel()
                opCache._dirty = True

        # Create 20 threads, start them, and join them.
        threads = []
        for i in range(n):
            foo = partial(checkOutput, i)
            threads.append(threading.Thread(target=foo))

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        req = opCache.Output[:].wait()
        assert opCache._request is None
        assert opCache.Output.value == 100


class TestOpZeroDefault(object):
    def test_basic(self):
        graph = lazyflow.graph.Graph()
        data = numpy.indices((100, 100), dtype=numpy.uint8).sum(0)
        data = vigra.taggedView(data, vigra.defaultAxistags("xy"))

        opDataProvider = OpBlockedArrayCache(graph=graph)
        opDataProvider.Input.setValue(data)

        op = OpZeroDefault(graph=graph)
        op.MetaInput.setValue(data)

        # Zero by default
        output_data = op.Output[:].wait()
        assert (output_data == 0).all()

        # Connecting a real input triggers dirty notification
        dirty_notification_count = [0]

        def handleDirty(*args):
            dirty_notification_count[0] += 1

        op.Output.notifyDirty(handleDirty)
        op.Input.connect(opDataProvider.Output)

        assert dirty_notification_count[0] == 1

        # Output should provide real data if available
        assert (op.Output[:].wait() == data.view(numpy.ndarray)).all()

        # Output provides zeros again when the data is no longer available
        op.Input.disconnect()
        output_data = op.Output[:].wait()
        assert (output_data == 0).all()


# if __name__ == "__main__":
#    import logging
#    traceLogger = logging.getLogger("TRACE.lazyflow.operators.valueProviders.OpValueCache")
#    traceLogger.setLevel(logging.DEBUG)
#    handler = logging.StreamHandler()
#    handler.setLevel(logging.DEBUG)
#    traceLogger.addHandler(handler)

if __name__ == "__main__":
    import sys
    import nose

    sys.argv.append("--nocapture")  # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture")  # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)
    if not ret:
        sys.exit(1)
