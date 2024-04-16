from typing import Sequence, Tuple, Union
import h5py
import pytest

from ilastik.applets.base.appletSerializer.serializerUtils import (
    deleteIfPresent,
    slicingToString,
    stringToSlicing,
)


def test_deleteIfPresent_present(empty_in_memory_project_file: h5py.File):
    test_group_name = "test_group_42"
    _ = empty_in_memory_project_file.create_group(test_group_name)
    assert test_group_name in empty_in_memory_project_file

    deleteIfPresent(empty_in_memory_project_file, test_group_name)

    assert test_group_name not in empty_in_memory_project_file


def test_deleteIfPresent_not_present(empty_in_memory_project_file: h5py.File):
    test_group_name = "test_group_42"
    assert test_group_name not in empty_in_memory_project_file

    deleteIfPresent(empty_in_memory_project_file, test_group_name)

    assert test_group_name not in empty_in_memory_project_file


@pytest.mark.parametrize(
    "slicing,expected_string",
    [
        ((slice(0, 1),), b"[0:1]"),
        ((slice(0, 1), slice(5, 42)), b"[0:1,5:42]"),
    ],
)
def test_slicingToString(slicing: Sequence[slice], expected_string: bytes):
    assert slicingToString(slicing) == expected_string


@pytest.mark.parametrize(
    "slicing",
    [
        (slice(0, 1, 5),),
        (slice(0, 1), slice(5, 42, 13)),
    ],
)
def test_slicingToString_invalid_step_raises(slicing):
    with pytest.raises(ValueError, match="Only slices with step size of `1` or `None` are supported."):
        _ = slicingToString(slicing)


@pytest.mark.parametrize(
    "slicing",
    [
        (slice(None, 1),),
        (slice(None, 1), slice(5, 42)),
        (slice(0, 1), slice(None, 42)),
    ],
)
def test_slicingToString_start_none_raises(slicing):
    with pytest.raises(ValueError, match="Start indices for slicing must be integer, got `None`."):
        _ = slicingToString(slicing)


@pytest.mark.parametrize(
    "slicing",
    [
        (slice(0, None),),
        (slice(0, None), slice(5, 42, None)),
    ],
)
def test_slicingToString_stop_none_raises(slicing):
    with pytest.raises(ValueError, match="Stop indices for slicing must be integer, got `None`"):
        _ = slicingToString(slicing)


@pytest.mark.parametrize(
    "slice_string,expected_slicing",
    [
        (b"[0:1]", (slice(0, 1),)),
        (b"[0:1,5:42]", (slice(0, 1), slice(5, 42))),
        ("[0:1,5:42]", (slice(0, 1), slice(5, 42))),
    ],
)
def test_stringToSlicing(slice_string: Union[bytes, str], expected_slicing: Tuple[slice, ...]):
    assert stringToSlicing(slice_string) == expected_slicing


@pytest.mark.parametrize(
    "slice_string",
    [
        b"[0:None]",
        b"[None:1,5:42]",
        "[0:1:5,5:42]",
    ],
)
def test_stringToSlicing_raises(slice_string: Union[bytes, str]):
    with pytest.raises(ValueError):
        _ = stringToSlicing(slice_string)
