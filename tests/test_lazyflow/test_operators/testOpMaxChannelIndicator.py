import pytest
import numpy
import vigra

from lazyflow.operators import OpArrayPiper, OpMaxChannelIndicatorOperator
from lazyflow.roi import InvalidRoiException
from lazyflow.utility import Pipeline


def test_OpMaxChannelIndicatorOperator_all_zeros(graph):
    """Special case for all zeros in probability maps"""
    data = vigra.VigraArray(numpy.zeros((1, 3, 5, 7, 2)), axistags=vigra.defaultAxistags("tzyxc"))

    # automatically connects op1.Output to op2.Input ...
    with Pipeline(graph=graph) as pipe_line:
        pipe_line.add(OpArrayPiper, Input=data)
        pipe_line.add(OpMaxChannelIndicatorOperator)

        for c in range(data.channels):
            assert not numpy.any(pipe_line[-1].Output[..., c].wait())


def test_OpMaxChannelIndicatorOperator(graph):
    data = vigra.VigraArray(numpy.zeros((1, 3, 5, 7, 2)), axistags=vigra.defaultAxistags("tzyxc"))

    data[:, :, :, ::2, 0] = 1
    data[:, :, :, 1::2, 1] = 1

    expected = data == 1

    # automatically connects op1.Output to op2.Input ...
    with Pipeline(graph=graph) as pipe_line:
        pipe_line.add(OpArrayPiper, Input=data)
        pipe_line.add(OpMaxChannelIndicatorOperator)

        for c in range(data.channels):
            numpy.testing.assert_array_equal(pipe_line[-1].Output[..., c].wait(), expected[..., c, None])


def test_OpMaxChannelIndicatorOperator_tied_pixels(graph):
    data = vigra.VigraArray(numpy.zeros((1, 3, 5, 7, 2)), axistags=vigra.defaultAxistags("tzyxc"))

    data[..., 0] = 1
    data[:, :, 0:2, 0:2, :] = 0.5

    # for tied pixels we expect the first occurrence to "win"
    expected = numpy.zeros_like(data)
    expected[..., 0] = 1

    # automatically connects op1.Output to op2.Input ...
    with Pipeline(graph=graph) as pipe_line:
        pipe_line.add(OpArrayPiper, Input=data)
        pipe_line.add(OpMaxChannelIndicatorOperator)

        for c in range(data.channels):
            numpy.testing.assert_array_equal(pipe_line[-1].Output[..., c].wait(), expected[..., c, None])


def test_OpMaxChannelIndicatorOperator_unexpected_roi_raises(graph):
    data = vigra.VigraArray(numpy.zeros((1, 3, 5, 7, 2)), axistags=vigra.defaultAxistags("tzyxc"))

    with pytest.raises(InvalidRoiException):
        # automatically connects op1.Output to op2.Input ...
        with Pipeline(graph=graph) as pipe_line:
            pipe_line.add(OpArrayPiper, Input=data)
            pipe_line.add(OpMaxChannelIndicatorOperator)
            pipe_line[-1].Output[()].wait()
