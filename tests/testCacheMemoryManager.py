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

import gc
import time

import numpy as np
import vigra

import unittest

import lazyflow
from lazyflow.graph import Graph
from lazyflow.roi import enlargeRoiForHalo, roiToSlice
from lazyflow.rtype import SubRegion
from lazyflow.request import Request
from lazyflow.utility import BigRequestStreamer
from lazyflow.operators.cacheMemoryManager import CacheMemoryManager
from lazyflow.utility import Memory
from lazyflow.operators.cacheMemoryManager import default_refresh_interval
from lazyflow.operators.opCache import Cache
from lazyflow.operators.opBlockedArrayCache import OpBlockedArrayCache
from lazyflow.operators.opSplitRequestsBlockwise import OpSplitRequestsBlockwise
from lazyflow.operators.filterOperators import OpGaussianSmoothing

from lazyflow.utility.testing import OpArrayPiperWithAccessCount

import logging

logger = logging.getLogger("tests.testCacheMemoryManager")
mgrLogger = logging.getLogger("lazyflow.operators.cacheMemoryManager")


class NonRegisteredCache(object):
    def __init__(self, name):
        self.name = name
        self._randn = np.random.randint(2 ** 16)


Cache.register(NonRegisteredCache)
assert issubclass(NonRegisteredCache, Cache)


class TestCacheMemoryManager(unittest.TestCase):
    def setup_method(self, method):
        pass

    def teardown_method(self, method):
        # reset cleanup frequency to sane value
        # reset max memory
        Memory.setAvailableRamCaches(-1)
        mgr = CacheMemoryManager()
        mgr.setRefreshInterval(default_refresh_interval)
        mgr.enable()
        Request.reset_thread_pool()

    def testAPIConformity(self):
        c = NonRegisteredCache("c")
        mgr = CacheMemoryManager()

        # dont clean up while we are testing
        mgr.disable()

        import weakref

        d = NonRegisteredCache("testwr")
        s = weakref.WeakSet()
        s.add(d)
        del d
        gc.collect()
        l = list(s)
        assert len(l) == 0, l[0].name

        c1 = NonRegisteredCache("c1")
        c1a = c1
        c2 = NonRegisteredCache("c2")

        mgr.addFirstClassCache(c)
        mgr.addCache(c1)
        mgr.addCache(c1a)
        mgr.addCache(c2)

        fcc = mgr.getFirstClassCaches()
        assert len(fcc) == 1, "too many first class caches"
        assert c in fcc, "did not register fcc correctly"
        del fcc

        cs = mgr.getCaches()
        assert len(cs) == 3, "wrong number of caches"
        refcs = [c, c1, c2]
        for cache in refcs:
            assert cache in cs, "{} not stored".format(cache.name)
        del cs
        del refcs
        del cache

        del c1a
        gc.collect()
        cs = mgr.getCaches()
        assert c1 in cs
        assert len(cs) == 3, str([x.name for x in cs])
        del cs

        del c2
        gc.collect()
        cs = mgr.getCaches()
        assert len(cs) == 2, str([x.name for x in cs])

    def testCacheHandling(self):
        n, k = 10, 5
        vol = np.zeros((n,) * 5, dtype=np.uint8)
        vol = vigra.taggedView(vol, axistags="txyzc")

        g = Graph()
        pipe = OpArrayPiperWithAccessCount(graph=g)
        cache = OpBlockedArrayCache(graph=g)

        mgr = CacheMemoryManager()

        # disallow cache memory
        Memory.setAvailableRamCaches(0)

        # set to frequent cleanup
        mgr.setRefreshInterval(0.01)
        mgr.enable()

        cache.BlockShape.setValue((k,) * 5)
        cache.Input.connect(pipe.Output)
        pipe.Input.setValue(vol)

        a = pipe.accessCount
        cache.Output[...].wait()
        b = pipe.accessCount
        assert b > a, "did not cache"

        # let the manager clean up
        mgr.enable()
        time.sleep(0.5)
        gc.collect()

        cache.Output[...].wait()
        c = pipe.accessCount
        assert c > b, "did not clean up"

    def testBlockedCacheHandling(self):
        n, k = 10, 5
        vol = np.zeros((n,) * 5, dtype=np.uint8)
        vol = vigra.taggedView(vol, axistags="txyzc")

        g = Graph()
        pipe = OpArrayPiperWithAccessCount(graph=g)
        cache = OpBlockedArrayCache(graph=g)

        mgr = CacheMemoryManager()

        # restrict cache memory to 0 Byte
        Memory.setAvailableRamCaches(0)

        # set to frequent cleanup
        mgr.setRefreshInterval(0.01)
        mgr.enable()

        cache.BlockShape.setValue((k,) * 5)
        cache.Input.connect(pipe.Output)
        pipe.Input.setValue(vol)

        a = pipe.accessCount
        cache.Output[...].wait()
        b = pipe.accessCount
        assert b > a, "did not cache"

        # let the manager clean up
        mgr.enable()
        time.sleep(0.5)
        gc.collect()

        cache.Output[...].wait()
        c = pipe.accessCount
        assert c > b, "did not clean up"

    def testBadMemoryConditions(self):
        """
        TestCacheMemoryManager.testBadMemoryConditions

        This test is a proof of the proposition in
            https://github.com/ilastik/lazyflow/issue/185
        which states that, given certain memory constraints, the cache
        cleanup strategy in use is inefficient. An advanced strategy
        should pass the test.
        """

        mgr = CacheMemoryManager()
        mgr.setRefreshInterval(0.01)
        mgr.enable()

        d = 2
        tags = "xy"

        shape = (999,) * d
        blockshape = (333,) * d

        # restrict memory for computation to one block (including fudge
        # factor 2 of bigRequestStreamer)
        cacheMem = np.prod(shape)
        Memory.setAvailableRam(np.prod(blockshape) * 2 + cacheMem)

        # restrict cache memory to the whole volume
        Memory.setAvailableRamCaches(cacheMem)

        # to ease observation, do everything single threaded
        Request.reset_thread_pool(num_workers=1)

        x = np.zeros(shape, dtype=np.uint8)
        x = vigra.taggedView(x, axistags=tags)

        g = Graph()
        pipe = OpArrayPiperWithAccessCount(graph=g)
        pipe.Input.setValue(x)
        pipe.Output.meta.ideal_blockshape = blockshape

        # simulate BlockedArrayCache behaviour without caching
        # cache = OpSplitRequestsBlockwise(True, graph=g)
        # cache.BlockShape.setValue(blockshape)
        # cache.Input.connect(pipe.Output)

        cache = OpBlockedArrayCache(graph=g)
        cache.Input.connect(pipe.Output)
        cache.BlockShape.setValue(blockshape)

        op = OpEnlarge(graph=g)
        op.Input.connect(cache.Output)

        split = OpSplitRequestsBlockwise(True, graph=g)
        split.BlockShape.setValue(blockshape)
        split.Input.connect(op.Output)

        streamer = BigRequestStreamer(split.Output, [(0,) * len(shape), shape])
        streamer.execute()

        # in the worst case, we have 4*4 + 4*6 + 9 = 49 requests to pipe
        # in the best case, we have 9
        np.testing.assert_equal(pipe.accessCount, 9)


class OpEnlarge(OpArrayPiperWithAccessCount):
    delay = 0.1

    def setupOutputs(self):
        self.Output.meta.ram_usage_per_requested_pixel = 1
        super(OpEnlarge, self).setupOutputs()

    def execute(self, slot, subindex, roi, result):
        sigma = 3.0
        roi_with_halo, result_roi = enlargeRoiForHalo(
            roi.start, roi.stop, self.Input.meta.shape, sigma, return_result_roi=True
        )
        start, stop = roi_with_halo
        newroi = SubRegion(self.Input, start=start, stop=stop)
        data = self.Input.get(newroi).wait()
        time.sleep(self.delay)
        result[:] = data[roiToSlice(*result_roi)]


if __name__ == "__main__":
    import sys

    # Set up logging for debug
    logHandler = logging.StreamHandler(sys.stdout)
    logger.addHandler(logHandler)
    mgrLogger.addHandler(logHandler)

    logger.setLevel(logging.DEBUG)
    mgrLogger.setLevel(logging.DEBUG)

    # Run nose
    import nose

    sys.argv.append("--nocapture")  # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture")  # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)
    if not ret:
        sys.exit(1)
