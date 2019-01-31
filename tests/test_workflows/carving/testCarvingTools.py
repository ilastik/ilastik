import unittest
import numpy


class TestCarvingTools(unittest.TestCase):

    def test_parallel_watershed_3d(self):
        from ilastik.workflows.carving.carvingTools import parallel_watershed
        shape = (200,) * 3
        x = numpy.random.rand(*shape).astype('float32')

        seg, max_id = parallel_watershed(x, max_workers=4)
        max_expected = seg.max()
        assert max_id == max_expected, f"Expect {max_expected} but got {max_id}"
        assert max_id > 1, f"Expect more than one segment in watershed result"
        # TODO test that labels in individual blocks are indeed different

    def test_parallel_watershed_2d(self):
        from ilastik.workflows.carving.carvingTools import parallel_watershed
        shape = (400,) * 2
        x = numpy.random.rand(*shape).astype('float32')

        seg, max_id = parallel_watershed(x, max_workers=4)
        max_expected = seg.max()
        assert max_id == max_expected, f"Expect {max_expected} but got {max_id}"
        assert max_id > 1, f"Expect more than one segment in watershed result"
        # TODO test that labels in individual blocks are indeed different


if __name__ == '__main__':
    unittest.main()
