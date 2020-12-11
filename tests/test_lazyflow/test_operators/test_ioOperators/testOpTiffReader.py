import numpy
from numpy.testing import assert_array_equal
import pytest
import vigra

from lazyflow.graph import Graph
from lazyflow.operators.ioOperators import OpTiffReader


class TestOpTiffReader:
    def test_2d(self, tmp_path):
        data = numpy.random.randint(0, 255, (100, 200, 3), dtype="uint8")

        tiff_path = str(tmp_path / "test-2d.tiff")
        vigra.impex.writeImage(vigra.taggedView(data, "yxc"), tiff_path, dtype="NATIVE", mode="w")

        op = OpTiffReader(graph=Graph())
        op.Filepath.setValue(tiff_path)
        assert op.Output.ready()
        assert (op.Output[50:100, 50:150].wait() == data[50:100, 50:150]).all()

    def test_3d(self, tmp_path):
        data = numpy.random.randint(0, 255, (50, 100, 200, 3)).astype(numpy.uint8)
        tiff_path = str(tmp_path / "test-3d.tiff")
        for z_slice in data:
            vigra.impex.writeImage(vigra.taggedView(z_slice, "yxc"), tiff_path, dtype="NATIVE", mode="a")

        op = OpTiffReader(graph=Graph())
        op.Filepath.setValue(tiff_path)
        assert op.Output.ready()
        assert (op.Output[20:30, 50:100, 50:150].wait() == data[20:30, 50:100, 50:150]).all()

    def test_3d_with_compression(self, tmp_path):
        """
        This tests that we can read a compressed (LZW) TIFF file.

        Note: It would be nice to test JPEG compression here, but strangely when vigra
        writes a JPEG-compressed TIFF, it is somehow messed up.  The image has two image
        'series' in it, so the thing seems to have twice as many planes as it should.
        Furthermore, vigra doesn't seem to read it back correctly, or maybe I'm missing something...
        """
        data = numpy.random.randint(0, 255, (50, 100, 200, 3), dtype="uint8")

        tiff_path = str(tmp_path / "test-3d.tiff")
        for z_slice in data:
            vigra.impex.writeImage(
                vigra.taggedView(z_slice, "yxc"), tiff_path, dtype="NATIVE", compression="LZW", mode="a"
            )

        op = OpTiffReader(graph=Graph())
        op.Filepath.setValue(tiff_path)
        assert op.Output.ready()
        assert (op.Output[20:30, 50:100, 50:150].wait() == data[20:30, 50:100, 50:150]).all()

    @pytest.mark.parametrize(
        "test_shape,axisorder",
        [((10, 20), "yx"), ((10, 20, 30), "zyx"), ((10, 20, 30, 3), "zyxc"), ((5, 10, 20, 30, 3), "tzyxc")],
    )
    def test_unknown_axes_tags(self, test_shape, axisorder, tmp_path):
        """
        This test is related to https://github.com/ilastik/ilastik/issues/1487

        Here, we generate a 3D tiff file with scikit-learn and try to read it
        """
        import tifffile

        data = numpy.random.randint(0, 256, test_shape, dtype="uint8")
        tiff_path = str(tmp_path / f"myfile_{axisorder}.tiff")
        tifffile.imsave(tiff_path, data)
        op = OpTiffReader(graph=Graph())
        op.Filepath.setValue(tiff_path)
        assert op.Output.ready()
        assert_array_equal(data, op.Output[:].wait())
        assert op.Output.meta.axistags == vigra.defaultAxistags(axisorder)

    def test_lzw_compressed_file(self, inputdata_dir):
        """
        This test is loosely related to
          https://github.com/ilastik/ilastik/issues/1415

        Tests whether lzw compressed tiff files can be read.
        """
        compressed_tiff_file = f"{inputdata_dir}/compressed_lzw.tiff"
        # generate checker-board, as in the file
        data = numpy.zeros((10, 20, 3), dtype="uint8")
        for i in range(data.shape[0]):
            if i % 2 == 0:
                data[i, 1::2, :] = 255
            else:
                data[i, 0::2, :] = 255

        op = OpTiffReader(graph=Graph())
        op.Filepath.setValue(compressed_tiff_file)
        assert op.Output.ready()
        assert op.Output.meta.shape == data.shape
        assert_array_equal(data, op.Output[:].wait())
