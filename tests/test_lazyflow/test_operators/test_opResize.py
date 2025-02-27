import math
from unittest import mock

import numpy
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


def test_resize_handles_blocks(graph):
    arr = numpy.indices((8, 8)).sum(0)
    data = vigra.taggedView(arr, "yx").astype(numpy.float64)
    scaling_target_shape = (7, 7)
    scaling_block_shape = (2, 3)  # Tiny blocks to exacerbate rounding and halo errors
    expected_n_blocks = math.ceil(scaling_target_shape[0] / scaling_block_shape[0]) * math.ceil(
        scaling_target_shape[1] / scaling_block_shape[1]
    )

    op = OpResize(graph=graph)
    op.RawImage.setValue(data)
    op.TargetShape.setValue(scaling_target_shape)

    split_op = OpSplitRequestsBlockwise(True, graph=graph)
    split_op.Input.connect(op.ResizedImage)
    split_op.BlockShape.setValue(scaling_block_shape)

    with mock.patch.object(OpResize, "execute", wraps=op.execute) as mock_execute:
        op_resized_block = split_op.Output[:].wait()
        assert mock_execute.call_count == expected_n_blocks, "blocks not split as expected"

    sk_resized = sk_resize(data, scaling_target_shape, anti_aliasing=True, preserve_range=True)
    op_resized = op.ResizedImage[:].wait()
    diff = op_resized - sk_resized
    diff_block = op_resized_block - sk_resized
    import tifffile

    tifffile.imwrite(f"C:/Users/root/Code/ilastik-group/sample-data/1orig.tif", data)
    tifffile.imwrite(f"C:/Users/root/Code/ilastik-group/sample-data/2skscaled.tif", sk_resized)
    tifffile.imwrite(f"C:/Users/root/Code/ilastik-group/sample-data/3opscaled.tif", op_resized)
    tifffile.imwrite(f"C:/Users/root/Code/ilastik-group/sample-data/4opblockscaled.tif", op_resized_block)
    tifffile.imwrite(f"C:/Users/root/Code/ilastik-group/sample-data/5diff-sk-op.tif", diff)
    tifffile.imwrite(f"C:/Users/root/Code/ilastik-group/sample-data/6diff-sk-opblock.tif", diff_block)
    numpy.testing.assert_allclose(op_resized, sk_resized, rtol=0.06)  # Higher tolerance due to different antialiasing
    numpy.testing.assert_allclose(
        op_resized_block, op_resized, rtol=0.01
    )  # Lower tolerance for block-splitting artifacts


def test_anisotropic_scaling(graph):
    pass
