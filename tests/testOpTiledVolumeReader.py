from builtins import object
import numpy
import h5py

from lazyflow.graph import Graph
from lazyflow.operators.ioOperators import OpTiledVolumeReader, OpCachedTiledVolumeReader
from lazyflow.utility import PathComponents
from lazyflow.roi import roiToSlice

# We use the SAME data setup as in the test for TiledVolume
import testTiledVolume

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
        op.tiled_volume.TEST_MODE = True

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
        op.tiled_volume.TEST_MODE = True

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
        op._opReader.tiled_volume.TEST_MODE = True

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


if __name__ == "__main__":
    # Logging is OFF by default when running from command-line nose, i.e.:
    # nosetests thisFile.py)
    # When running this file directly, use the logging configuration below.

    import sys

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))

    # Logging for this test
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    # logging for testTiledVolume, which provides the data setup
    testTiledVolume_logger = logging.getLogger("testTiledVolume")
    testTiledVolume_logger.addHandler(handler)
    testTiledVolume_logger.setLevel(logging.ERROR)
    testTiledVolume.ENABLE_SERVER_LOGGING = False

    # requests module logging
    requests_logger = logging.getLogger("requests")
    requests_logger.addHandler(handler)
    requests_logger.setLevel(logging.WARN)

    # tiledVolume logging
    tiledVolumeLogger = logging.getLogger("lazyflow.utility.io_util.tiledVolume")
    tiledVolumeLogger.addHandler(handler)
    tiledVolumeLogger.setLevel(logging.ERROR)

    import nose

    sys.argv.append("--nocapture")  # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture")  # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)
    if not ret:
        sys.exit(1)
