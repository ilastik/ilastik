import os
import numpy
import shutil
from pathlib import Path
import tempfile
import pytest
import requests
from typing import List
import h5py

from ilastik.applets.dataSelection import DatasetInfo

def download_test_image(url, suffix:str):
    resp = requests.get(url)
    _, image_path = tempfile.mkstemp(suffix='-' + suffix)
    with open(image_path, 'wb') as f:
        f.write(resp.content)
    return image_path

def download_stack(urls:List[str], prefix:str):
    stack_dir = tempfile.mkdtemp()
    extensions = [u.split('.')[-1] for u in urls]
    for idx, url in enumerate(urls):
        suffix = f"{prefix}{idx}.{extensions[idx]}"
        path =  download_test_image(url, suffix)
        shutil.move(path, os.path.join(stack_dir, suffix))
    return stack_dir

@pytest.fixture
def png_stack_dir():
    urls = ["http://data.ilastik.org/pixel-classification/2d/c_cells_1.png",
            "http://data.ilastik.org/pixel-classification/2d/c_cells_2.png",
            "http://data.ilastik.org/pixel-classification/2d/c_cells_1.png"]
    stack_dir = download_stack(urls, "c_cells_")
    yield stack_dir
    shutil.rmtree(stack_dir)

@pytest.fixture
def h5_stack_dir():
    urls = ["http://data.ilastik.org/object-classification/2d_apoptotic_binary.h5",
            "http://data.ilastik.org/object-classification/2d_apoptotic_binary.h5",
            "http://data.ilastik.org/object-classification/2d_apoptotic_binary.h5"]
    stack_dir = download_stack(urls, "2d_apoptotic_binary_")
    yield stack_dir
    shutil.rmtree(stack_dir)

def dir_to_colon_glob(dir_path:str):
    return os.path.pathsep.join(os.path.join(dir_path, file_path) for file_path in  os.listdir(dir_path))

def dir_to_star_glob(dir_path:str, append_extension:bool=False):
    if append_extension:
        extensions = set(path.split('.')[-1] for path in os.listdir(dir_path))
        assert len(extensions) == 1
        ext = '.' + extensions.pop()
    else:
        ext = ''
    return os.path.join(dir_path, '*' + ext)

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
    inner_path = '/volume/data'
    return h5_colon_path_stack.replace(':', inner_path + ':') + inner_path

@pytest.fixture
def h5_star_stack(h5_stack_dir) -> str:
    return dir_to_star_glob(h5_stack_dir)

@pytest.fixture
def empty_project_file() -> h5py.File:
    return h5py.File(tempfile.mkstemp()[1], 'r+')

def test_create_nickname(h5_colon_path_stack):
    nickname, _ = DatasetInfo.process_filepath(h5_colon_path_stack)
    assert nickname == '2d_apoptotic_binary_'

def test_create_nickname_for_single_file_does_not_contain_extension(h5_colon_path_stack):
    nickname, _ = DatasetInfo.process_filepath(h5_colon_path_stack.split(os.path.pathsep)[0])
    assert nickname == '2d_apoptotic_binary_0'

def test_create_nickname_with_internal_paths(h5_colon_path_stack_with_inner_paths):
    nickname, expanded_paths= DatasetInfo.process_filepath(h5_colon_path_stack_with_inner_paths)
    assert nickname == '2d_apoptotic_binary_-volume-data'
    assert len(expanded_paths) == 3

def test_expand_path(h5_stack_dir):
    expansions = DatasetInfo.expandPath(os.path.join(h5_stack_dir, '*'))
    expected_file_paths = [os.path.join(h5_stack_dir, '2d_apoptotic_binary_0.h5'),
                           os.path.join(h5_stack_dir, '2d_apoptotic_binary_1.h5'),
                           os.path.join(h5_stack_dir, '2d_apoptotic_binary_2.h5')]
    assert expansions == expected_file_paths

    expected_dataset_paths = [os.path.join(fp, 'volume/data') for fp in expected_file_paths]
    expansions = DatasetInfo.expandPath(os.path.join(h5_stack_dir, '*.h5', 'vol*'))
    assert expansions == expected_dataset_paths

    expansions = DatasetInfo.expandPath(os.path.join(h5_stack_dir, '2d_apoptotic_binary_1.h5'))
    assert expansions == expected_file_paths[1:2]


    relative_paths = ['2d_apoptotic_binary_0.h5',
                      '2d_apoptotic_binary_1.h5',
                      '2d_apoptotic_binary_2.h5']
    relative_paths_with_colon = os.path.pathsep.join(relative_paths)
    expansions = DatasetInfo.expandPath(relative_paths_with_colon, cwd=h5_stack_dir)
    assert expansions == expected_file_paths


def test_stack_via_star_glob(png_star_stack:str):
    info = DatasetInfo(png_star_stack, sequence_axis='z')
    assert info.nickname == 'c_cells_'
    assert info.location == DatasetInfo.Location.FileSystem

def test_saving_internally_via_star_glob(png_star_stack:str, empty_project_file):
    inner_group_path = 'some/inner/group'
    info = DatasetInfo(
        png_star_stack,
        sequence_axis='z',
        location=DatasetInfo.Location.ProjectInternal,
        project_file=empty_project_file,
        inner_group_path=inner_group_path)

    saved_data = empty_project_file[info.filePath]
    assert info.nickname == 'c_cells_'
    assert info.laneDtype == saved_data.dtype == numpy.uint8
    assert info.laneShape == saved_data.shape == (3,520,697,3)
    assert info.location == DatasetInfo.Location.ProjectInternal
    assert info.axiskeys == 'zyxc'


def test_relative_paths():
    """please implement me!!!"""

def test_star_glob(png_colon_path_stack:str):
    info = DatasetInfo(png_colon_path_stack, sequence_axis='z')
    assert info.nickname == 'c_cells_'
    assert info.laneDtype == numpy.uint8
    assert info.laneShape == (3,520,697,3)
    assert info.location == DatasetInfo.Location.FileSystem

def test_stack_via_colon_glob(png_colon_path_stack):
    info = DatasetInfo(png_colon_path_stack, sequence_axis='t')
    assert info.nickname == 'c_cells_'
    assert info.location == DatasetInfo.Location.FileSystem

def test_h5_stack_via_colon_glob(h5_colon_path_stack_with_inner_paths):
    info = DatasetInfo(h5_colon_path_stack_with_inner_paths, sequence_axis='t')
    assert info.nickname == '2d_apoptotic_binary_-volume-data'
    assert info.location == DatasetInfo.Location.FileSystem

def test_h5_stack_via_star_file_glob_and_defined_inner_path(h5_stack_dir):
    h5_external_star_glob = os.path.join(h5_stack_dir, '*.h5')
    internal_path = DatasetInfo.globInternalPaths(h5_external_star_glob, '*')[0]
    total_path = os.path.join(h5_stack_dir, '*.h5', internal_path)
    info = DatasetInfo(total_path, sequence_axis='z')
    assert info.nickname == '2d_apoptotic_binary_-volume-data'
    assert info.location == DatasetInfo.Location.FileSystem

def test_h5_stack_via_star_file_glob_and_stared_internal_path(h5_stack_dir):
    star_glob = os.path.join(h5_stack_dir, '*.h5/*')
    info = DatasetInfo(star_glob, sequence_axis='z')
    assert info.nickname == '2d_apoptotic_binary_-volume-data'
    assert info.location == DatasetInfo.Location.FileSystem

    expected_filepath = os.path.pathsep.join([os.path.join(h5_stack_dir, '2d_apoptotic_binary_0.h5/volume/data'),
                                              os.path.join(h5_stack_dir, '2d_apoptotic_binary_1.h5/volume/data'),
                                              os.path.join(h5_stack_dir, '2d_apoptotic_binary_2.h5/volume/data')])

    assert info.filePath == expected_filepath

