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

    def test_agglomerate_labels_2d(self):
        from ilastik.workflows.carving.carvingTools import parallel_watershed, agglomerate_labels
        shape = (200,) * 2
        x = numpy.random.rand(*shape).astype('float32')
        over_seg, max_id1 = parallel_watershed(x, max_workers=4, block_shape=[50, 50],
                                               halo=[10, 10])

        seg = agglomerate_labels(x, over_seg, max_workers=4, reduce_to=.8)
        max_id2 = seg.max()
        assert not numpy.allclose(seg, 0), "Expect agglomerated labels to not be empty"
        assert max_id2 < max_id1,\
            f"Expect number of labels after {max_id2} to be less than before {max_id1} agglomeration"

    def test_agglomerate_labels_3d(self):
        from ilastik.workflows.carving.carvingTools import parallel_watershed, agglomerate_labels
        shape = (100,) * 3
        x = numpy.random.rand(*shape).astype('float32')
        over_seg, max_id1 = parallel_watershed(x, max_workers=4, block_shape=[50, 50, 50],
                                               halo=[10, 10, 10])

        seg = agglomerate_labels(x, over_seg, max_workers=4, reduce_to=.8)
        max_id2 = seg.max()
        assert not numpy.allclose(seg, 0), "Expect agglomerated labels to not be empty"
        assert max_id2 < max_id1,\
            f"Expect number of labels after {max_id2} to be less than before {max_id1} agglomeration"

    def test_agglomerate_and_watershed(self):
        from ilastik.workflows.carving.carvingTools import watershed_and_agglomerate
        shape = (400,) * 2
        x = numpy.random.rand(*shape).astype('float32')
        seg = watershed_and_agglomerate(x, max_workers=4)
        # we check that there is a reasonable number of unique ids
        ids = numpy.unique(seg)
        assert len(ids) > 5, f"Expected non trivial number of unique ids, got {len(ids)}"
        assert ids[0] == 1, f"Expected ids to start at 1, got {ids[0]}"


if __name__ == '__main__':
    unittest.main()
