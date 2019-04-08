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

import unittest

from lazyflow.graph import Graph, Operator

from lazyflow.operators.opCache import Cache
from lazyflow.operators.opCache import ObservableCache
from lazyflow.operators.opCache import ManagedCache
from lazyflow.operators.opCache import ManagedBlockedCache
from lazyflow.operators.opCache import MemInfoNode


def iterSubclasses(cls):
    for subcls in cls.__subclasses__():
        for more in iterSubclasses(subcls):
            yield more
    yield cls


def ClassFactory(name, Model, TestClass):
    """
    construct a new test case for 'TestClass' with tests from 'Model'
    """
    newclass = type(name, (TestClass, unittest.TestCase), {})
    newclass.Model = Model
    return newclass


class GeneralTestOpCache(object):
    def setup_method(self, method):
        pass

    def testAPIConformity(self):
        g = Graph()
        op = self.Model(graph=g)
        r = MemInfoNode()
        op.generateReport(r)
        assert r.type is not None
        assert r.id is not None
        assert r.name is not None


# automagically test all implementations of Cache *and* Operator
opClasses = set(iterSubclasses(Operator))
knownAbstractBases = [Cache, ObservableCache, ManagedCache, ManagedBlockedCache]
for subtype in iterSubclasses(Cache):
    if subtype in knownAbstractBases or subtype not in opClasses:
        # skip known abstract implementations and classes that are
        # not operators
        continue
    name = "TestOpCache_Test" + subtype.__name__
    globals()[name] = ClassFactory(name, subtype, GeneralTestOpCache)


class GeneralTestOpObservableCache(object):
    def setup_method(self, method):
        pass

    def testAPIConformity(self):
        g = Graph()
        op = self.Model(graph=g)
        r = MemInfoNode()
        op.generateReport(r)

        used = op.usedMemory()
        assert used is not None
        assert used >= 0
        assert used == r.usedMemory
        frac = op.fractionOfUsedMemoryDirty()
        assert frac is not None
        assert frac >= 0.0
        assert frac <= 1.0
        assert frac == r.fractionOfUsedMemoryDirty


# automagically test all implementations of ObservableCache *and* Operator
for subtype in iterSubclasses(ObservableCache):
    if subtype in knownAbstractBases or subtype not in opClasses:
        # skip known abstract implementations
        continue
    name = "TestOpObservableCache_Test" + subtype.__name__
    globals()[name] = ClassFactory(name, subtype, GeneralTestOpObservableCache)


class GeneralTestOpManagedCache(object):
    def setup_method(self, method):
        pass

    def testAPIConformity(self):
        g = Graph()
        op = self.Model(graph=g)
        r = MemInfoNode()
        op.generateReport(r)

        t = op.lastAccessTime()
        assert t is not None
        assert t >= 0.0
        assert t == r.lastAccessTime

        dirty = op.fractionOfUsedMemoryDirty()
        memFreed = op.freeDirtyMemory()
        assert op.fractionOfUsedMemoryDirty() <= dirty
        assert memFreed is not None
        assert memFreed >= 0

        memFreed = op.freeMemory()
        assert op.usedMemory() == 0
        assert memFreed is not None
        assert memFreed >= 0


# automagically test all implementations of ManagedCache *and* Operator
for subtype in iterSubclasses(ManagedCache):
    if subtype in knownAbstractBases or subtype not in opClasses:
        # skip known abstract implementations
        continue
    name = "TestOpManagedCache_Test" + subtype.__name__
    globals()[name] = ClassFactory(name, subtype, GeneralTestOpManagedCache)


class GeneralTestOpManagedBlockedCache(object):
    def setup_method(self, method):
        pass

    def testAPIConformity(self):
        g = Graph()
        op = self.Model(graph=g)
        r = MemInfoNode()
        op.generateReport(r)

        t = op.lastAccessTime()
        assert t is not None
        assert t >= 0.0
        assert t == r.lastAccessTime

        dirty = op.fractionOfUsedMemoryDirty()
        memFreed = op.freeDirtyMemory()
        assert op.fractionOfUsedMemoryDirty() <= dirty
        assert memFreed is not None
        assert memFreed >= 0

        memFreed = op.freeMemory()
        assert op.usedMemory() == 0
        assert memFreed is not None
        assert memFreed >= 0


# automagically test all implementations of ManagedBlockedCache and Operator
for subtype in iterSubclasses(ManagedBlockedCache):
    if subtype in knownAbstractBases or subtype not in opClasses:
        # skip known abstract implementations
        continue
    name = "TestOpManagedBlockedCache_Test" + subtype.__name__
    globals()[name] = ClassFactory(name, subtype, GeneralTestOpManagedBlockedCache)
