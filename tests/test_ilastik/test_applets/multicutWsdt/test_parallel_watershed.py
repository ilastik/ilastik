import numpy
import pytest

from elf.parallel.common import get_blocking
from lazyflow.roi import roiToSlice

from ilastik.applets.wsdt.opWsdt import parallel_watershed, _adjust_block_slicings, _min_outer_size


def _mk_block(inner, outer, inner_local):
    """Minimal stand-in for elf's block-with-halo object."""
    from types import SimpleNamespace

    def bb(begin, end):
        return SimpleNamespace(begin=begin, end=end)

    return SimpleNamespace(
        innerBlock=bb(*inner),
        outerBlock=bb(*outer),
        innerBlockLocal=bb(*inner_local),
    )


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


class TestMinOuterSize:
    def test_large_sigma(self):
        assert _min_outer_size(5.0, 5.0, [10, 10, 10]) == 31

    def test_halo_dominates(self):
        # halo+1 = 11 > 6*0.7+1 = 5
        assert _min_outer_size(0.7, 0.7, [10, 10, 10]) == 11

    def test_sigma_dominates(self):
        assert _min_outer_size(3.0, 0.5, [2, 2, 2]) == 19


class TestAdjustBlockSlicings:
    data_shape = (129, 129, 129)
    min_outer = 31  # for sigma=5.0

    def test_interior_block_no_extension(self):
        # Block well inside the data — no extension needed
        block = _mk_block(
            inner=((10, 10, 10), (50, 50, 50)),
            outer=((0, 0, 0), (60, 60, 60)),
            inner_local=((10, 10, 10), (50, 50, 50)),
        )
        inner, outer, inner_local = _adjust_block_slicings(block, self.data_shape, self.min_outer)
        # outer unchanged (60 >= 31)
        assert outer == (slice(0, 60),) * 3
        # inner unchanged
        assert inner == (slice(10, 50),) * 3
        # inner_local unchanged (outer_begin not shifted)
        assert inner_local == (slice(10, 50),) * 3

    def test_edge_block_extends_backward(self):
        # Last 1-voxel block with halo=10 -> outer is 11 voxels, needs extension to 31
        # outer = [118, 129] (11 voxels), clamped at end
        block = _mk_block(
            inner=((128, 128, 128), (129, 129, 129)),
            outer=((118, 118, 118), (129, 129, 129)),
            inner_local=((10, 10, 10), (11, 11, 11)),
        )
        inner, outer, inner_local = _adjust_block_slicings(block, self.data_shape, self.min_outer)
        # Deficit = 31 - 11 = 20. outer_begin=118, so extend_start = min(20, 118) = 20
        # outer_begin -> 98, outer_end unchanged at 129. Size = 31.
        assert outer[0] == slice(98, 129)
        # inner unchanged
        assert inner == (slice(128, 129),) * 3
        # inner_local shifts by outerBlock.begin - outer_begin = 118 - 98 = 20
        # inner_local_begin = 10 + 20 = 30, size = 1
        assert inner_local == (slice(30, 31),) * 3

    def test_edge_block_extends_forward(self):
        # First block, outer clamped at start: outer = [0, 11]
        block = _mk_block(
            inner=((0, 0, 0), (1, 1, 1)),
            outer=((0, 0, 0), (11, 11, 11)),
            inner_local=((0, 0, 0), (1, 1, 1)),
        )
        inner, outer, inner_local = _adjust_block_slicings(block, self.data_shape, self.min_outer)
        # Deficit = 20. outer_begin=0, extend_start = min(20, 0) = 0.
        # extend_end = min(20, 129-11) = 20. outer_end -> 31.
        assert outer[0] == slice(0, 31)
        # inner_local_begin = 0 + (0 - 0) = 0, unchanged
        assert inner_local == (slice(0, 1),) * 3

    def test_partial_extension_when_data_too_small(self):
        # Data only 10 voxels, outer is 4 voxels, min_outer=31
        # Can only extend to 10 (data limit), not 31
        small_shape = (10, 10, 10)
        block = _mk_block(
            inner=((9, 9, 9), (10, 10, 10)),
            outer=((6, 6, 6), (10, 10, 10)),
            inner_local=((3, 3, 3), (4, 4, 4)),
        )
        inner, outer, inner_local = _adjust_block_slicings(block, small_shape, 31)
        # Deficit = 31 - 4 = 27. extend_start = min(27, 6) = 6 -> begin=0
        # extend_end = min(21, 10-10) = 0 -> end=10. Size = 10 (partial).
        assert outer[0] == slice(0, 10)
        # inner_local_begin = 3 + (6 - 0) = 9
        assert inner_local == (slice(9, 10),) * 3


class TestSigmaTooLargeForData:
    def test_raises_when_data_too_small(self):
        # 10^3 data with sigma=5 -> min_outer=31 > 10
        data = numpy.zeros((10, 10, 10), dtype=numpy.float32)
        with pytest.raises(ValueError, match="too small"):
            parallel_watershed(
                data=data,
                threshold=0.5,
                sigma_seeds=5.0,
                sigma_weights=5.0,
                minsize=1,
                alpha=0.9,
                pixel_pitch=None,
                non_max_suppression=False,
                block_shape=None,
                halo=None,
                max_workers=1,
            )

    def test_does_not_raise_when_data_large_enough(self):
        # 64^3 data with sigma=1 -> min_outer = 7, fits fine
        data = numpy.random.rand(64, 64, 64).astype(numpy.float32)
        ws, max_label = parallel_watershed(
            data=data,
            threshold=0.5,
            sigma_seeds=1.0,
            sigma_weights=1.0,
            minsize=1,
            alpha=0.9,
            pixel_pitch=None,
            non_max_suppression=False,
            block_shape=None,
            halo=None,
            max_workers=1,
        )
        assert max_label > 0
