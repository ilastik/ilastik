from ilastik.utility.data_url import Dataset
import os
from pathlib import Path
import numpy
import vigra
import shutil
import tempfile
import pytest
import requests
from typing import List
import h5py
from PIL import Image as PilImage

from ilastik.applets.dataSelection import DatasetInfo, FilesystemDatasetInfo


@pytest.fixture
def h5_stack_dir(tmp_path):
    for i in range(3):
        raw = (numpy.random.rand(1, 100, 200, 1, 1) * 255).astype(numpy.uint8)
        with h5py.File(tmp_path / f"2d_apoptotic_binary_{i}.h5", "w") as f:
            f.create_group("volume")
            f["volume/data"] = raw
    return tmp_path


def dir_to_colon_glob(dir_path: str):
    return os.path.pathsep.join(os.path.join(dir_path, file_path) for file_path in os.listdir(dir_path))


@pytest.fixture
def h5_colon_path_stack(h5_stack_dir) -> str:
    return dir_to_colon_glob(h5_stack_dir)


@pytest.fixture
def h5_colon_path_stack_with_inner_paths(h5_colon_path_stack) -> str:
    inner_path = "/volume/data"
    return h5_colon_path_stack.replace(os.path.pathsep, inner_path + os.path.pathsep) + inner_path


def test_nickname(h5_colon_path_stack_with_inner_paths):
    dataset_info = FilesystemDatasetInfo(
        dataset=Dataset.split(h5_colon_path_stack_with_inner_paths, deglob=False), sequence_axis="z"
    )
    assert dataset_info.nickname == "2d_apoptotic_binary_-volume-data"
