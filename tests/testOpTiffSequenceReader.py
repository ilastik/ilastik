import contextlib
import tempfile
import shutil

import numpy

from lazyflow.graph import Graph
from lazyflow.operators.ioOperators import OpTiffSequenceReader
import vigra


@contextlib.contextmanager
def tempdir():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d)


class TestOpTiffReader(object):
    def test_2d_along_z(self):
        data = numpy.random.randint(0, 255, (20, 100, 200, 3)).astype(numpy.uint8)
        expected_axistags = vigra.AxisTags(
            [
                vigra.AxisInfo("z", typeFlags=vigra.AxisType.Space),
                vigra.AxisInfo("y", typeFlags=vigra.AxisType.Space),
                vigra.AxisInfo("x", typeFlags=vigra.AxisType.Space),
                vigra.AxisInfo("c", typeFlags=vigra.AxisType.Channels),
            ]
        )

        with tempdir() as d:
            tiff_path = d + "/test-2d-{slice_index:02d}.tiff"
            tiff_glob_path = d + "/test-2d-*.tiff"
            for slice_index, z_slice in enumerate(data):
                vigra.impex.writeImage(
                    vigra.taggedView(z_slice, "yxc"),
                    tiff_path.format(slice_index=slice_index),
                    dtype="NATIVE",
                    mode="w",
                )

            op = OpTiffSequenceReader(graph=Graph())
            op.SequenceAxis.setValue("z")
            op.GlobString.setValue(tiff_glob_path)
            assert op.Output.ready()
            assert op.Output.meta.axistags == expected_axistags
            assert (op.Output[5:10, 50:100, 100:150].wait() == data[5:10, 50:100, 100:150]).all()

    def test_2d_along_t(self):
        data = numpy.random.randint(0, 255, (20, 100, 200, 3)).astype(numpy.uint8)
        expected_axistags = vigra.AxisTags(
            [
                vigra.AxisInfo("t", typeFlags=vigra.AxisType.Time),
                vigra.AxisInfo("y", typeFlags=vigra.AxisType.Space),
                vigra.AxisInfo("x", typeFlags=vigra.AxisType.Space),
                vigra.AxisInfo("c", typeFlags=vigra.AxisType.Channels),
            ]
        )

        with tempdir() as d:
            tiff_path = d + "/test-2d-{slice_index:02d}.tiff"
            tiff_glob_path = d + "/test-2d-*.tiff"
            for slice_index, t_slice in enumerate(data):
                vigra.impex.writeImage(
                    vigra.taggedView(t_slice, "yxc"),
                    tiff_path.format(slice_index=slice_index),
                    dtype="NATIVE",
                    mode="w",
                )

            op = OpTiffSequenceReader(graph=Graph())
            op.SequenceAxis.setValue("t")
            op.GlobString.setValue(tiff_glob_path)
            assert op.Output.ready()
            assert op.Output.meta.axistags == expected_axistags
            assert (op.Output[5:10, 50:100, 100:150].wait() == data[5:10, 50:100, 100:150]).all()


if __name__ == "__main__":
    import sys
    import nose

    sys.argv.append("--nocapture")  # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture")  # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
