from __future__ import print_function
from unittest import TestCase

from lazyflow.utility import helpers


class TestDefaultAxisOrdering(TestCase):
    """Class for testing the default axis ordering"""

    def testValidShapes(self):
        testshapes = [((10, 20), "yx"), ((10, 20, 30), "zyx"), ((10, 20, 30, 3), "zyxc"), ((5, 10, 20, 30, 3), "tzyxc")]
        for shape, expected_axes_string in testshapes:
            default_axes = helpers.get_default_axisordering(shape)
            assert default_axes == expected_axes_string

    def testInvalidShapes(self):
        testshapes = [tuple(), tuple([1]), (1, 2, 3, 4, 5, 6)]
        for shape in testshapes:
            print(shape)
            self.assertRaises(ValueError, helpers.get_default_axisordering, shape)
