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

import gc
import time

import numpy as np
import vigra

import unittest

import lazyflow
from lazyflow.graph import Graph
from lazyflow.operators.cacheMemoryManager import CacheMemoryManager
from lazyflow.operators.cacheMemoryManager import memoryUsage
from lazyflow.operators.cacheMemoryManager\
    import default_refresh_interval
from lazyflow.operators.opCache import Cache
from lazyflow.operators.opArrayCache import OpArrayCache
from lazyflow.utility.testing import OpArrayPiperWithAccessCount


class NonRegisteredCache(object):
    def __init__(self, name):
        self.name = name
        self._randn = np.random.randint(2**16)

Cache.register(NonRegisteredCache)
assert issubclass(NonRegisteredCache, Cache)



class TestCacheMemoryManager(unittest.TestCase):
    def setUp(self):
        self._old_ram_mb = lazyflow.AVAILABLE_RAM_MB

    def tearDown(self):
        # reset cleanup frequency to sane value
        # reset max memory
        lazyflow.AVAILABLE_RAM_MB = self._old_ram_mb
        mgr = CacheMemoryManager()
        mgr.setRefreshInterval(default_refresh_interval)
        mgr.enable()

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
        assert len(cs) == 3, str(map(lambda x: x.name, cs))
        del cs

        del c2
        gc.collect()
        cs = mgr.getCaches()
        assert len(cs) == 2, str(map(lambda x: x.name, cs))

    def testCacheHandling(self):
        n, k = 10, 5
        vol = np.random.randint(255, size=(n,)*5).astype(np.uint8)
        vol = vigra.taggedView(vol, axistags='txyzc')

        g = Graph()
        pipe = OpArrayPiperWithAccessCount(graph=g)
        cache = OpArrayCache(graph=g)

        mgr = CacheMemoryManager()

        # restrict memory to 1 Byte
        # note that 0 has a special meaning
        lazyflow.AVAILABLE_RAM_MB = 0.000001

        # set to frequent cleanup
        mgr.setRefreshInterval(.01)
        mgr.enable()

        cache.blockShape.setValue((k,)*5)
        cache.Input.connect(pipe.Output)
        pipe.Input.setValue(vol)

        a = pipe.accessCount
        cache.Output[...].wait()
        b = pipe.accessCount
        assert b > a, "did not cache"

        # let the manager clean up
        mgr.enable()
        time.sleep(.5)
        gc.collect()

        cache.Output[...].wait()
        c = pipe.accessCount
        assert c > b, "did not clean up"
