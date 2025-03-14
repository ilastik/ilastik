import math
from unittest import mock

import numpy
import pytest
import vigra
from skimage.transform import resize as sk_resize

from lazyflow.operators.opResize import OpResize
from lazyflow.operators.opSplitRequestsBlockwise import OpSplitRequestsBlockwise


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
        ((11, 11), (5, 5), "yx", (3, 3)),  # Tiny blocks
        ((9, 9), (8, 8), "yx", (1, 1)),  # Pixelwise
        ((15, 10), (9, 3), "yx", (4, 6)),  # Anisotropic
    ],
)
def test_resize_handles_blocks(graph, raw_shape, scaled_shape, axes, block_shape):
    arr = numpy.indices(raw_shape).sum(0)
    data = vigra.taggedView(arr, axes).astype(numpy.float64)
    expected_n_blocks = math.ceil(scaled_shape[0] / block_shape[0]) * math.ceil(scaled_shape[1] / block_shape[1])

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
    numpy.testing.assert_allclose(op_resized, sk_resized, rtol=0.06)
    numpy.testing.assert_allclose(op_resized_block, op_resized)  # Block-splitting artifacts not tolerated


def test_resize_dask():
    import dask
    from dask.array import map_overlap
    from ngff_zarr.methods._itkwasm import _itkwasm_blur_and_downsample
    from ngff_zarr.methods._support import _compute_sigma
    from itkwasm_downsample import gaussian_kernel_radius
    import itkwasm
    import tifffile
    import numpy

    arr = numpy.indices((8, 8)).sum(0)
    scaling_block_shape = (2, 3)  # Tiny blocks to exacerbate rounding and halo errors
    shrink_factors = [8 / 7, 8 / 7]
    mockblock = itkwasm.image_from_array(numpy.ones(scaling_block_shape), is_vector=False)
    kernel_radius = gaussian_kernel_radius(size=mockblock.size, sigma=_compute_sigma(shrink_factors))
    dask_resized = map_overlap(
        _itkwasm_blur_and_downsample,
        dask.array.from_array(arr.astype(numpy.float64)),
        shrink_factors=shrink_factors,
        kernel_radius=kernel_radius,
        smoothing="gaussian",
        is_vector=False,
        dtype=arr.dtype,
        depth=dict(enumerate(numpy.flip(kernel_radius))),  # overlap is in tzyx
        boundary="nearest",
        trim=False,  # Overlapped region is trimmed in blur_and_downsample to output size
        chunks=scaling_block_shape,
    ).compute()
    tifffile.imwrite(f"C:/Users/root/Code/ilastik-group/sample-data/7ngffscaled.tif", dask_resized)


def test_anisotropic_scaling(graph):
    pass
