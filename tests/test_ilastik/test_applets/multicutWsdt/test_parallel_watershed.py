import numpy
import pytest

from elf.parallel.common import get_blocking
from lazyflow.roi import roiToSlice

from ilastik.applets.wsdt.opWsdt import parallel_watershed


@pytest.fixture
def data():
    data = numpy.zeros((64, 64, 64), dtype=numpy.float32)
    # fmt: off
    data[ 0,  0, 0] = 0.7
    data[ 0, -1, 0] = 0.7
    data[-1,  0, 0] = 0.7
    data[-1, -1, 0] = 0.7
    # fmt: on
    return data


def test_parallel_watershed_consistency(data):
    block_shape = (32, 32, 32)
    halo = [10, 10, 10]

    ws, max_label = parallel_watershed(
        data=data,
        threshold=0.5,
        sigma_seeds=0.7,
        sigma_weights=0.7,
        minsize=1,
        alpha=0.9,
        pixel_pitch=None,
        non_max_suppression=False,
        block_shape=block_shape,
        halo=halo,
        max_workers=None,
    )

    assert max_label == 8
    assert ws.min() == 1

    blocking = get_blocking(data, block_shape, roi=None, n_threads=2)
    running_max = 1
    for block_index in range(blocking.numberOfBlocks):
        block = blocking.getBlockWithHalo(blockIndex=block_index, halo=halo)
        inner_slicing = roiToSlice(block.innerBlock.begin, block.innerBlock.end)

        block_data = ws[inner_slicing]
        assert block_data.min() == running_max
        running_max = block_data.max() + 1


def test_parallel_watershed_small_edge_blocks():
    """Regression test for #3153: segfault when edge blocks are very small.

    With a dataset of shape 129x129x129 and default block_shape=128, the last
    block along each axis has only 1 voxel inner + 10 halo = 11 voxels. With a
    large sigma, fastfilters.gaussianSmoothing would segfault on such small blocks.
    The fix extends the outer block to a minimum size.
    """
    # 129^3 -> last block is only 1 voxel, with halo=10 the outer block is 11 voxels
    data = numpy.random.rand(129, 129, 129).astype(numpy.float32)
    # Use a sigma large enough to cause issues with small blocks
    sigma = 5.0

    ws, max_label = parallel_watershed(
        data=data,
        threshold=0.5,
        sigma_seeds=sigma,
        sigma_weights=sigma,
        minsize=1,
        alpha=0.9,
        pixel_pitch=None,
        non_max_suppression=False,
        block_shape=None,  # default 128^3
        halo=None,  # default [10, 10, 10]
        max_workers=1,
    )

    assert max_label > 0
    assert ws.min() == 1
    assert ws.shape == data.shape
