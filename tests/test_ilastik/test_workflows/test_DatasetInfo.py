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
def png_stack_dir(tmp_path) -> Path:
    for i in range(3):
        pil_image = PilImage.fromarray((numpy.random.rand(520, 697, 3) * 255).astype(numpy.uint8))
        with open(tmp_path / f"c_cells_{i}.png", "wb") as png_file:
            pil_image.save(png_file, "png")
    return tmp_path


@pytest.fixture
def h5_1_100_200_1_1(tmp_path):
    _, h5_path = tempfile.mkstemp(prefix=os.path.join(tmp_path, ""), suffix=".h5")
    raw = (numpy.random.rand(1, 100, 200, 1, 1) * 255).astype(numpy.uint8)
    with h5py.File(h5_path, "w") as f:
        f["some_data"] = raw
    return h5_path


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


def dir_to_star_glob(dir_path: str, append_extension: bool = False):
    if append_extension:
        extensions = set(path.split(".")[-1] for path in os.listdir(dir_path))
        assert len(extensions) == 1
        ext = "." + extensions.pop()
    else:
        ext = ""
    return os.path.join(dir_path, "*" + ext)


@pytest.fixture
def png_colon_path_stack(png_stack_dir) -> str:
    return dir_to_colon_glob(png_stack_dir)


@pytest.fixture
def png_star_stack(png_stack_dir) -> str:
    return dir_to_star_glob(png_stack_dir)


@pytest.fixture
def h5_colon_path_stack(h5_stack_dir) -> str:
    return dir_to_colon_glob(h5_stack_dir)


@pytest.fixture
def h5_colon_path_stack_with_inner_paths(h5_colon_path_stack) -> str:
    inner_path = "/volume/data"
    return h5_colon_path_stack.replace(os.path.pathsep, inner_path + os.path.pathsep) + inner_path


@pytest.fixture
def h5_star_stack(h5_stack_dir) -> str:
    return dir_to_star_glob(h5_stack_dir)


@pytest.fixture
def empty_project_file() -> h5py.File:
    return h5py.File(tempfile.mkstemp()[1], "r+")


def test_create_nickname(h5_colon_path_stack):
    expanded_paths = DatasetInfo.expand_path(h5_colon_path_stack)
    nickname = DatasetInfo.create_nickname(expanded_paths)
    assert nickname == "2d_apoptotic_binary_"


def test_create_nickname_for_single_file_does_not_contain_extension(h5_colon_path_stack):
    expanded_paths = DatasetInfo.expand_path(h5_colon_path_stack)
    nickname = DatasetInfo.create_nickname(expanded_paths[0:1])
    assert nickname == "2d_apoptotic_binary_0"


def test_create_nickname_with_internal_paths(h5_colon_path_stack_with_inner_paths):
    expanded_paths = DatasetInfo.expand_path(h5_colon_path_stack_with_inner_paths)
    nickname = DatasetInfo.create_nickname(expanded_paths)
    assert nickname == "2d_apoptotic_binary_-volume-data"


def test_expand_path(h5_stack_dir):
    expansions = [Path(p) for p in DatasetInfo.expand_path(os.path.join(h5_stack_dir, "*"))]
    expected_file_paths = [
        Path(h5_stack_dir) / "2d_apoptotic_binary_0.h5",
        Path(h5_stack_dir) / "2d_apoptotic_binary_1.h5",
        Path(h5_stack_dir) / "2d_apoptotic_binary_2.h5",
    ]
    assert expansions == expected_file_paths

    expected_dataset_paths = [Path(fp) / "volume/data" for fp in expected_file_paths]
    expansions = [Path(p) for p in DatasetInfo.expand_path(os.path.join(h5_stack_dir, "*.h5", "vol*"))]
    assert expansions == expected_dataset_paths

    expansions = [Path(p) for p in DatasetInfo.expand_path(os.path.join(h5_stack_dir, "2d_apoptotic_binary_1.h5"))]
    assert expansions == expected_file_paths[1:2]

    relative_paths = ["2d_apoptotic_binary_0.h5", "2d_apoptotic_binary_1.h5", "2d_apoptotic_binary_2.h5"]
    relative_paths_with_colon = os.path.pathsep.join(relative_paths)
    expansions = [Path(p) for p in DatasetInfo.expand_path(relative_paths_with_colon, cwd=h5_stack_dir)]
    assert expansions == expected_file_paths


def test_stack_via_star_glob(png_star_stack: str, empty_project_file):
    info = FilesystemDatasetInfo(filePath=png_star_stack, sequence_axis="z", project_file=empty_project_file)
    assert info.nickname == "c_cells_"

    # empty project lies in /tmp, so paths should be relative
    assert info.is_under_project_file()


def test_relative_paths(png_stack_dir: str, monkeypatch):
    with h5py.File(os.path.join(png_stack_dir, "myproj.ilp"), "w") as project_file:
        info = FilesystemDatasetInfo(
            filePath=os.path.join(png_stack_dir, "*.png"), project_file=project_file, sequence_axis="z"
        )
        assert info.is_under_project_file()
        assert info.get_relative_paths() == ["c_cells_0.png", "c_cells_1.png", "c_cells_2.png"]


def test_no_relative_paths_when_project_file_not_in_same_tree_as_files(png_stack_dir: str, monkeypatch):
    with h5py.File(os.path.join(tempfile.mkdtemp(), "myproj.ilp"), "w") as project_file:
        info = FilesystemDatasetInfo(
            filePath=os.path.join(png_stack_dir, "*.png"), project_file=project_file, sequence_axis="z"
        )
        assert not info.is_under_project_file()


def test_create_using_paths_relative_to_project_file(png_stack_dir: str):
    with h5py.File(os.path.join(png_stack_dir, "myproj.ilp"), "w") as project_file:
        info = FilesystemDatasetInfo(filePath="*.png", project_file=project_file, sequence_axis="z")
        assert info.get_relative_paths() == ["c_cells_0.png", "c_cells_1.png", "c_cells_2.png"]


def test_star_glob(png_colon_path_stack: str, empty_project_file: h5py.File):
    info = FilesystemDatasetInfo(filePath=png_colon_path_stack, sequence_axis="z", project_file=empty_project_file)
    assert info.nickname == "c_cells_"
    assert info.laneDtype == numpy.uint8
    assert info.laneShape == (3, 520, 697, 3)
    assert info.is_under_project_file()


def test_stack_via_colon_glob(png_colon_path_stack, empty_project_file: h5py.File):
    info = FilesystemDatasetInfo(filePath=png_colon_path_stack, sequence_axis="t", project_file=empty_project_file)
    assert info.nickname == "c_cells_"
    assert info.is_under_project_file()


def test_h5_stack_via_colon_glob(h5_colon_path_stack_with_inner_paths, empty_project_file):
    info = FilesystemDatasetInfo(
        filePath=h5_colon_path_stack_with_inner_paths, sequence_axis="t", project_file=empty_project_file
    )
    assert info.nickname == "2d_apoptotic_binary_-volume-data"


def test_h5_stack_via_star_file_glob_and_defined_inner_path(h5_stack_dir, empty_project_file: h5py.File):
    h5_external_star_glob = os.path.join(h5_stack_dir, "*.h5")
    internal_path = DatasetInfo.globInternalPaths(h5_external_star_glob, "*")[0]
    total_path = os.path.join(h5_stack_dir, "*.h5", internal_path)
    info = FilesystemDatasetInfo(filePath=total_path, sequence_axis="z", project_file=empty_project_file)
    assert info.nickname == "2d_apoptotic_binary_-volume-data"
    assert info.is_under_project_file()


def test_h5_stack_via_star_file_glob_and_stared_internal_path(h5_stack_dir, empty_project_file):
    star_glob = h5_stack_dir / "*.h5/*"
    info = FilesystemDatasetInfo(filePath=str(star_glob), sequence_axis="z", project_file=empty_project_file)
    assert info.nickname == "2d_apoptotic_binary_-volume-data"
    assert info.is_under_project_file()

    expected_filepath = os.path.pathsep.join(
        [
            Path(h5_stack_dir).joinpath("2d_apoptotic_binary_0.h5/volume/data").as_posix(),
            Path(h5_stack_dir).joinpath("2d_apoptotic_binary_1.h5/volume/data").as_posix(),
            Path(h5_stack_dir).joinpath("2d_apoptotic_binary_2.h5/volume/data").as_posix(),
        ]
    )

    assert info.filePath == expected_filepath


def test_guess_tags_for_singleton_axes(h5_1_100_200_1_1, empty_project_file):
    info = FilesystemDatasetInfo(
        filePath=h5_1_100_200_1_1,
        project_file=empty_project_file,
        axistags=vigra.defaultAxistags("yx"),
        guess_tags_for_singleton_axes=True,
        sequence_axis="z",
    )
    assert info.axiskeys[1:3] == "yx"
