from builtins import object
import os
import tempfile
import shutil

import numpy
import vigra

from lazyflow.graph import Graph
from lazyflow.operators.ioOperators import OpImageReader


class TestOpImageReader_multipage(object):
    @classmethod
    def setup_class(cls):
        cls._tmpdir = tempfile.mkdtemp()
        cls._volume_file = os.path.join(cls._tmpdir, "test_volume.tif")

        cls._shape_zyx = (10, 100, 200)
        a = numpy.random.randint(0, 255, cls._shape_zyx).astype(numpy.uint8)
        a = vigra.taggedView(a, "zyx")
        for z_slice in a:
            vigra.impex.writeImage(z_slice, cls._volume_file, dtype="NATIVE", mode="a")

        cls._testdata = a

    @classmethod
    def teardown_class(cls):
        shutil.rmtree(cls._tmpdir)

    def test(self):
        op = OpImageReader(graph=Graph())
        op.Filename.setValue(self._volume_file)
        assert op.Image.meta.shape == self._shape_zyx + (1,), "Wrong output shape: {}".format(op.Image.meta.shape)
        assert op.Image.meta.getAxisKeys() == list("zyxc"), "Wrong output axistags: {}".format(op.Image.meta.axistags)

        assert (
            op.Image[3:5, 10:90, 150:200, :].wait() == self._testdata[3:5, 10:90, 150:200, None].view(numpy.ndarray)
        ).all()


class TestOpImageReader_2D(object):
    @classmethod
    def setup_class(cls):
        cls._tmpdir = tempfile.mkdtemp()
        cls._file = os.path.join(cls._tmpdir, "test_image.tif")

        cls._shape_yx = (100, 200)
        a = numpy.random.randint(0, 255, cls._shape_yx).astype(numpy.uint8)
        a = vigra.taggedView(a, "yx")
        vigra.impex.writeImage(a, cls._file, dtype="NATIVE", mode="w")

        cls._testdata = a

    @classmethod
    def teardown_class(cls):
        shutil.rmtree(cls._tmpdir)

    def test(self):
        op = OpImageReader(graph=Graph())
        op.Filename.setValue(self._file)
        assert op.Image.meta.shape == self._shape_yx + (1,), "Wrong output shape: {}".format(op.Image.meta.shape)
        assert op.Image.meta.getAxisKeys() == list("yxc"), "Wrong output axistags: {}".format(op.Image.meta.axistags)

        assert (op.Image[10:90, 50:60, :].wait() == self._testdata[10:90, 50:60, None].view(numpy.ndarray)).all()


if __name__ == "__main__":
    import sys
    import nose

    sys.argv.append("--nocapture")  # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture")  # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
