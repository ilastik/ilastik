from builtins import object
import numpy
import h5py

from lazyflow.graph import Graph
from lazyflow.operators.ioOperators import OpTiledVolumeReader, OpCachedTiledVolumeReader
from lazyflow.utility import PathComponents
from lazyflow.roi import roiToSlice

# We use the SAME data setup as in the test for TiledVolume
from tests.test_lazyflow.test_utility.test_io_util import testTiledVolume

import logging

logger = logging.getLogger(__name__)


class TestOpTiledVolumeReader(object):
    @classmethod
    def setup_class(cls):
        cls.data_setup = testTiledVolume.DataSetup()
        cls.data_setup.setup()

    @classmethod
    def teardown_class(cls):
        cls.data_setup.teardown()

    def testBasic(self):
        graph = Graph()
        op = OpTiledVolumeReader(graph=graph)
        op.DescriptionFilePath.setValue(self.data_setup.VOLUME_DESCRIPTION_FILE)

        roi = numpy.array([(10, 150, 100), (30, 550, 550)])
        result_out = op.Output(*roi).wait()

        # We expect a channel dimension to be added automatically...
        assert (result_out.shape == roi[1] - roi[0]).all()

        ref_path_comp = PathComponents(self.data_setup.REFERENCE_VOL_PATH)
        with h5py.File(ref_path_comp.externalPath, "r") as f:
            ref_data = f[ref_path_comp.internalPath][:]

        expected = ref_data[roiToSlice(*roi)]

        # numpy.save('/tmp/expected.npy', expected)
        # numpy.save('/tmp/result_out.npy', result_out)

        # We can't expect the pixels to match exactly because compression was used to create the tiles...
        assert (expected == result_out).all()


class TestOpTiledVolumeReader_Transposed(object):
    @classmethod
    def setup_class(cls):
        cls.data_setup = testTiledVolume.DataSetup()
        cls.data_setup.setup()

    @classmethod
    def teardown_class(cls):
        cls.data_setup.teardown()

    def test(self):
        graph = Graph()
        op = OpTiledVolumeReader(graph=graph)
        op.DescriptionFilePath.setValue(self.data_setup.TRANSPOSED_VOLUME_DESCRIPTION_FILE)

        roi = numpy.array([(10, 150, 100), (30, 550, 550)])
        roi_t = numpy.array([tuple(reversed(roi[0])), tuple(reversed(roi[1]))])

        result_out_t = op.Output(*roi_t).wait()
        result_out = result_out_t.transpose()

        # We expect a channel dimension to be added automatically...
        assert (result_out_t.shape == roi_t[1] - roi_t[0]).all()

        ref_path_comp = PathComponents(self.data_setup.REFERENCE_VOL_PATH)
        with h5py.File(ref_path_comp.externalPath, "r") as f:
            ref_data = f[ref_path_comp.internalPath][:]

        expected = ref_data[roiToSlice(*roi)]

        # numpy.save('/tmp/expected.npy', expected)
        # numpy.save('/tmp/result_out.npy', result_out)

        # We can't expect the pixels to match exactly because compression was used to create the tiles...
        assert (expected == result_out).all()


class TestOpCachedTiledVolumeReader(object):
    @classmethod
    def setup_class(cls):
        cls.data_setup = testTiledVolume.DataSetup()
        cls.data_setup.setup()

    @classmethod
    def teardown_class(cls):
        cls.data_setup.teardown()

    def testBasic(self):
        graph = Graph()
        op = OpCachedTiledVolumeReader(graph=graph)
        op.DescriptionFilePath.setValue(self.data_setup.VOLUME_DESCRIPTION_FILE)

        roi = numpy.array([(10, 150, 100), (30, 550, 550)])
        cached_result_out = op.CachedOutput(*roi).wait()
        uncached_result_out = op.UncachedOutput(*roi).wait()
        specified_result_out = op.CachedOutput(*roi).wait()

        # We expect a channel dimension to be added automatically...
        assert (cached_result_out.shape == roi[1] - roi[0]).all()

        ref_path_comp = PathComponents(self.data_setup.REFERENCE_VOL_PATH)
        with h5py.File(ref_path_comp.externalPath, "r") as f:
            ref_data = f[ref_path_comp.internalPath][:]

        expected = ref_data[roiToSlice(*roi)]

        # numpy.save('/tmp/expected.npy', expected)
        # numpy.save('/tmp/result_out.npy', result_out)

        # We can't expect the pixels to match exactly because compression was used to create the tiles...
        assert (expected == cached_result_out).all()
        assert (expected == uncached_result_out).all()
        assert (expected == specified_result_out).all()
