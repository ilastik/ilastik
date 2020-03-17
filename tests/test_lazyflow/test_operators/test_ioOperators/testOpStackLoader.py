from builtins import range
from builtins import object

###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the Lesser GNU General Public License
# as published by the Free Software Foundation; either version 2.1
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# See the files LICENSE.lgpl2 and LICENSE.lgpl3 for full text of the
# GNU Lesser General Public License version 2.1 and 3 respectively.
# This information is also available on the ilastik web site at:
# 		   http://ilastik.org/license/
###############################################################################
import os
import shutil
import tempfile

import numpy
import vigra

from lazyflow.graph import Graph
from lazyflow.operators.ioOperators import OpStackLoader

# from lazyflow.operators.ioOperators import OpInputDataReader
import h5py


class TestOpStackLoader(object):
    def setup_method(self, method):
        self._tmp_dir = tempfile.mkdtemp()

    def teardown_method(self, method):
        shutil.rmtree(self._tmp_dir)

    def _prepare_data(self, name, shape, axes, stack_axis, stack_existing_channels=False):
        """
            Writes random data in a series of [multi-page] tiff files.
            'stack_existing_channels' can be used to stack the first and the
            last axis together. This is useful when testing to stack data with
            c > 1 along c.
        """
        if stack_axis in axes:
            assert len(shape) == len(axes)
            assert axes[0] == stack_axis
        else:
            assert len(shape) == len(axes) + 1

        file_base = os.path.join(self._tmp_dir, name)

        rand_data = numpy.random.random(shape)
        rand_data *= 256
        rand_data = rand_data.astype(numpy.uint8)
        rand_data = vigra.taggedView(rand_data, axes)

        nr_data_axes = len(axes.replace("c", "").replace(stack_axis, ""))
        if nr_data_axes < 3:
            for a in range(shape[0]):
                file_name = file_base + "_{:03}.tiff".format(a)
                vigra.impex.writeImage(rand_data[a, ...], file_name)
        else:
            for a in range(shape[0]):
                file_name = file_base + "_{:03}.tiff".format(a)
                for b in range(shape[1]):
                    vigra.impex.writeImage(rand_data[a, b, ...], file_name, mode="a")

        if stack_existing_channels:
            true_shape = tuple([shape[0] * shape[-1]] + [s for s in shape[1:-1]])
            true_data = numpy.empty(true_shape, dtype=numpy.uint8)
            for i in range(shape[0]):
                for j in range(shape[-1]):
                    true_data[i * shape[-1] + j] = rand_data[i, ..., j]

            rand_data = vigra.taggedView(true_data, "c" + axes[1:-1])

        return rand_data, file_base + "_*.tiff"

    def test_xyz(self):
        expected_volume, globstring = self._prepare_data("rand_3d", (11, 99, 98), "zyx", "z")

        graph = Graph()
        op = OpStackLoader(graph=graph)
        op.globstring.setValue(globstring)

        assert len(op.stack.meta.axistags) == 4
        assert op.stack.meta.getAxisKeys() == list("zyxc")
        assert op.stack.meta.dtype == expected_volume.dtype

        volume_from_stack = op.stack[:].wait()
        volume_from_stack = vigra.taggedView(volume_from_stack, "zyxc")
        volume_from_stack = volume_from_stack.withAxes(*"zyx")

        assert (volume_from_stack == expected_volume).all(), "3D Volume from stack did not match expected data."

    def test_xyz_stack_c(self):
        # expected_volume_zyxc, globstring = self._prepare_data_zyx_stack_c()
        expected_volume, globstring = self._prepare_data("rand_3d_stack_c", (2, 3, 5, 4), "czxy", "c")

        graph = Graph()
        op = OpStackLoader(graph=graph)
        op.SequenceAxis.setValue("c")
        op.globstring.setValue(globstring)

        assert len(op.stack.meta.axistags) == 4
        assert op.stack.meta.getAxisKeys() == list("czyx")
        assert op.stack.meta.dtype == expected_volume.dtype

        volume_from_stack = op.stack[:].wait()
        volume_from_stack = vigra.taggedView(volume_from_stack, "czyx")
        volume_from_stack = volume_from_stack.withAxes(*"czxy")

        assert (volume_from_stack == expected_volume).all(), "3D Volume stacked along c did not match expected data."

    def test_zyxc(self):
        expected_volume_zyxc, globstring = self._prepare_data("rand_3dc", (10, 50, 100, 3), "zyxc", "z")

        graph = Graph()
        op = OpStackLoader(graph=graph)
        op.globstring.setValue(globstring)

        assert len(op.stack.meta.axistags) == 4
        assert op.stack.meta.getAxisKeys() == list("zyxc")
        assert op.stack.meta.dtype == expected_volume_zyxc.dtype

        vol_from_stack_zyxc = op.stack[:].wait()
        vol_from_stack_zyxc = vigra.taggedView(vol_from_stack_zyxc, "zyxc")

        assert (
            vol_from_stack_zyxc == expected_volume_zyxc
        ).all(), "3D+c Volume from stack did not match expected data."

    def test_zyxc_stack_c(self):
        # Test to stack 3D data with channels along the channels.
        # For data preparation only the t axis is used to create a tiff series
        # of 3D+c data, the expected_volume is corrected to 'czyx' with the
        # flag 'stack_existing_channels=True'
        expected_volume, globstring = self._prepare_data(
            "rand_3dc_stack_c", (5, 22, 33, 44, 2), "tzyxc", "t", stack_existing_channels=True
        )

        graph = Graph()
        op = OpStackLoader(graph=graph)
        op.SequenceAxis.setValue("c")
        op.globstring.setValue(globstring)

        assert len(op.stack.meta.axistags) == 4
        assert op.stack.meta.getAxisKeys() == list("czyx")
        assert op.stack.meta.dtype == expected_volume.dtype

        volume_from_stack = op.stack[:].wait()
        volume_from_stack = vigra.taggedView(volume_from_stack, "czyx")

        assert (volume_from_stack == expected_volume).all(), "3D+c Volume stacked along c did not match expected data."

    def test_tzyx(self):
        expected_volume_tzyx, globstring = self._prepare_data("rand_4d", (5, 10, 100, 99), "tzyx", "t")

        graph = Graph()
        op = OpStackLoader(graph=graph)
        op.globstring.setValue(globstring)

        assert len(op.stack.meta.axistags) == 5
        assert op.stack.meta.getAxisKeys() == list("tzyxc")
        assert op.stack.meta.dtype == expected_volume_tzyx.dtype

        vol_from_stack_tzyxc = op.stack[:].wait()
        vol_from_stack_tzyxc = vigra.taggedView(vol_from_stack_tzyxc, "tzyxc")
        vol_from_stack_tzyx = vol_from_stack_tzyxc.withAxes(*"tzyx")

        assert (vol_from_stack_tzyx == expected_volume_tzyx).all(), "4D Volume from stack did not match expected data."

    def test_tzyxc(self):
        expected_volume_tzyxc, globstring = self._prepare_data("rand_4dc", (5, 10, 50, 100, 3), "tzyxc", "t")

        graph = Graph()
        op = OpStackLoader(graph=graph)
        op.globstring.setValue(globstring)

        assert len(op.stack.meta.axistags) == 5
        assert op.stack.meta.getAxisKeys() == list("tzyxc")
        assert op.stack.meta.dtype == expected_volume_tzyxc.dtype

        vol_from_stack_tzyxc = op.stack[:].wait()
        vol_from_stack_tzyxc = vigra.taggedView(vol_from_stack_tzyxc, "tzyxc")

        assert (
            vol_from_stack_tzyxc == expected_volume_tzyxc
        ).all(), "4D+c Volume from stack did not match expected data."

    def test_stack_pngs(self, inputdata_dir):
        graph = Graph()
        op = OpStackLoader(graph=graph)
        op.SequenceAxis.setValue("c")

        globstring = os.path.join(inputdata_dir, "3c[0-2].png")
        op.globstring.setValue(globstring)

        assert len(op.stack.meta.axistags) == 3
        assert op.stack.meta.getAxisKeys() == list("xyc")

        stack = op.stack[:].wait()

        gt_path = os.path.join(inputdata_dir, "3cRGB.h5")
        h5File = h5py.File(gt_path, "r")
        expected = h5File["data"]

        assert stack.dtype == expected.dtype
        assert stack.shape == expected.shape

        assert (stack == expected).all(), "stacked 2d images did not match expected data."


if __name__ == "__main__":
    import sys
    import nose

    # Don't steal stdout. Show it on the console as usual.
    sys.argv.append("--nocapture")
    # Don't set the logging level to DEBUG. Leave it alone.
    sys.argv.append("--nologcapture")
    ret = nose.run(defaultTest=__file__)
    if not ret:
        sys.exit(1)
