from builtins import zip
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

import unittest
from functools import total_ordering

import numpy as np
from numpy.testing import assert_array_equal

from lazyflow.utility.priorityQueue import PriorityQueue


@total_ordering
class Comp(object):
    def __init__(self, c):
        self._c = c

    def __hash__(self):
        return self._c

    def __eq__(self, other):
        return self._c == other._c

    def __lt__(self, other):
        return self._c < other._c


c2 = Comp(2)
c1 = Comp(1)
assert c1 < c2
assert c2 > c1


class TestPriorityQueue(unittest.TestCase):
    def setup_method(self, method):
        pass

    def testIntegers(self):
        x = np.random.randint(0, 2 ** 15, size=(100,)).astype(int)
        y = np.sort(x)
        pq = PriorityQueue()
        for a in x:
            pq.push(a)
        z = np.asarray([pq.pop() for i in range(len(pq))])
        z = z.astype(int)
        assert_array_equal(y, z)

    def testObjects(self):
        x = [3, 1, 1, 2]
        a = [Comp(i) for i in x]

        pq = PriorityQueue()
        for c in a:
            pq.push(c)
        y = [pq.pop() for i in range(len(pq))]

        assert y[2] is a[3]
        assert y[3] is a[0]
        assert y[0] is a[1]
        assert y[1] is a[2]

    def testOnePriority(self):
        n = 100
        p = np.random.random(size=(n,))
        a = np.random.random(size=(n,))
        combined = list(zip(p, a))

        pq = PriorityQueue()
        for pair in combined:
            pq.push(pair)

        s = sorted(combined, key=lambda x: x[0])
        y = [pq.pop() for i in range(len(pq))]

        assert_array_equal(s, y)

    def testTwoPriorities(self):
        n = 400
        p1 = np.random.randint(0, 5, size=(n,))
        p2 = np.random.random(size=(n,))
        a = np.random.random(size=(n,))
        combined = list(zip(p1, p2, a))

        pq = PriorityQueue()
        for pair in combined:
            pq.push(pair)

        s = sorted(combined, key=lambda x: x[0] + x[1])
        x = [a[2] for a in s]
        y = [pq.pop()[2] for i in range(len(pq))]

        assert_array_equal(x, y)
