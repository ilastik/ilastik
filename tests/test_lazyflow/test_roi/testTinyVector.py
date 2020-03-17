from __future__ import print_function, division
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
import sys
import copy
import operator  # This is the Python standard operator module, not lazyflow.operator!
import numpy
from lazyflow.roi import TinyVector


class TestTinyVector(object):
    def setup_method(self, method):
        self.v1 = TinyVector(list(range(1, 11)))
        self.v2 = TinyVector(list(range(11, 21)))

        self.a1 = numpy.array(self.v1)
        self.a2 = numpy.array(self.v2)

        self.l1 = list(self.v1)
        self.l2 = list(self.v2)

        self.scalar = 3

    def _checkBinaryOperation(self, op, numpyOp=None):
        if numpyOp is None:
            numpyOp = op
        v1 = self.v1
        v2 = self.v2
        a1 = self.a1
        a2 = self.a2
        l1 = self.l1
        l2 = self.l2
        scalar = self.scalar

        try:
            # Try all combinations of TinyVector with TinyVector, numpy.array, and plain list
            # as both LEFT AND RIGHT operands
            # Check each against the the expected results (numpy.array is the reference)
            assert all(op(v1, v2) == numpyOp(a1, a2))
            assert all(op(v2, v1) == numpyOp(a2, a1))

            assert all(op(v1, l2) == numpyOp(a1, l2))
            assert all(op(l2, v1) == numpyOp(l2, a1))

            assert all(op(v1, a2) == numpyOp(a1, a2))
            assert all(op(v2, a1) == numpyOp(a2, a1))

            assert all(op(v1, scalar) == numpyOp(a1, scalar))
            assert all(op(scalar, v1) == numpyOp(scalar, a1))

        except AssertionError:
            print("Failed for op: {}".format(op))
            raise

    def testBinary(self):
        self._checkBinaryOperation(operator.add)
        self._checkBinaryOperation(operator.sub)
        self._checkBinaryOperation(operator.mul)
        self._checkBinaryOperation(operator.mod)
        self._checkBinaryOperation(operator.floordiv)

        self._checkBinaryOperation(operator.and_)
        self._checkBinaryOperation(operator.or_)
        self._checkBinaryOperation(operator.xor)

        self._checkBinaryOperation(operator.eq)
        self._checkBinaryOperation(operator.ne)
        self._checkBinaryOperation(operator.lt)
        self._checkBinaryOperation(operator.le)
        self._checkBinaryOperation(operator.ge)
        self._checkBinaryOperation(operator.gt)

        if sys.version_info.major == 2:
            self._checkBinaryOperation(operator.div, lambda a, b: a / b)

    def _checkAssignment(self, assignmentOp, numpyOp=None):
        if numpyOp is None:
            numpyOp = assignmentOp
        v1 = self.v1
        v2 = self.v2
        a1 = self.a1
        a2 = self.a2
        l1 = self.l1
        l2 = self.l2
        scalar = self.scalar

        try:
            _a1 = copy.copy(a1)
            _v1 = copy.copy(v1)
            _v2 = copy.copy(v2)
            _a1 = numpyOp(_a1, a2)
            _v1 = assignmentOp(_v1, _v2)
            assert all(_a1 == _v1), "Assignment operation failed."
            assert all(_v2 == v2), "Assignment modified the wrong value."

            _a1 = copy.copy(a1)
            _v1 = copy.copy(v1)
            _l2 = copy.copy(l2)
            _a1 = numpyOp(_a1, l2)
            _v1 = assignmentOp(_v1, _l2)
            assert all(_a1 == _v1), "Assignment operation failed."
            assert all([x_y[0] == x_y[1] for x_y in zip(_l2, l2)]), "Assignment modified the wrong value."

            _a1 = copy.copy(a1)
            _v1 = copy.copy(v1)
            _a1 = numpyOp(_a1, scalar)
            _v1 = assignmentOp(_v1, scalar)
            assert all(_a1 == _v1), "Assignment operation failed."

        except AssertionError:
            print("Failed for assignment op: {}".format(assignmentOp))
            raise

    def testAssignment(self):
        self._checkAssignment(operator.iadd)
        self._checkAssignment(operator.isub)
        self._checkAssignment(operator.imul)
        self._checkAssignment(operator.imod)
        self._checkAssignment(operator.ifloordiv)
        self._checkAssignment(operator.iand)
        self._checkAssignment(operator.ior)
        self._checkAssignment(operator.ixor)

        if sys.version_info.major == 2:
            self._checkAssignment(operator.idiv, lambda a, b: a / b)

    def testComparison(self):
        v1 = self.v1
        v2 = self.v2
        a1 = self.a1
        a2 = self.a2
        l1 = self.l1
        l2 = self.l2

        assert all(v1 == v1)
        assert all(v1 == a1)
        assert all(v1 == l1)
        assert all(v2 == v2)
        assert all(v2 == a2)
        assert all(v2 == l2)

        assert not any(v1 == a2)
        assert not any(v2 == a1)
        assert not any(v1 == l2)
        assert not any(v2 == l1)

    def testAll(self):
        a = TinyVector([True, True, True])
        b = TinyVector([True, False, True])
        c = TinyVector([False, False, False])
        assert a.all()
        assert not b.all()
        assert not c.all()

    def testAny(self):
        a = TinyVector([True, True, True])
        b = TinyVector([True, False, True])
        c = TinyVector([False, False, False])
        assert a.any()
        assert b.any()
        assert not c.any()

    def _checkUnaryOperation(self, op):
        v1 = self.v1
        nv1 = TinyVector(-x for x in v1)
        a1 = numpy.array(v1)
        na1 = numpy.array(nv1)

        assert all(op(v1) == op(a1))
        assert all(op(nv1) == op(na1))

    def testUnaryOperators(self):
        self._checkUnaryOperation(operator.neg)
        self._checkUnaryOperation(operator.pos)
        self._checkUnaryOperation(operator.abs)
        self._checkUnaryOperation(operator.invert)


if __name__ == "__main__":
    import sys
    import nose

    sys.argv.append("--nocapture")  # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture")  # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)

    if not ret:
        sys.exit(1)
