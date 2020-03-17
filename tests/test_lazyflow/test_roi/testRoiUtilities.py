from builtins import object
from unittest import TestCase

import numpy

from lazyflow.roi import (
    determineBlockShape,
    getIntersection,
    enlargeRoiForHalo,
    TinyVector,
    nonzero_bounding_box,
    containing_rois,
    getIntersectingBlocks,
)


class Test_determineBlockShape(object):
    def testBasic(self):
        max_shape = (1000, 1000, 1000, 1)
        block_shape = determineBlockShape(max_shape, 1e6)
        assert block_shape == (100, 100, 100, 1), "Got {}, expected (100,100,100,1)".format(block_shape)

    def testBasic2(self):
        max_shape = (1, 100, 5, 200, 3)
        block_shape = determineBlockShape(max_shape, 1000)
        assert block_shape == (1, 8, 5, 8, 3)

    def testSmallMax(self):
        # In this case, the target size is too large for the given max_shape
        # Therefore, block_shape == max_shape
        max_shape = (1, 2, 3, 2, 1)
        block_shape = determineBlockShape(max_shape, 1000)
        assert block_shape == max_shape

    def testInvalidMax(self):
        try:
            max_shape = (1, 2, 3, 2, 0)
            determineBlockShape(max_shape, 1000)
        except AssertionError:
            pass
        except Exception as e:
            assert False, "Wrong type of exception.  Expected AssertionError, but got {}".format(e)
        else:
            assert False, "Expected assertion in determineBlockShape() due to invalid inputs"


class Test_getIntersection(object):
    def testBasic(self):
        roiA = [(10, 10, 10), (20, 20, 20)]
        roiB = [(15, 16, 17), (25, 25, 25)]
        intersection = getIntersection(roiA, roiB)
        assert (numpy.array(intersection) == ([15, 16, 17], [20, 20, 20])).all()

    def testAssertNonIntersect(self):
        roiA = [(10, 10, 10), (20, 20, 20)]
        roiB = [(15, 26, 27), (16, 30, 30)]
        try:
            intersection = getIntersection(roiA, roiB)
        except AssertionError:
            pass
        else:
            assert False, "getIntersection() was supposed to assert because the parameters don't intersect!"

    def testNoAssertNonIntersect(self):
        roiA = [(10, 10, 10), (20, 20, 20)]
        roiB = [(15, 26, 27), (16, 30, 30)]
        intersection = getIntersection(roiA, roiB, assertIntersect=False)
        assert intersection is None, "Expected None because {} doesn't intersect with {}".format()


class TestEnlargeRoiForHalo(object):
    def testBasic(self):
        start = TinyVector([10, 100, 200, 300, 1])
        stop = TinyVector([11, 150, 300, 500, 3])
        image_shape = [20, 152, 500, 500, 10]

        sigma = 3.1
        window = 2
        enlarge_axes = (False, True, True, True, False)

        enlarged_start, enlarged_stop = enlargeRoiForHalo(start, stop, image_shape, sigma, window, enlarge_axes)

        full_halo_width = numpy.ceil(sigma * window)

        # Non-enlarged axes should remain the same
        assert (enlarged_start[[0, 4]] == (start[0], start[4])).all(), "{} == {}".format(
            enlarged_start[[0, 4]], (start[0], start[4])
        )
        assert (enlarged_stop[[0, 4]] == (stop[0], stop[4])).all(), "{} == {}".format(
            enlarged_stop[[0, 4]], (stop[0], stop[4])
        )

        # The start coord isn't close to the image border, so the halo should be full-sized on the start side
        assert (enlarged_start[1:4] == numpy.array(start)[1:4] - full_halo_width).all()

        # The stop coord is close to the image border in some dimensions,
        #  so some axes couldn't be expanded by the full halo width.
        assert enlarged_stop[1] == 152
        assert enlarged_stop[2] == stop[2] + full_halo_width
        assert enlarged_stop[3] == 500


class TestNonzeroBoundingBox(object):
    def testBasic(self):
        data = numpy.zeros((10, 100, 100), numpy.uint8)
        data[4, 30:40, 50:60] = 1
        data[7, 45:55, 30:35] = 255
        bb_roi = nonzero_bounding_box(data)
        assert isinstance(bb_roi, numpy.ndarray)
        assert (bb_roi == [[4, 30, 30], [8, 55, 60]]).all()

    def test_empty_data(self):
        data = numpy.zeros((10, 100, 100), numpy.uint8)
        bb_roi = nonzero_bounding_box(data)
        assert isinstance(bb_roi, numpy.ndarray)
        assert (bb_roi == [[0, 0, 0], [0, 0, 0]]).all()


class TestContainingRois(object):
    def testBasic(self):
        rois = [([0, 0, 0], [10, 10, 10]), ([5, 3, 2], [11, 12, 13]), ([4, 6, 4], [5, 9, 9])]

        result = containing_rois(rois, ([4, 7, 6], [5, 8, 8]))
        assert (result == [([0, 0, 0], [10, 10, 10]), ([4, 6, 4], [5, 9, 9])]).all()

    def testEmptyResult(self):
        rois = [([0, 0, 0], [10, 10, 10]), ([5, 3, 2], [11, 12, 13]), ([4, 6, 4], [5, 9, 9])]

        result = containing_rois(rois, ([100, 100, 100], [200, 200, 200]))
        assert result.shape == (0, 2, 3)

    def testEmptyInput(self):
        rois = []
        result = containing_rois(rois, ([100, 100, 100], [200, 200, 200]))
        assert result.shape == (0,)


class TestGetIntersectionBlocks(TestCase):
    def test_invalid_parameters(self):
        with self.assertRaises(AssertionError):
            getIntersectingBlocks((256, 256, 0, 2), ([0, 0, 0, 0], [256, 256, 256, 2]))

        with self.assertRaises(AssertionError):
            getIntersectingBlocks(numpy.array((256, 256, 0, 2)), ([0, 0, 0, 0], [256, 256, 256, 2]))


if __name__ == "__main__":
    # Run nose
    import sys
    import nose

    sys.argv.append("--nocapture")  # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture")  # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)
    if not ret:
        sys.exit(1)
