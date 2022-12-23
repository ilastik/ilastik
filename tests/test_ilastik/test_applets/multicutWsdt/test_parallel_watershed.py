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

    blocking = get_blocking(data, block_shape, roi=None)
    running_max = 1
    for block_index in range(blocking.numberOfBlocks):
        block = blocking.getBlockWithHalo(blockIndex=block_index, halo=halo)
        inner_slicing = roiToSlice(block.innerBlock.begin, block.innerBlock.end)

        block_data = ws[inner_slicing]
        assert block_data.min() == running_max
        running_max = block_data.max() + 1
