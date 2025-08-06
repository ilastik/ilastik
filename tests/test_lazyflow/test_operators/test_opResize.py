###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2025, the ilastik developers
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
#          http://ilastik.org/license/
###############################################################################
from unittest import mock

import numpy
import pytest
import vigra
from skimage.transform import resize as sk_resize

from lazyflow.operators.opResize import OpResize
from lazyflow.operators.opSplitRequestsBlockwise import OpSplitRequestsBlockwise
from lazyflow.utility.data_semantics import ImageTypes


def test_resize_matches_skimage(graph):
    # OpResize implementation uses @haesleinhuepf antialiasing sigmas
    # (cf BioImageAnalysisNotebooks downscaling and denoising):
    # i.e. antialiasing_sigmas = np.array([f / 4 for f in downscaling_factors])
    # skimage.transform.resize uses antialiasing_sigmas = np.maximum(0, (downscaling_factors - 1) / 2)
    # The differences should be negligible for an int image.
    arr = numpy.random.randint(0, 256, (10, 10, 10), dtype="uint8")
    data = vigra.taggedView(arr, "zyx")

    op = OpResize(graph=graph)
    op.RawImage.setValue(data)
    op.TargetShape.setValue((5, 5, 5))

    op_resized = op.ResizedImage[:].wait()
    sk_resized = sk_resize(data, (5, 5, 5), anti_aliasing=True, preserve_range=True).astype(numpy.uint8)

    numpy.testing.assert_array_equal(op_resized, sk_resized)


@pytest.mark.parametrize(
    "raw_shape,scaled_shape,axes,block_shape",
    [
        ((4, 160, 160, 160, 3), (4, 80, 80, 80, 3), "tzyxc", (1, 50, 50, 50, 3)),  # Realistic use case
        ((11, 11), (5, 5), "yx", (3, 3)),  # Tiny blocks
        ((9, 9), (8, 8), "yx", (1, 1)),  # Pixelwise
        ((15, 10), (9, 3), "yx", (4, 6)),  # Anisotropic
        ((4, 5), (8, 6), "yx", (3, 3)),  # Upscaling
        ((11, 11), (11, 11), "yx", (4, 6)),  # Noop
        ((11, 7, 23), (6, 6, 6), "yzx", (5, 5, 5)),  # 3D and weird axes
        ((5, 11, 8, 23), (2, 8, 8, 8), "tzyx", (1, 5, 5, 5)),  # 4D (bad idea, but technically valid), 1:1 along y
        ((10, 10, 3), (5, 5, 3), "yxc", (3, 3, 2)),  # c allowed to be present but not scaled
    ],
)
def test_resize_handles_blocks(graph, raw_shape, scaled_shape, axes, block_shape):
    arr = numpy.indices(raw_shape).sum(0)
    data = vigra.taggedView(arr, axes).astype(numpy.float64)
    expected_n_blocks = numpy.prod([numpy.ceil(scaled / block) for scaled, block in zip(scaled_shape, block_shape)])
    if raw_shape == scaled_shape:
        # When not actually scaling, the op should directly connect output to input,
        # resulting in 0 calls to its own execute.
        expected_n_blocks = 0

    op = OpResize(graph=graph)
    op.RawImage.setValue(data)
    op.TargetShape.setValue(scaled_shape)

    split_op = OpSplitRequestsBlockwise(True, graph=graph)
    split_op.Input.connect(op.ResizedImage)
    split_op.BlockShape.setValue(block_shape)

    with mock.patch.object(OpResize, "execute", wraps=op.execute) as mock_execute:
        op_resized_block = split_op.Output[:].wait()
        assert mock_execute.call_count == expected_n_blocks, "blocks not split as expected"

    sk_resized = sk_resize(data, scaled_shape, anti_aliasing=True, preserve_range=True)
    op_resized = op.ResizedImage[:].wait()

    # Different antialiasing, see test_resize_matches_skimage - with float image need some tolerance
    numpy.testing.assert_allclose(op_resized, sk_resized, rtol=0.07)
    numpy.testing.assert_allclose(op_resized_block, op_resized, rtol=1e-15)  # Block-splitting artifacts not tolerated


def test_interpolation_order(graph):
    """1 (LINEAR) is default, test 0 (NEAREST)."""
    arr = numpy.indices((25, 25)).sum(0)
    data = vigra.taggedView(arr, "yx")

    op = OpResize(graph=graph)
    op.RawImage.setValue(data)
    op.TargetShape.setValue((5, 5))
    op.InterpolationOrder.setValue(OpResize.Interpolation.NEAREST)

    op_resized = op.ResizedImage[:].wait()

    sk_resized = sk_resize(data, (5, 5), order=0, preserve_range=True).astype(numpy.uint8)

    numpy.testing.assert_array_equal(op_resized, sk_resized)


@pytest.mark.parametrize("image_type", ImageTypes)
def test_semantics_to_interpolation_covers_all_types(image_type: ImageTypes):
    assert (
        image_type in OpResize.semantics_to_interpolation
    ), f'specify appropriate interpolation order for "{image_type}" data semantics'


@pytest.mark.parametrize("order", OpResize.Interpolation)
def test_min_padding_exists_for_all_interpolations(order: OpResize.Interpolation):
    """
    This is mainly about halo required for upscaling. For downscaling, the antialiasing
    halo was always sufficiently large also for interpolation.
    Higher interpolation orders require more padding. For orders 0 and 1, the
    required padding was empirically determined.
    """
    assert (
        order in OpResize.required_min_padding
    ), f"specify required minimum pixel padding for interpolation of order {order}"


def test_raises_on_c_scaling(graph):
    arr = numpy.random.randint(0, 256, (10, 10, 3), dtype="uint8")
    data = vigra.taggedView(arr, "yxc")

    op = OpResize(graph=graph)
    op.RawImage.setValue(data)
    with pytest.raises(AssertionError):
        op.TargetShape.setValue((10, 10, 2))


def test_antialiasing_does_not_filter_across_channel(graph):
    arr = numpy.random.randint(0, 256, (10, 10, 3), dtype="uint8")
    arr[:, :, 1] = 1
    arr[:, :, 2] = 0
    data = vigra.taggedView(arr, "yxc")

    op = OpResize(graph=graph)
    op.RawImage.setValue(data)
    op.TargetShape.setValue((5, 5, 3))

    resized = op.ResizedImage[:].wait()

    numpy.testing.assert_array_equal(resized[:, :, 1], 1)
    numpy.testing.assert_array_equal(resized[:, :, 2], 0)
