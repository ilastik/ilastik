from __future__ import print_function

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

import weakref
import gc
import unittest

import numpy
import vigra
from lazyflow.graph import Graph

from lazyflow.roi import sliceToRoi, roiToSlice
from lazyflow.operators.opBlockedArrayCache import OpBlockedArrayCache
from lazyflow.operators.opCache import MemInfoNode

from lazyflow.utility.testing import OpArrayPiperWithAccessCount
from lazyflow.operators.cacheMemoryManager import CacheMemoryManager
from functools import reduce


# from lazyflow.request import Request
# Request.reset_thread_pool(0)


class KeyMaker(object):
    def __getitem__(self, *args):
        return list(*args)


make_key = KeyMaker()


class TestOpBlockedArrayCache(unittest.TestCase):
    def setup_method(self, method):
        self.dataShape = (1, 100, 100, 10, 1)
        self.data = numpy.random.randint(0, 256, size=self.dataShape)
        self.data = self.data.astype(numpy.uint32)
        self.data = self.data.view(vigra.VigraArray)
        self.data.axistags = vigra.defaultAxistags("txyzc")

        graph = Graph()
        opProvider = OpArrayPiperWithAccessCount(graph=graph)
        opProvider.Input.setValue(self.data)
        self.opProvider = opProvider

        opCache = OpBlockedArrayCache(graph=graph)
        opCache.Input.connect(opProvider.Output)
        opCache.BlockShape.setValue((20, 20, 20, 20, 20))
        opCache.fixAtCurrent.setValue(False)
        self.opCache = opCache

    def testCacheAccess(self):
        opCache = self.opCache
        opProvider = self.opProvider

        expectedAccessCount = 0
        assert opProvider.accessCount == expectedAccessCount, "Access count={}, expected={}".format(
            opProvider.accessCount, expectedAccessCount
        )

        # Block-aligned request
        slicing = make_key[0:1, 0:10, 10:20, 0:10, 0:1]
        data = opCache.Output(slicing).wait()
        data = data.view(vigra.VigraArray)
        data.axistags = opCache.Output.meta.axistags
        expectedAccessCount += 1
        assert (data == self.data[slicing]).all()
        assert opProvider.accessCount == expectedAccessCount, "Access count={}, expected={}".format(
            opProvider.accessCount, expectedAccessCount
        )
        assert opCache.CleanBlocks.value == [tuple(make_key[0:1, 0:20, 0:20, 0:10, 0:1])]

        # Same request should come from cache, so access count is unchanged
        data = opCache.Output(slicing).wait()
        assert opProvider.accessCount == expectedAccessCount, "Access count={}, expected={}".format(
            opProvider.accessCount, expectedAccessCount
        )
        assert opCache.CleanBlocks.value == [tuple(make_key[0:1, 0:20, 0:20, 0:10, 0:1])]

        # Not block-aligned request
        slicing = make_key[0:1, 35:45, 10:20, 0:10, 0:1]
        data = opCache.Output(slicing).wait()
        data = data.view(vigra.VigraArray)
        data.axistags = opCache.Output.meta.axistags
        expectedAccessCount += 2
        assert (data == self.data[slicing]).all()
        assert opProvider.accessCount == expectedAccessCount, "Access count={}, expected={}".format(
            opProvider.accessCount, expectedAccessCount
        )
        assert opCache.CleanBlocks.value == [
            tuple(make_key[0:1, 0:20, 0:20, 0:10, 0:1]),
            tuple(make_key[0:1, 20:40, 0:20, 0:10, 0:1]),
            tuple(make_key[0:1, 40:60, 0:20, 0:10, 0:1]),
        ]

        # Same request should come from cache, so access count is unchanged
        data = opCache.Output(slicing).wait()
        assert opProvider.accessCount == expectedAccessCount, "Access count={}, expected={}".format(
            opProvider.accessCount, expectedAccessCount
        )

    def testCompressed(self):
        self.opCache.CompressionEnabled.setValue(True)
        self.testCacheAccess()

    def testDirtySource(self):
        opCache = self.opCache
        opProvider = self.opProvider

        oldAccessCount = 0
        assert opProvider.accessCount == oldAccessCount, "Access count={}, expected={}".format(
            opProvider.accessCount, oldAccessCount
        )

        # Request
        slicing = make_key[:, 0:50, 15:45, 0:10, :]
        data = opCache.Output(slicing).wait()
        data = data.view(vigra.VigraArray)
        data.axistags = opCache.Output.meta.axistags
        assert (data == self.data[slicing]).all()
        assert opCache.CleanBlocks.value == [
            tuple(make_key[0:1, 0:20, 0:20, 0:10, 0:1]),
            tuple(make_key[0:1, 0:20, 20:40, 0:10, 0:1]),
            tuple(make_key[0:1, 0:20, 40:60, 0:10, 0:1]),
            tuple(make_key[0:1, 20:40, 0:20, 0:10, 0:1]),
            tuple(make_key[0:1, 20:40, 20:40, 0:10, 0:1]),
            tuple(make_key[0:1, 20:40, 40:60, 0:10, 0:1]),
            tuple(make_key[0:1, 40:60, 0:20, 0:10, 0:1]),
            tuple(make_key[0:1, 40:60, 20:40, 0:10, 0:1]),
            tuple(make_key[0:1, 40:60, 40:60, 0:10, 0:1]),
        ]

        # Our slice intersects 3*3=9 outerBlocks, and a total of 20 innerBlocks
        # Inner caches are allowed to split up the accesses, so there could be as many as 20
        minAccess = oldAccessCount + 9
        maxAccess = oldAccessCount + 20
        assert opProvider.accessCount >= minAccess
        assert opProvider.accessCount <= maxAccess
        oldAccessCount = opProvider.accessCount

        # Track dirty notifications
        gotDirtyKeys = []

        def handleDirty(slot, roi):
            gotDirtyKeys.append(list(roiToSlice(roi.start, roi.stop)))

        opCache.Output.notifyDirty(handleDirty)

        # Change some of the input data and mark it dirty
        dirtykey = make_key[0:1, 10:20, 20:30, 0:3, 0:1]
        self.data[dirtykey] = 0.12345
        opProvider.Input.setDirty(dirtykey)
        assert len(gotDirtyKeys) > 0

        assert opCache.CleanBlocks.value == [
            tuple(make_key[0:1, 0:20, 0:20, 0:10, 0:1]),
            # tuple(make_key[0:1,  0:20, 20:40, 0:10, 0:1]), # dirty
            tuple(make_key[0:1, 0:20, 40:60, 0:10, 0:1]),
            tuple(make_key[0:1, 20:40, 0:20, 0:10, 0:1]),
            tuple(make_key[0:1, 20:40, 20:40, 0:10, 0:1]),
            tuple(make_key[0:1, 20:40, 40:60, 0:10, 0:1]),
            tuple(make_key[0:1, 40:60, 0:20, 0:10, 0:1]),
            tuple(make_key[0:1, 40:60, 20:40, 0:10, 0:1]),
            tuple(make_key[0:1, 40:60, 40:60, 0:10, 0:1]),
        ]

        # Same request, but should need to access the data again due to dirtiness
        data = opCache.Output(slicing).wait()
        data = data.view(vigra.VigraArray)
        data.axistags = opCache.Output.meta.axistags
        assert (data == self.data[slicing]).all()
        assert opCache.CleanBlocks.value == [
            tuple(make_key[0:1, 0:20, 0:20, 0:10, 0:1]),
            tuple(make_key[0:1, 0:20, 20:40, 0:10, 0:1]),
            tuple(make_key[0:1, 0:20, 40:60, 0:10, 0:1]),
            tuple(make_key[0:1, 20:40, 0:20, 0:10, 0:1]),
            tuple(make_key[0:1, 20:40, 20:40, 0:10, 0:1]),
            tuple(make_key[0:1, 20:40, 40:60, 0:10, 0:1]),
            tuple(make_key[0:1, 40:60, 0:20, 0:10, 0:1]),
            tuple(make_key[0:1, 40:60, 20:40, 0:10, 0:1]),
            tuple(make_key[0:1, 40:60, 40:60, 0:10, 0:1]),
        ]

        # The dirty data intersected 1 outerBlocks and a total of 1 innerBlock.
        minAccess = oldAccessCount + 1
        maxAccess = oldAccessCount + 1
        assert opProvider.accessCount >= minAccess
        assert opProvider.accessCount <= maxAccess
        oldAccessCount = opProvider.accessCount

    def testFixAtCurrent(self):
        try:
            CacheMemoryManager().disable()
            opCache = self.opCache
            opProvider = self.opProvider

            # Track dirty notifications
            gotDirtyRois = []

            def handleDirty(slot, roi):
                gotDirtyRois.append((roi.start, roi.stop))

            opCache.Output.notifyDirty(handleDirty)

            opCache.fixAtCurrent.setValue(True)

            oldAccessCount = 0
            assert opProvider.accessCount == oldAccessCount, "Access count={}, expected={}".format(
                opProvider.accessCount, oldAccessCount
            )

            # Request (no access to provider because fixAtCurrent)
            slicing = make_key[:, 0:50, 15:45, 0:1, :]
            data = opCache.Output(slicing).wait()
            assert opProvider.accessCount == oldAccessCount, "Access count={}, expected={}".format(
                opProvider.accessCount, oldAccessCount
            )

            # We haven't accessed this data yet,
            # but fixAtCurrent is True so the cache gives us zeros
            assert (data == 0).all()

            opCache.fixAtCurrent.setValue(False)

            def boundingBox(roiA, roiB):
                return (numpy.minimum(roiA[0], roiB[0]), numpy.maximum(roiA[1], roiB[1]))

            # Since we got zeros while the cache was fixed, the requested
            #  tiles are signaled as dirty when the cache becomes unfixed.
            # Our only requirement here is that any dirty rois we got add up to encompass all the tiles we requested.
            dirty_bb = reduce(boundingBox, gotDirtyRois)
            requested_roi = sliceToRoi(slicing, opCache.Output.meta.shape)
            assert (dirty_bb[0] <= requested_roi[0]).all() and (dirty_bb[1] >= requested_roi[1]).all()

            # Request again.  Data should match this time.
            oldAccessCount = opProvider.accessCount
            data = opCache.Output(slicing).wait()
            data = data.view(vigra.VigraArray)
            data.axistags = opCache.Output.meta.axistags
            assert (data == self.data[slicing]).all()

            # Our slice intersects 3*3=9 outerBlocks, and a total of 20 innerBlocks
            # Inner caches are allowed to split up the accesses, so there could be as many as 20
            minAccess = oldAccessCount + 9
            maxAccess = oldAccessCount + 20
            assert opProvider.accessCount >= minAccess
            assert opProvider.accessCount <= maxAccess
            oldAccessCount = opProvider.accessCount

            # Request again.  Data should match WITHOUT requesting from the source.
            data = opCache.Output(slicing).wait()
            data = data.view(vigra.VigraArray)
            data.axistags = opCache.Output.meta.axistags
            assert (data == self.data[slicing]).all()
            assert opProvider.accessCount == oldAccessCount, "Access count={}, expected={}".format(
                opProvider.accessCount, oldAccessCount
            )

            # Freeze it again
            opCache.fixAtCurrent.setValue(True)

            # Clear previous
            gotDirtyRois = []

            # Change some of the input data that ISN'T cached yet and mark it dirty
            dirtykey = make_key[0:1, 90:100, 90:100, 0:1, 0:1]
            self.data[dirtykey] = 0.12345
            opProvider.Input.setDirty(dirtykey)

            # Dirtiness not propagated due to fixAtCurrent
            assert len(gotDirtyRois) == 0

            # Same request.  Data should still match the previous data (not yet refreshed)
            data2 = opCache.Output(slicing).wait()
            data2 = data2.view(vigra.VigraArray)
            data2.axistags = opCache.Output.meta.axistags
            assert opProvider.accessCount == oldAccessCount, "Access count={}, expected={}".format(
                opProvider.accessCount, oldAccessCount
            )
            assert (data2 == data).all()

            # Unfreeze.
            opCache.fixAtCurrent.setValue(False)

            # Dirty blocks are propagated after the cache is unfixed.
            assert len(gotDirtyRois) > 0

            # Same request.  Data should be updated now that we're unfrozen.
            data = opCache.Output(slicing).wait()
            data = data.view(vigra.VigraArray)
            data.axistags = opCache.Output.meta.axistags
            assert (data == self.data[slicing]).all()

            # Dirty data did not intersect with this request.
            # Data should still be cached (no extra accesses)
            assert opProvider.accessCount == oldAccessCount, "Access count={}, expected={}".format(
                opProvider.accessCount, oldAccessCount
            )

            ###########################3
            # Freeze it again
            opCache.fixAtCurrent.setValue(True)

            # Reset tracked notifications
            gotDirtyRois = []

            # Change some of the input data that IS cached and mark it dirty
            dirtykey = make_key[:, 0:25, 20:40, 0:1, :]
            self.data[dirtykey] = 0.54321
            opProvider.Input.setDirty(dirtykey)

            # Dirtiness not propagated due to fixAtCurrent
            assert len(gotDirtyRois) == 0

            # Same request.  Data should still match the previous data (not yet refreshed)
            data2 = opCache.Output(slicing).wait()
            data2 = data2.view(vigra.VigraArray)
            data2.axistags = opCache.Output.meta.axistags
            assert opProvider.accessCount == oldAccessCount, "Access count={}, expected={}".format(
                opProvider.accessCount, oldAccessCount
            )
            assert (data2 == data).all()

            # Unfreeze. Previous dirty notifications should now be seen.
            opCache.fixAtCurrent.setValue(False)
            assert len(gotDirtyRois) > 0

            # Same request.  Data should be updated now that we're unfrozen.
            data = opCache.Output(slicing).wait()
            data = data.view(vigra.VigraArray)
            data.axistags = opCache.Output.meta.axistags
            assert (data == self.data[slicing]).all()

            # The dirty data intersected 2 outerBlocks, and a total of 6 innerblocks
            # Inner caches are allowed to split up the accesses, so there could be as many as 6
            minAccess = oldAccessCount + 2
            maxAccess = oldAccessCount + 6
            assert opProvider.accessCount >= minAccess
            assert opProvider.accessCount <= maxAccess

            #####################

            #### Repeat plain dirty test to ensure fixAtCurrent didn't mess up the block states.

            opProvider.accessCount = 0  # Reset
            gotDirtyRois = []

            # Change some of the input data and mark it dirty
            dirtykey = make_key[0:1, 10:11, 20:21, 0:3, 0:1]
            self.data[dirtykey] = 0.54321
            opProvider.Input.setDirty(dirtykey)

            assert len(gotDirtyRois) > 0

            # Should need access again.
            slicing = make_key[:, 0:50, 15:45, 0:10, :]
            data = opCache.Output(slicing).wait()
            data = data.view(vigra.VigraArray)
            data.axistags = opCache.Output.meta.axistags
            assert (data == self.data[slicing]).all()

            # The dirty data intersected 1 outerBlocks and a total of 1 innerblock
            minAccess = 1
            maxAccess = 1
            assert opProvider.accessCount >= minAccess
            assert opProvider.accessCount <= maxAccess, "Too many accesses: {}".format(opProvider.accessCount)
            oldAccessCount = opProvider.accessCount

        finally:
            CacheMemoryManager().enable()

    # # the refactored OpBlockedArrayCache is not a cache by itself
    # # keep for reference
    #    def testReportGeneration(self):
    #        opCache = self.opCache
    #        opProvider = self.opProvider
    #
    #        expectedAccessCount = 0
    #        assert opProvider.accessCount == expectedAccessCount, "Access count={}, expected={}".format(opProvider.accessCount, expectedAccessCount)
    #
    #        # Block-aligned request
    #        slicing = make_key[0:1, 0:10, 10:20, 0:10, 0:1]
    #        data = opCache.Output( slicing ).wait()
    #        data = data.view(vigra.VigraArray)
    #        data.axistags = opCache.Output.meta.axistags
    #        expectedAccessCount += 1
    #        assert (data == self.data[slicing]).all()
    #
    #        r = MemInfoNode()
    #        opCache.generateReport(r)
    #        # we are expecting one inner block to be reserved, inner block
    #        # size is 20x20x10, uint32 is 4 bytes
    #        usedMemory = 20*20*10*4
    #        numpy.testing.assert_equal(r.usedMemory, usedMemory)

    def testCleanup(self):
        try:
            CacheMemoryManager().disable()

            op = OpBlockedArrayCache(graph=self.opProvider.graph)
            op.Input.connect(self.opProvider.Output)
            s = self.opProvider.Output.meta.shape
            op.BlockShape.setValue(s)
            op.fixAtCurrent.setValue(False)
            x = op.Output[...].wait()
            op.Input.disconnect()
            op.cleanUp()

            r = weakref.ref(op)
            del op
            gc.collect()
            ref = r()
            if ref is not None:
                for i, o in enumerate(gc.get_referrers(ref)):
                    print("Object", i, ":", type(o), ":", o)

            assert r() is None, "OpBlockedArrayCache was not cleaned up correctly"
        finally:
            CacheMemoryManager().enable()

    def testDirtyPropagation(self):
        opCache = self.opCache
        opProvider = self.opProvider
        # opProvider.Input.setDirty(slice(None))
        # opProvider.clean()
        dirty_key = make_key[0:1, 10:11, 20:21, 0:3, 0:1]
        req_key = make_key[:, 0:50, 15:45, 0:10, :]

        # Should need access again.
        # block shape: (20. 20, 20, 20, 20), input shape: (1,100,100,10,1)
        opCache.Output(req_key).wait()
        assert opProvider.accessCount == 3 * 3 * 1, str(opProvider.accessCount)

        opProvider.clear()

        opProvider.Input.setDirty(dirty_key)
        opCache.Output(req_key).wait()
        assert opProvider.accessCount == 1

    def testBypassMode(self):
        opCache = self.opCache
        opProvider = self.opProvider

        # Activate "bypass mode", which just disables the cache entirely.
        # No block scheme, no data copying, no 'fixAtCurrent'
        opCache.BypassModeEnabled.setValue(True)

        # We can set 'fixAtCurrent', but it makes no difference.
        opCache.fixAtCurrent.setValue(False)

        expectedAccessCount = 0
        assert opProvider.accessCount == expectedAccessCount, "Access count={}, expected={}".format(
            opProvider.accessCount, expectedAccessCount
        )

        # Not block-aligned request -- even in bypass mode, blocking is not ignored
        slicing = make_key[0:1, 35:45, 10:20, 0:10, 0:1]
        data = opCache.Output(slicing).wait()
        data = data.view(vigra.VigraArray)
        data.axistags = opCache.Output.meta.axistags
        expectedAccessCount += 2
        assert (data == self.data[slicing]).all()
        assert opProvider.accessCount == expectedAccessCount, "Access count={}, expected={}".format(
            opProvider.accessCount, expectedAccessCount
        )

        # In bypass mode, the data wasn't cached, so the data is simply requested a second time.
        data = opCache.Output(slicing).wait()
        expectedAccessCount += 2
        assert opProvider.accessCount == expectedAccessCount, "Access count={}, expected={}".format(
            opProvider.accessCount, expectedAccessCount
        )


class TestOpBlockedArrayCache_masked(object):
    def setup_method(self, method):
        self.dataShape = (1, 100, 100, 10, 1)
        self.data = (numpy.random.random(self.dataShape) * 100).astype(int)
        self.data = numpy.ma.masked_array(
            self.data, mask=numpy.ma.getmaskarray(self.data), fill_value=numpy.iinfo(int).max, shrink=False
        )
        self.data[:, 0] = numpy.ma.masked

        graph = Graph()
        opProvider = OpArrayPiperWithAccessCount(graph=graph)
        opProvider.Input.meta.axistags = vigra.defaultAxistags("txyzc")
        opProvider.Input.meta.has_mask = True
        opProvider.Input.setValue(self.data)
        self.opProvider = opProvider

        opCache = OpBlockedArrayCache(graph=graph)
        opCache.Input.connect(opProvider.Output)
        opCache.BlockShape.setValue((20, 20, 20, 20, 20))
        opCache.fixAtCurrent.setValue(False)
        self.opCache = opCache

    def testCacheAccess(self):
        opCache = self.opCache
        opProvider = self.opProvider

        expectedAccessCount = 0
        assert opProvider.accessCount == expectedAccessCount, "Access count={}, expected={}".format(
            opProvider.accessCount, expectedAccessCount
        )

        # Block-aligned request
        slicing = make_key[0:1, 0:10, 10:20, 0:10, 0:1]
        data = opCache.Output(slicing).wait()
        data.axistags = opCache.Output.meta.axistags
        expectedAccessCount += 1
        assert (data == self.data[slicing]).all()
        assert (data.mask == self.data.mask[slicing]).all()
        assert (data.fill_value == self.data.fill_value).all()
        assert opProvider.accessCount == expectedAccessCount, "Access count={}, expected={}".format(
            opProvider.accessCount, expectedAccessCount
        )

        # Same request should come from cache, so access count is unchanged
        data = opCache.Output(slicing).wait()
        assert opProvider.accessCount == expectedAccessCount, "Access count={}, expected={}".format(
            opProvider.accessCount, expectedAccessCount
        )

        # Not block-aligned request
        slicing = make_key[0:1, 35:45, 10:20, 0:10, 0:1]
        data = opCache.Output(slicing).wait()
        data.axistags = opCache.Output.meta.axistags
        expectedAccessCount += 2
        assert (data == self.data[slicing]).all()
        assert (data.mask == self.data.mask[slicing]).all()
        assert (data.fill_value == self.data.fill_value).all()
        assert opProvider.accessCount == expectedAccessCount, "Access count={}, expected={}".format(
            opProvider.accessCount, expectedAccessCount
        )

        # Same request should come from cache, so access count is unchanged
        data = opCache.Output(slicing).wait()
        assert opProvider.accessCount == expectedAccessCount, "Access count={}, expected={}".format(
            opProvider.accessCount, expectedAccessCount
        )

    def testDirtySource(self):
        opCache = self.opCache
        opProvider = self.opProvider

        oldAccessCount = 0
        assert opProvider.accessCount == oldAccessCount, "Access count={}, expected={}".format(
            opProvider.accessCount, oldAccessCount
        )

        # Request
        slicing = make_key[:, 0:50, 15:45, 0:10, :]
        data = opCache.Output(slicing).wait()
        data.axistags = opCache.Output.meta.axistags
        assert (data == self.data[slicing]).all()
        assert (data.mask == self.data.mask[slicing]).all()
        assert (data.fill_value == self.data.fill_value).all()

        # Our slice intersects 3*3=9 outerBlocks, and a total of 20 innerBlocks
        # Inner caches are allowed to split up the accesses, so there could be as many as 20
        minAccess = oldAccessCount + 9
        maxAccess = oldAccessCount + 20
        assert opProvider.accessCount >= minAccess
        assert opProvider.accessCount <= maxAccess
        oldAccessCount = opProvider.accessCount

        # Track dirty notifications
        gotDirtyKeys = []

        def handleDirty(slot, roi):
            gotDirtyKeys.append(list(roiToSlice(roi.start, roi.stop)))

        opCache.Output.notifyDirty(handleDirty)

        # Change some of the input data and mark it dirty
        dirtykey = make_key[0:1, 10:20, 20:30, 0:3, 0:1]
        self.data[dirtykey] = 0.12345
        opProvider.Input.setDirty(dirtykey)
        assert len(gotDirtyKeys) > 0

        # Same request, but should need to access the data again due to dirtiness
        data = opCache.Output(slicing).wait()
        data.axistags = opCache.Output.meta.axistags

        assert (data == self.data[slicing]).all()
        assert (data.mask == self.data.mask[slicing]).all()
        assert (data.fill_value == self.data.fill_value).all()

        # The dirty data intersected 1 outerBlocks and a total of 1 innerBlock.
        minAccess = oldAccessCount + 1
        maxAccess = oldAccessCount + 1
        assert opProvider.accessCount >= minAccess
        assert opProvider.accessCount <= maxAccess
        oldAccessCount = opProvider.accessCount

    def testFixAtCurrent(self):
        opCache = self.opCache
        opProvider = self.opProvider

        # Track dirty notifications
        gotDirtyRois = []

        def handleDirty(slot, roi):
            gotDirtyRois.append((roi.start, roi.stop))

        opCache.Output.notifyDirty(handleDirty)

        opCache.fixAtCurrent.setValue(True)

        oldAccessCount = 0
        assert opProvider.accessCount == oldAccessCount, "Access count={}, expected={}".format(
            opProvider.accessCount, oldAccessCount
        )

        # Request (no access to provider because fixAtCurrent)
        slicing = make_key[:, 0:50, 15:45, 0:1, :]
        data = opCache.Output(slicing).wait()
        assert opProvider.accessCount == oldAccessCount, "Access count={}, expected={}".format(
            opProvider.accessCount, oldAccessCount
        )

        # We haven't accessed this data yet,
        # but fixAtCurrent is True so the cache gives us zeros
        assert (data == 0).all()
        assert (data.mask == False).all()
        assert (data.fill_value == 0).all()

        opCache.fixAtCurrent.setValue(False)

        def boundingBox(roiA, roiB):
            return (numpy.minimum(roiA[0], roiB[0]), numpy.maximum(roiA[1], roiB[1]))

        # Since we got zeros while the cache was fixed, the requested
        #  tiles are signaled as dirty when the cache becomes unfixed.
        dirty_bb = reduce(boundingBox, gotDirtyRois)
        requested_roi = sliceToRoi(slicing, opCache.Output.meta.shape)
        assert (dirty_bb[0] <= requested_roi[0]).all() and (dirty_bb[1] >= requested_roi[1]).all()

        # Request again.  Data should match this time.
        oldAccessCount = opProvider.accessCount
        data = opCache.Output(slicing).wait()
        data.axistags = opCache.Output.meta.axistags
        assert (data == self.data[slicing]).all()
        assert (data.mask == self.data.mask[slicing]).all()
        assert (data.fill_value == self.data.fill_value).all()

        # Our slice intersects 3*3=9 outerBlocks, and a total of 20 innerBlocks
        # Inner caches are allowed to split up the accesses, so there could be as many as 20
        minAccess = oldAccessCount + 9
        maxAccess = oldAccessCount + 20
        assert opProvider.accessCount >= minAccess
        assert opProvider.accessCount <= maxAccess
        oldAccessCount = opProvider.accessCount

        # Request again.  Data should match WITHOUT requesting from the source.
        data = opCache.Output(slicing).wait()
        data.axistags = opCache.Output.meta.axistags
        assert (data == self.data[slicing]).all()
        assert (data.mask == self.data.mask[slicing]).all()
        assert (data.fill_value == self.data.fill_value).all()
        assert opProvider.accessCount == oldAccessCount, "Access count={}, expected={}".format(
            opProvider.accessCount, oldAccessCount
        )

        # Freeze it again
        opCache.fixAtCurrent.setValue(True)

        # Clear previous
        gotDirtyRois = []

        # Change some of the input data that ISN'T cached yet and mark it dirty
        dirtykey = make_key[0:1, 90:100, 90:100, 0:1, 0:1]
        self.data[dirtykey] = 0.12345
        opProvider.Input.setDirty(dirtykey)

        # Dirtiness not propagated due to fixAtCurrent
        assert len(gotDirtyRois) == 0

        # Same request.  Data should still match the previous data (not yet refreshed)
        data2 = opCache.Output(slicing).wait()
        data2.axistags = opCache.Output.meta.axistags
        assert opProvider.accessCount == oldAccessCount, "Access count={}, expected={}".format(
            opProvider.accessCount, oldAccessCount
        )
        assert (data2 == data).all()
        assert (data2.mask == data.mask).all()
        assert (data2.fill_value == data.fill_value).all()

        # Unfreeze.
        opCache.fixAtCurrent.setValue(False)

        # Dirty blocks are propagated after the cache is unfixed.
        assert len(gotDirtyRois) > 0

        # Same request.  Data should be updated now that we're unfrozen.
        data = opCache.Output(slicing).wait()
        data.axistags = opCache.Output.meta.axistags
        assert (data == self.data[slicing]).all()
        assert (data.mask == self.data.mask[slicing]).all()
        assert (data.fill_value == self.data.fill_value).all()

        # Dirty data did not intersect with this request.
        # Data should still be cached (no extra accesses)
        assert opProvider.accessCount == oldAccessCount, "Access count={}, expected={}".format(
            opProvider.accessCount, oldAccessCount
        )

        ###########################3
        # Freeze it again
        opCache.fixAtCurrent.setValue(True)

        # Reset tracked notifications
        gotDirtyRois = []

        # Change some of the input data that IS cached and mark it dirty
        dirtykey = make_key[:, 0:25, 20:40, 0:1, :]
        self.data[dirtykey] = 0.54321
        opProvider.Input.setDirty(dirtykey)

        # Dirtiness not propagated due to fixAtCurrent
        assert len(gotDirtyRois) == 0

        # Same request.  Data should still match the previous data (not yet refreshed)
        data2 = opCache.Output(slicing).wait()
        data2.axistags = opCache.Output.meta.axistags
        assert opProvider.accessCount == oldAccessCount, "Access count={}, expected={}".format(
            opProvider.accessCount, oldAccessCount
        )
        assert (data2 == data).all()
        assert (data2.mask == data.mask).all()
        assert (data2.fill_value == data.fill_value).all()

        # Unfreeze. Previous dirty notifications should now be seen.
        opCache.fixAtCurrent.setValue(False)
        assert len(gotDirtyRois) > 0

        # Same request.  Data should be updated now that we're unfrozen.
        data = opCache.Output(slicing).wait()
        data.axistags = opCache.Output.meta.axistags
        assert (data == self.data[slicing]).all()
        assert (data.mask == self.data.mask[slicing]).all()
        assert (data.fill_value == self.data.fill_value).all()

        # The dirty data intersected 2 outerBlocks, and a total of 6 innerblocks
        # Inner caches are allowed to split up the accesses, so there could be as many as 6
        minAccess = oldAccessCount + 2
        maxAccess = oldAccessCount + 6
        assert opProvider.accessCount >= minAccess
        assert opProvider.accessCount <= maxAccess
        oldAccessCount = opProvider.accessCount

        #####################

        #### Repeat plain dirty test to ensure fixAtCurrent didn't mess up the block states.

        gotDirtyRois = []

        # Change some of the input data and mark it dirty
        dirtykey = make_key[0:1, 10:11, 20:21, 0:3, 0:1]
        self.data[dirtykey] = 0.54321
        opProvider.Input.setDirty(dirtykey)

        assert len(gotDirtyRois) > 0

        # Should need access again.
        slicing = make_key[:, 0:50, 15:45, 0:10, :]
        data = opCache.Output(slicing).wait()
        data.axistags = opCache.Output.meta.axistags
        assert (data == self.data[slicing]).all()
        assert (data.mask == self.data.mask[slicing]).all()
        assert (data.fill_value == self.data.fill_value).all()

        # The dirty data intersected 1 outerBlocks and a total of 1 innerblock
        minAccess = oldAccessCount + 1
        maxAccess = oldAccessCount + 1
        assert opProvider.accessCount >= minAccess
        assert opProvider.accessCount <= maxAccess, "Too many accesses: {}".format(opProvider.accessCount)
        oldAccessCount = opProvider.accessCount


if __name__ == "__main__":
    import sys
    import nose

    sys.argv.append("--nocapture")  # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture")  # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)
    if not ret:
        sys.exit(1)
