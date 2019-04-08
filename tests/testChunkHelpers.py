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
from lazyflow.utility.chunkHelpers import chooseChunkShape
from numpy.testing import assert_array_equal


class TestChunkHelpers(unittest.TestCase):
    def setup_method(self, method):
        pass

    def testChooseChunkShape(self):
        a = (15,)
        b = chooseChunkShape(a, 3)
        assert_array_equal(b, (3,))

        a = (20, 50)
        b = chooseChunkShape(a, 10)
        assert_array_equal(b, (2, 5))

        a = (20, 50)
        b = chooseChunkShape(a, 3000)
        assert_array_equal(b, (20, 50))

        a = (17, 33)  # roughly 1:2
        b = chooseChunkShape(a, 3)
        assert_array_equal(b, (1, 2))
