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


# automagically test all implementations of OpCache
for subtype in OpCache.__subclasses__():
    if subtype in [OpObservableCache, OpManagedCache]:
        # skip known abstract implementations
        continue
    name = "TestOpCache_Test" + subtype.__name__
    globals()[name] = ClassFactory(name, subtype, GeneralTestOpCache)


#class TestOpObservableCache(unittest.TestCase):
#    def setUp(self):
#        pass
#
#
#class TestOpManagedCache(unittest.TestCase):
#    def setUp(self):
#        pass