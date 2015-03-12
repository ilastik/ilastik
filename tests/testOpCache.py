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

import unittest

from lazyflow.graph import Graph

from lazyflow.operators.opCache import OpCache
from lazyflow.operators.opCache import OpObservableCache
from lazyflow.operators.opCache import OpManagedCache
from lazyflow.operators.opCache import MemInfoNode


def ClassFactory(name, Model, TestClass):
    '''
    construct a new test case for 'TestClass' with tests from 'Model'
    '''
    newclass = type(name, (TestClass, unittest.TestCase), {})
    newclass.Model = Model
    return newclass


class GeneralTestOpCache(object):
    def setUp(self):
        pass

    def testAPIConformity(self):
        g = Graph()
        op = self.Model(graph=g)
        r = MemInfoNode()
        op.generateReport(r)
        assert r.type is not None
        assert r.id is not None
        assert r.name is not None


# automagically test all implementations of OpCache
for subtype in OpCache.__subclasses__():
    if subtype in [OpCache, OpObservableCache, OpManagedCache]:
        # skip known abstract implementations
        continue
    name = "TestOpCache_Test" + subtype.__name__
    globals()[name] = ClassFactory(name, subtype, GeneralTestOpCache)


class GeneralTestOpObservableCache(object):
    def setUp(self):
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


# automagically test all implementations of OpObservableCache
for subtype in OpObservableCache.__subclasses__():
    if subtype in [OpObservableCache, OpManagedCache]:
        # skip known abstract implementations
        continue
    name = "TestOpObservableCache_Test" + subtype.__name__
    globals()[name] = ClassFactory(name, subtype, GeneralTestOpObservableCache)


class GeneralTestOpManagedCache(object):
    def setUp(self):
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

        op.freeMemory()
        assert op.usedMemory() == 0


# automagically test all implementations of OpManagedCache
for subtype in OpManagedCache.__subclasses__():
    if subtype in [OpManagedCache]:
        # skip known abstract implementations
        continue
    name = "TestOpManagedCache_Test" + subtype.__name__
    globals()[name] = ClassFactory(name, subtype, GeneralTestOpManagedCache)

