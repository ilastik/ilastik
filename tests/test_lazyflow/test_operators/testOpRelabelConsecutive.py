###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2024, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#          http://ilastik.org/license.html
###############################################################################
from unittest.mock import MagicMock, patch

import numpy as np
import numpy.typing as npt
import pytest
import vigra

# from lazyflow.operators import OpRelabelConsecutive
from lazyflow.operators import opRelabelConsecutive
from lazyflow.operators.opRelabelConsecutive import OpRelabelConsecutive
from lazyflow.roi import sliceToRoi


@pytest.fixture
def oprelabel(graph):
    return OpRelabelConsecutive(graph=graph)


@pytest.fixture
def labels() -> vigra.VigraArray:
    return vigra.taggedView(2 * np.arange(0, 90, dtype=np.uint8).reshape((9, 10)), "yx").withAxes("tzyxc")


@pytest.fixture
def labels_t() -> vigra.VigraArray:
    data = vigra.taggedView(2 * np.arange(0, 270, dtype=np.uint32).reshape((3, 9, 10)), "tyx")
    # a "background" pixel for every time slice"
    data[:, 0, 0] = 0
    return data


@pytest.mark.parametrize("axistags", ["tyx", "zytx", "xyzt", "xztyc"])
def test_preserve_axistags(oprelabel, labels, axistags):
    labels = labels.withAxes(axistags)
    oprelabel.Input.setValue(labels)

    assert oprelabel.CachedOutput.ready()
    assert "".join(oprelabel.CachedOutput.meta.getAxisKeys()) == axistags
    # This output _always_ has a time axis
    assert oprelabel.RelabelDict.meta.axistags == vigra.defaultAxistags("t")
    assert oprelabel.RelabelDict.meta.shape == (1,)


def test_simple(oprelabel: OpRelabelConsecutive, labels: vigra.VigraArray):
    oprelabel.Input.setValue(labels)
    expected = labels // 2
    relabeled: npt.ArrayLike = oprelabel.CachedOutput[:].wait()
    np.testing.assert_array_equal(relabeled, expected)
    mapping = oprelabel.RelabelDict[:].wait()[0]

    rev_mapping = {v: k for k, v in mapping.items()}
    original_from_dict = vigra.taggedView(vigra.analysis.applyMapping(relabeled.squeeze(), rev_mapping), "yx").withAxes(
        "tzyxc"
    )
    np.testing.assert_array_equal(original_from_dict, labels)


@pytest.mark.parametrize(
    "dtype_in, expected_dtype",
    [
        ("uint8", "uint8"),
        ("uint16", "uint32"),  # uint16 will be converted to uint32 (vigra cannot handle uint16)
        ("uint32", "uint32"),
        ("uint64", "uint64"),
    ],
)
def test_input_datatypes(oprelabel, labels, dtype_in, expected_dtype):
    labels = labels.astype(dtype_in)
    expected = labels // 2
    oprelabel.Input.setValue(labels)
    relabeled = oprelabel.CachedOutput[:].wait()
    np.testing.assert_array_equal(relabeled, expected)
    assert relabeled.dtype == expected_dtype


@pytest.mark.parametrize("dtype", ["float", "float16", "float32", "float64"])
def test_unsupported_dtype_raises(oprelabel, labels, dtype):
    labels = labels.astype(dtype)

    with pytest.raises(ValueError):
        oprelabel.Input.setValue(labels)


def test_startlabel_output(oprelabel, labels):
    oprelabel.StartLabel.setValue(10)
    oprelabel.Input.setValue(labels)

    assert oprelabel.CachedOutput.ready(), "output not ready!"

    expected = labels // 2
    expected[expected > 0] += 9

    relabeled = oprelabel.CachedOutput[:].wait()

    # 0 is a special label (we assume it's background), so it is unchanged
    # the first found object will have value 10
    # with the input data being 0, 2, 4, 6, 8 ...: 0, 10, 11, 12, 13 ...

    np.testing.assert_array_equal(relabeled, expected)


def test_startlabel_dict(oprelabel, labels):
    oprelabel.StartLabel.setValue(10)
    oprelabel.Input.setValue(labels)

    relabel_dict = oprelabel.RelabelDict[:].wait()[0]

    # 0 is a special label (we assume it's background), so it is unchanged
    # the first found object will have value 10
    # with the input data being 0, 2, 4, 6, 8 ...: 0, 10, 11, 12, 13 ...

    assert relabel_dict[0] == 0
    assert sorted(relabel_dict.values())[0:2] == [0, 10]


def test_requesting_output_saves_dict(oprelabel, labels):
    oprelabel.Input.setValue(labels)
    _ = oprelabel.CachedOutput[:].wait()

    assert oprelabel._opRelabelConsecutive._block_data.keys() == oprelabel._opRelabelConsecutive._block_dicts.keys()


@patch("vigra.analysis.relabelConsecutive", wraps=vigra.analysis.relabelConsecutive)
def test_request_order_0(relabel_mock: MagicMock, oprelabel, labels):
    oprelabel.Input.setValue(labels)
    relabel_mock.assert_not_called()
    relabeld_data = oprelabel.CachedOutput[:].wait()
    relabel_mock.assert_called_once()
    relabel_mapping = oprelabel.RelabelDict[:].wait()
    relabel_mock.assert_called_once()


@patch("vigra.analysis.relabelConsecutive", wraps=vigra.analysis.relabelConsecutive)
def test_request_order_1(relabel_mock: MagicMock, oprelabel, labels):
    oprelabel.Input.setValue(labels)
    relabel_mock.assert_not_called()
    relabel_mapping = oprelabel.RelabelDict[:].wait()
    relabel_mock.assert_called_once()
    relabeled_data = oprelabel.CachedOutput[:].wait()
    relabel_mock.assert_called_once()


@patch("vigra.analysis.relabelConsecutive", wraps=vigra.analysis.relabelConsecutive)
def test_time_slice_blocking_output(relabel_mock: MagicMock, oprelabel, labels_t):
    oprelabel.Input.setValue(labels_t)

    relabeled_data = oprelabel.CachedOutput[:].wait()
    assert relabel_mock.call_count == 3

    np.testing.assert_array_equal(relabeled_data.view(np.ndarray).min(axis=(1, 2)), [0, 0, 0])
    np.testing.assert_array_equal(relabeled_data.view(np.ndarray).max(axis=(1, 2)), [89, 89, 89])


@patch("vigra.analysis.relabelConsecutive", wraps=vigra.analysis.relabelConsecutive)
def test_sub_roi_request(relabel_mock: MagicMock, oprelabel, labels_t):
    oprelabel.Input.setValue(labels_t)
    relabel_mock.assert_not_called()
    relabeled_data = oprelabel.CachedOutput[1, 0:2, 0:3].wait()

    relabel_mock.assert_called_once()
    assert relabeled_data.shape == (1, 2, 3)
    expected_data = [[[0, 1, 2], [10, 11, 12]]]
    np.testing.assert_array_equal(relabeled_data, expected_data)


@patch("vigra.analysis.relabelConsecutive", wraps=vigra.analysis.relabelConsecutive)
def test_time_slice_blocking_dict(relabel_mock: MagicMock, oprelabel, labels_t):
    oprelabel.Input.setValue(labels_t)

    relabeled_dict = oprelabel.RelabelDict[:].wait()
    assert relabel_mock.call_count == 3

    for i, dct in enumerate(relabeled_dict):
        assert len(dct) == 90
        ref_dict = {((i * 90) + k) * 2: k for k in range(1, 90)}
        ref_dict[0] = 0
        assert dct == ref_dict


def test_serialization_output(oprelabel: OpRelabelConsecutive, labels):
    oprelabel.Input.setValue(labels)

    expected = labels // 2
    _ = oprelabel.CachedOutput[:].wait()

    data_to_serialize = oprelabel.SerializationOutput[:].wait()

    assert data_to_serialize.shape == (1,)
    assert data_to_serialize.dtype == object

    assert len(data_to_serialize) == 1

    relabeled_data, relabel_mapping = data_to_serialize[0]

    np.testing.assert_array_equal(relabeled_data, expected)

    rev_mapping = {v: k for k, v in relabel_mapping.items()}
    original_from_dict = vigra.taggedView(
        vigra.analysis.applyMapping(relabeled_data.squeeze(), rev_mapping), "yx"
    ).withAxes("tzyxc")
    np.testing.assert_array_equal(original_from_dict, labels)


def test_serialization_input(oprelabel: OpRelabelConsecutive, labels):
    # get OP ready
    oprelabel.Input.setValue(labels)
    cache_op = oprelabel._opRelabelConsecutive

    relabeled_data, __, relabel_dict = vigra.analysis.relabelConsecutive(
        labels.squeeze(), start_label=1, keep_zeros=True
    )

    relabeled_data = vigra.taggedView(relabeled_data, "yx").withAxes("tzyxc")
    slicing = (slice(0, 1, None),)

    assert len(cache_op._block_data) == 0
    assert len(cache_op._block_dicts) == 0

    oprelabel.SerializationInput[slicing] = (relabeled_data, relabel_dict)

    assert len(cache_op._block_data) == 1
    assert len(cache_op._block_dicts) == 1

    assert cache_op._block_data.keys() == cache_op._block_dicts.keys()


def test_memory_report(oprelabel: OpRelabelConsecutive, labels):
    cache_op = oprelabel._opRelabelConsecutive

    assert cache_op.usedMemory() == 0.0
    oprelabel.Input.setValue(labels)
    assert cache_op.usedMemory() == 0.0, "Nothing requested yet, cache should be cold"

    # labels 8bit, dict assumed to be key, value with each 8 bytes
    expected_memory_bytes = labels.size + labels.size * 8 * 2
    _ = oprelabel.CachedOutput[:].wait()
    assert cache_op.usedMemory() == expected_memory_bytes

    assert cache_op.freeMemory() == expected_memory_bytes

    assert cache_op.usedMemory() == 0.0


def test_free_block(oprelabel: OpRelabelConsecutive, labels_t: vigra.VigraArray):
    cache_op = oprelabel._opRelabelConsecutive
    oprelabel.Input.setValue(labels_t)
    _ = oprelabel.CachedOutput[:].wait()

    clean_blocks = oprelabel.CleanBlocks[:].wait()[0]

    assert len(clean_blocks) == 3

    mem_total = cache_op.usedMemory()

    block_roi = sliceToRoi(clean_blocks[-1], labels_t.withAxes("tzyxc").shape)
    block_key = tuple(map(tuple, block_roi))

    mem = cache_op.freeBlock(block_key)

    mem_after_clean = cache_op.usedMemory()

    assert (mem_after_clean + mem) == mem_total

    clean_blocks_after_clean = oprelabel.CleanBlocks[:].wait()[0]

    assert len(clean_blocks_after_clean) == 2
    assert clean_blocks_after_clean == clean_blocks[0:2]


def test_compressed(oprelabel: OpRelabelConsecutive, labels):
    oprelabel.CompressionEnabled.setValue(True)
    cache_op = oprelabel._opRelabelConsecutive

    # make the data compressible, labels is arange -> would not compress
    labels[labels > 0] = 2
    labels[:, :, 0:3, :, :] = 0
    oprelabel.Input.setValue(labels)
    output = oprelabel.CachedOutput[:].wait()
    relabel_dict = oprelabel.RelabelDict[:].wait()[0]

    assert relabel_dict == {0: 0, 2: 1}
    assert output.max() == 1
    assert output.sum() == 60

    expected_uncompressed_memory_bytes = labels.size + labels.size * 8 * 2

    compressed_mem = cache_op.usedMemory()
    assert compressed_mem > 0.0
    assert compressed_mem < expected_uncompressed_memory_bytes


def test_non_exisiting_block_ignored_in_free(oprelabel: OpRelabelConsecutive, labels):
    cache_op = oprelabel._opRelabelConsecutive

    # empty cache
    freed = cache_op.freeBlock(((0, 0), (0, 1)))
    assert freed == 0

    # cache filled
    oprelabel.Input.setValue(labels)
    _ = oprelabel.CachedOutput[:].wait()

    freed = cache_op.freeBlock(((5, 5), (6, 6)))
    assert freed == 0

    # test the case where block might have been removed before the request
    # for memory (usedMemory, freeBlock) completed
    freed_internal = cache_op._memory_for_block(((5, 5), (6, 6)))
    assert freed_internal == 0
