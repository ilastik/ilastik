from unittest import mock

import numpy
import vigra
from skimage.transform import resize as sk_resize

from lazyflow.operators.opResize import OpResize
from lazyflow.operators.opSplitRequestsBlockwise import OpSplitRequestsBlockwise


def test_resize_matches_skimage(graph):
    arr = numpy.random.randint(0, 256, (10, 10, 10), dtype="uint8")
    data = vigra.taggedView(arr, "zyx")

    op = OpResize(graph=graph)
    op.RawImage.setValue(data)
    op.TargetShape.setValue((5, 5, 5))

    op_resized = op.ResizedImage[:].wait()
    sk_resized = sk_resize(data, (5, 5, 5), anti_aliasing=True, preserve_range=True).astype(numpy.uint8)

    numpy.testing.assert_allclose(op_resized, sk_resized)


def test_resize_handles_blocks(graph):
    # arr = numpy.random.randint(0, 256, (50, 50), dtype="uint8")
    arr = numpy.indices((50, 50)).sum(0)
    tolerance = 2  # Specific to the indices data; would need to adjust for random data
    data = vigra.taggedView(arr, "yx")

    op = OpResize(graph=graph)
    op.RawImage.setValue(data)
    op.TargetShape.setValue((17, 17))

    split_op = OpSplitRequestsBlockwise(True, graph=graph)
    split_op.Input.connect(op.ResizedImage)
    split_op.BlockShape.setValue((5, 5))  # Tiny blocks to exacerbate rounding and halo errors

    with mock.patch.object(OpResize, "execute", wraps=op.execute) as mock_execute:
        op_resized = split_op.Output[:].wait()
        assert mock_execute.call_count == 16, "splitting into 16 blocks not working"

    sk_resized = sk_resize(data, (17, 17), anti_aliasing=True, preserve_range=True).astype(numpy.uint8)
    numpy.testing.assert_allclose(op_resized, sk_resized, atol=tolerance)
