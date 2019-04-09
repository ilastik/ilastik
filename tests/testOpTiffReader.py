from builtins import object
import tempfile
import shutil
import contextlib

import numpy
from numpy.testing import assert_array_equal
import vigra

from lazyflow.graph import Graph
from lazyflow.operators.ioOperators import OpTiffReader


@contextlib.contextmanager
def tempdir():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d)


class TestOpTiffReader(object):
    def test_2d(self):
        data = numpy.random.randint(0, 255, (100, 200, 3)).astype(numpy.uint8)
        with tempdir() as d:
            tiff_path = d + "/test-2d.tiff"
            vigra.impex.writeImage(vigra.taggedView(data, "yxc"), tiff_path, dtype="NATIVE", mode="w")

            op = OpTiffReader(graph=Graph())
            op.Filepath.setValue(tiff_path)
            assert op.Output.ready()
            assert (op.Output[50:100, 50:150].wait() == data[50:100, 50:150]).all()

    def test_3d(self):
        data = numpy.random.randint(0, 255, (50, 100, 200, 3)).astype(numpy.uint8)
        with tempdir() as d:
            tiff_path = d + "/test-3d.tiff"
            for z_slice in data:
                vigra.impex.writeImage(vigra.taggedView(z_slice, "yxc"), tiff_path, dtype="NATIVE", mode="a")

            op = OpTiffReader(graph=Graph())
            op.Filepath.setValue(tiff_path)
            assert op.Output.ready()
            assert (op.Output[20:30, 50:100, 50:150].wait() == data[20:30, 50:100, 50:150]).all()

    def test_3d_with_compression(self):
        """
        This tests that we can read a compressed (LZW) TIFF file.

        Note: It would be nice to test JPEG compression here, but strangely when vigra
        writes a JPEG-compressed TIFF, it is somehow messed up.  The image has two image
        'series' in it, so the thing seems to have twice as many planes as it should.
        Furthermore, vigra doesn't seem to read it back correctly, or maybe I'm missing something...
        """
        data = numpy.random.randint(0, 255, (50, 100, 200, 3)).astype(numpy.uint8)
        with tempdir() as d:
            tiff_path = d + "/test-3d.tiff"
            for z_slice in data:
                vigra.impex.writeImage(
                    vigra.taggedView(z_slice, "yxc"), tiff_path, dtype="NATIVE", compression="LZW", mode="a"
                )

            op = OpTiffReader(graph=Graph())
            op.Filepath.setValue(tiff_path)
            assert op.Output.ready()
            assert (op.Output[20:30, 50:100, 50:150].wait() == data[20:30, 50:100, 50:150]).all()

    def test_unknown_axes_tags(self):
        """
        This test is related to https://github.com/ilastik/ilastik/issues/1487

        Here, we generate a 3D tiff file with scikit-learn and try to read it
        """
        import tifffile
        from distutils import version

        # TODO(Dominik) remove version checking once tifffile dependency is fixed
        # ilastik tiffile version >= 2000.0.0
        # latest tifffile version is 0.13.0 right now
        tifffile_version_ilastik_ref = version.StrictVersion("2000.0.0")
        tifffile_version_ref = version.StrictVersion("0.7.0")
        tifffile_version = version.StrictVersion(tifffile.__version__)

        testshapes = [((10, 20), "yx"), ((10, 20, 30), "zyx"), ((10, 20, 30, 3), "zyxc"), ((5, 10, 20, 30, 3), "tzyxc")]

        with tempdir() as d:
            for test_shape, test_axes in testshapes:
                data = numpy.random.randint(0, 256, test_shape).astype(numpy.uint8)
                tiff_path = "{}/myfile_{}.tiff".format(d, test_axes)
                # TODO(Dominik) remove version checking once dependencies for
                # skimage are >= 0.13.0 for all flavours of ilastik
                if (tifffile_version > tifffile_version_ilastik_ref) or (tifffile_version < tifffile_version_ref):
                    tifffile.imsave(tiff_path, data)
                else:
                    tifffile.imsave(tiff_path, data, metadata={"axes": "QQQ"})
                op = OpTiffReader(graph=Graph())
                op.Filepath.setValue(tiff_path)
                assert op.Output.ready()
                assert_array_equal(data, op.Output[:].wait())
                assert op.Output.meta.axistags == vigra.defaultAxistags(test_axes)

    def test_lzw_compressed_file(self):
        """
        This test is loosely related to
          https://github.com/ilastik/ilastik/issues/1415

        Tests whether lzw compressed tiff files can be read.
        """
        import os

        basepath = os.path.split(__file__)[0]
        compressed_tiff_file = "{}/data/inputdata/compressed_lzw.tiff".format(basepath)
        # generate checker-board, as in the file
        data = numpy.zeros((10, 20, 3)).astype(numpy.uint8)
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


if __name__ == "__main__":
    import sys
    import nose

    sys.argv.append("--nocapture")  # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture")  # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
