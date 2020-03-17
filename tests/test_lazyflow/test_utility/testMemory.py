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
from lazyflow.utility import Memory
from lazyflow.utility.memory import FormatError
from functools import partial

from numpy.testing import assert_equal


class TestMemory(unittest.TestCase):
    def setup_method(self, method):
        Memory.setAvailableRam(-1)
        Memory.setAvailableRamCaches(-1)

    def teardown_method(self, method):
        Memory.setAvailableRam(-1)
        Memory.setAvailableRamCaches(-1)

    def testFormatting(self):
        fmt = partial(Memory.format, trailing_digits=1)
        r = 1
        assert fmt(r) == "1.0B"

        r *= 1024
        assert fmt(r) == "1.0KiB"

        r *= 1024
        assert fmt(r) == "1.0MiB"

        r *= 1024
        assert fmt(r) == "1.0GiB"

        r *= 1024
        assert fmt(r) == "1.0TiB"

    def testSettings(self):
        assert Memory.getAvailableRam() > 0
        assert Memory.getAvailableRamCaches() > 0
        ram = 47 * 1111
        Memory.setAvailableRam(ram)
        assert Memory.getAvailableRam() == ram
        cache_ram = ram // 3
        Memory.setAvailableRamCaches(cache_ram)
        assert Memory.getAvailableRamCaches() == cache_ram

    def testParsing(self):
        parse = Memory.parse

        d = parse("15B")
        assert_equal(d, 15)

        d = parse("1.0KiB")
        assert_equal(d, 1024)

        d = parse("2.25MiB")
        assert_equal(d, int(2.25 * 1024 ** 2))

        with self.assertRaises(FormatError):
            d = parse("bla")

        with self.assertRaises(FormatError):
            d = parse("15mB")

    def testScientific(self):
        sci = Memory.toScientific

        x = 2.2 * 1024 ** 3
        (mant, exp) = sci(x)
        assert_equal(mant, 2.2)
        assert_equal(exp, 3)

        x = 5.34 * 1e16
        (mant, exp) = sci(x, base=10, explimit=100)
        assert_equal(mant, 5.34)
        assert_equal(exp, 16)

        x = 17.2
        (mant, exp) = sci(x, base=100)
        assert_equal(mant, x)
        assert_equal(exp, 0)

        x = 223 * 1e3
        (mant, exp) = sci(x, base=10, expstep=3)
        assert_equal(mant, 223)
        assert_equal(exp, 3)
