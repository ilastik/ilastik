import pytest  # type: ignore
import os
from pathlib import Path, PurePosixPath

import h5py
import numpy as np
import z5py

from ilastik.utility.data_url import (
    ArchiveDataPath,
    DataPath,
    H5DataPath,
    N5DataPath,
    SimpleDataPath,
    NpzDataPath,
    Dataset,
)


@pytest.fixture  # type: ignore
def sample_files_dir(tmpdir) -> Path:
    samples_dir = Path(tmpdir / "samples")
    os.mkdir(samples_dir)

    samples_dir.joinpath("some_file[1].tiff").touch()
    samples_dir.joinpath("some_file_x.tiff").touch()
    samples_dir.joinpath("some_file_y.tiff").touch()
    samples_dir.joinpath("some_file_z.tiff").touch()

    with h5py.File(samples_dir / "some_h5_file[1].h5", "w") as f:
        f.create_dataset("/some/data[1]", data=np.arange(100).reshape(10, 10))
        f.create_dataset("/some/data_x", data=np.arange(100).reshape(10, 10))
        f.create_dataset("/some/data_y", data=np.arange(100).reshape(10, 10))
        f.create_dataset("/some/data_z", data=np.arange(100).reshape(10, 10))

    with h5py.File(samples_dir / "some_h5_file_x.hdf5", "w") as f:
        f.create_dataset("/some/data[1]", data=np.arange(100).reshape(10, 10))
        f.create_dataset("/some/data_x", data=np.arange(100).reshape(10, 10))
        f.create_dataset("/some/data_y", data=np.arange(100).reshape(10, 10))
        f.create_dataset("/some/data_z", data=np.arange(100).reshape(10, 10))

    with h5py.File(samples_dir / "some_h5_file_y.hdf5", "w") as f:
        f.create_dataset("/some/data[1]", data=np.arange(100).reshape(10, 10))
        f.create_dataset("/some/data_x", data=np.arange(100).reshape(10, 10))
        f.create_dataset("/some/data_y", data=np.arange(100).reshape(10, 10))
        f.create_dataset("/some/data_z", data=np.arange(100).reshape(10, 10))

    with z5py.File(samples_dir / "some_n5_file_[1].n5", "w") as f:
        f.create_dataset("some/data[1]", data=np.arange(100).reshape(10, 10))
        f.create_dataset("some/data_x", data=np.arange(100).reshape(10, 10))
        f.create_dataset("some/data_y", data=np.arange(100).reshape(10, 10))
        f.create_dataset("some/data_z", data=np.arange(100).reshape(10, 10))

    with z5py.File(samples_dir / "some_n5_file_x.n5", "w") as f:
        f.create_dataset("some/data[1]", data=np.arange(100).reshape(10, 10))
        f.create_dataset("some/data_x", data=np.arange(100).reshape(10, 10))
        f.create_dataset("some/data_y", data=np.arange(100).reshape(10, 10))
        f.create_dataset("some/data_z", data=np.arange(100).reshape(10, 10))

    with z5py.File(samples_dir / "some_n5_file_y.n5", "w") as f:
        f.create_dataset("some/data[1]", data=np.arange(100).reshape(10, 10))
        f.create_dataset("some/data_x", data=np.arange(100).reshape(10, 10))

    np.savez(
        samples_dir / "some_npz_file_x.npz",
        data_x=np.arange(100).reshape(10, 10),
        data_y=np.arange(100).reshape(10, 10),
        data_z=np.arange(100).reshape(10, 10),
    )

    np.savez(samples_dir / "some_npz_file_y.npz", data_x=np.arange(100).reshape(10, 10))

    return samples_dir


def test_non_globlike_simple_data_path(sample_files_dir: Path):
    single_globlike_file_path = sample_files_dir / "some_file[1].tiff"
    simple_data_path = DataPath.from_string(str(single_globlike_file_path))
    assert simple_data_path.exists()
    assert simple_data_path.glob(smart=True) == [simple_data_path]
    simple_data_path.glob(smart=False) == []


def test_globlike_simple_data_path(sample_files_dir: Path):
    glob_path = SimpleDataPath(sample_files_dir / "some_file_[xyz].tiff")
    assert glob_path.glob() == [
        SimpleDataPath(sample_files_dir / p) for p in ("some_file_x.tiff", "some_file_y.tiff", "some_file_z.tiff")
    ]


########################################################


def test_non_globlike_h5_data_path(sample_files_dir: Path):
    h5_globlike_file_path = sample_files_dir / "some_h5_file[1].h5/some/data[1]"
    h5_data_path = DataPath.from_string(str(h5_globlike_file_path))
    assert isinstance(h5_data_path, H5DataPath)
    assert h5_data_path.exists()
    assert h5_data_path.glob(smart=True) == [h5_data_path]
    h5_data_path.glob(smart=False) == []


def test_externally_globlike_h5_data_path_expands_properly(sample_files_dir: Path):
    glob_path = DataPath.from_string(str(sample_files_dir / "some_h5_file_[xy].hdf5/some/data_x"))
    assert glob_path.glob() == [
        H5DataPath(sample_files_dir / "some_h5_file_x.hdf5", PurePosixPath("/some/data_x")),
        H5DataPath(sample_files_dir / "some_h5_file_y.hdf5", PurePosixPath("/some/data_x")),
    ]


def test_internally_globlike_h5_data_path_expands_properly(sample_files_dir: Path):
    glob_path = DataPath.from_string(str(sample_files_dir / "some_h5_file_x.hdf5/some/data_[xyz]"))
    expanded = glob_path.glob()
    expected = [
        H5DataPath(sample_files_dir / "some_h5_file_x.hdf5", PurePosixPath("/some/data_x")),
        H5DataPath(sample_files_dir / "some_h5_file_x.hdf5", PurePosixPath("/some/data_y")),
        H5DataPath(sample_files_dir / "some_h5_file_x.hdf5", PurePosixPath("/some/data_z")),
    ]
    assert expanded == expected


def test_internally_and_externally_globlike_h5_data_path_expands_properly(sample_files_dir: Path):
    glob_path = DataPath.from_string(str(sample_files_dir / "some_h5_file_[xy].hdf5/some/data_[xyz]"))
    expanded = glob_path.glob()
    expected = [
        H5DataPath(sample_files_dir / "some_h5_file_x.hdf5", PurePosixPath("/some/data_x")),
        H5DataPath(sample_files_dir / "some_h5_file_x.hdf5", PurePosixPath("/some/data_y")),
        H5DataPath(sample_files_dir / "some_h5_file_x.hdf5", PurePosixPath("/some/data_z")),
        H5DataPath(sample_files_dir / "some_h5_file_y.hdf5", PurePosixPath("/some/data_x")),
        H5DataPath(sample_files_dir / "some_h5_file_y.hdf5", PurePosixPath("/some/data_y")),
        H5DataPath(sample_files_dir / "some_h5_file_y.hdf5", PurePosixPath("/some/data_z")),
    ]
    assert expanded == expected


############################################################


def test_externally_globlike_n5_data_path_expands_properly(sample_files_dir: Path):
    glob_path = DataPath.from_string(str(sample_files_dir / "some_n5_file_[xy].n5/some/data_x"))
    expanded = glob_path.glob()
    expected = [
        N5DataPath(sample_files_dir / "some_n5_file_x.n5", PurePosixPath("/some/data_x")),
        N5DataPath(sample_files_dir / "some_n5_file_y.n5", PurePosixPath("/some/data_x")),
    ]
    assert expanded == expected


def test_internally_globlike_n5_data_path_expands_properly(sample_files_dir: Path):
    glob_path = DataPath.from_string(str(sample_files_dir / "some_n5_file_x.n5/some/data_[xyz]"))
    expanded = glob_path.glob()
    expected = [
        N5DataPath(sample_files_dir / "some_n5_file_x.n5", PurePosixPath("/some/data_x")),
        N5DataPath(sample_files_dir / "some_n5_file_x.n5", PurePosixPath("/some/data_y")),
        N5DataPath(sample_files_dir / "some_n5_file_x.n5", PurePosixPath("/some/data_z")),
    ]
    assert expanded == expected


def test_internally_and_externally_globlike_n5_data_path_expands_properly(sample_files_dir: Path):
    glob_path = DataPath.from_string(str(sample_files_dir / "some_n5_file_[xy].n5/some/data_[xyz]"))
    expanded = glob_path.glob()
    expected = [
        N5DataPath(sample_files_dir / "some_n5_file_x.n5", PurePosixPath("/some/data_x")),
        N5DataPath(sample_files_dir / "some_n5_file_x.n5", PurePosixPath("/some/data_y")),
        N5DataPath(sample_files_dir / "some_n5_file_x.n5", PurePosixPath("/some/data_z")),
        N5DataPath(sample_files_dir / "some_n5_file_y.n5", PurePosixPath("/some/data_x")),
    ]
    assert expanded == expected


def test_externally_globlike_npz_data_path_expands_properly(sample_files_dir: Path):
    glob_path = DataPath.from_string(str(sample_files_dir / "some_npz_file_[xy].npz/data_x"))
    expanded = glob_path.glob()
    expected = [
        NpzDataPath(sample_files_dir / "some_npz_file_x.npz", PurePosixPath("/data_x")),
        NpzDataPath(sample_files_dir / "some_npz_file_y.npz", PurePosixPath("/data_x")),
    ]
    assert expanded == expected


def test_internally_globlike_npz_data_path_expands_properly(sample_files_dir: Path):
    glob_path = DataPath.from_string(str(sample_files_dir / "some_npz_file_x.npz/data_[xyz]"))
    expanded = glob_path.glob()
    expected = [
        NpzDataPath(sample_files_dir / "some_npz_file_x.npz", PurePosixPath("/data_x")),
        NpzDataPath(sample_files_dir / "some_npz_file_x.npz", PurePosixPath("/data_y")),
        NpzDataPath(sample_files_dir / "some_npz_file_x.npz", PurePosixPath("/data_z")),
    ]
    assert expanded == expected


def test_internally_and_externally_globlike_npz_data_path_expands_properly(sample_files_dir: Path):
    glob_path = DataPath.from_string(str(sample_files_dir / "some_npz_file_[xy].npz/data_[xyz]"))
    expanded = glob_path.glob()
    expected = [
        NpzDataPath(sample_files_dir / "some_npz_file_x.npz", PurePosixPath("/data_x")),
        NpzDataPath(sample_files_dir / "some_npz_file_x.npz", PurePosixPath("/data_y")),
        NpzDataPath(sample_files_dir / "some_npz_file_x.npz", PurePosixPath("/data_z")),
        NpzDataPath(sample_files_dir / "some_npz_file_y.npz", PurePosixPath("/data_x")),
    ]
    assert expanded == expected


###############################################################


def test_listing_archive_datasets(sample_files_dir: Path):
    assert ArchiveDataPath.list_internal_paths(sample_files_dir / "some_h5_file_x.hdf5") == [
        PurePosixPath("/some/data[1]"),
        PurePosixPath("/some/data_x"),
        PurePosixPath("/some/data_y"),
        PurePosixPath("/some/data_z"),
    ]

    assert ArchiveDataPath.list_internal_paths(sample_files_dir / "some_n5_file_[1].n5") == [
        PurePosixPath("/some/data[1]"),
        PurePosixPath("/some/data_x"),
        PurePosixPath("/some/data_y"),
        PurePosixPath("/some/data_z"),
    ]

    assert ArchiveDataPath.list_internal_paths(sample_files_dir / "some_npz_file_x.npz") == [
        PurePosixPath("/data_x"),
        PurePosixPath("/data_y"),
        PurePosixPath("/data_z"),
    ]


###############################################################


def test_dataset_from_string(sample_files_dir: Path):
    simple_globlike_path = sample_files_dir / "some_file[1].tiff"
    dsp = Dataset.from_string(str(simple_globlike_path), deglob=True)
    assert len(dsp.data_paths) == 1 and dsp.data_paths[0] == SimpleDataPath(simple_globlike_path)

    simple_glob_path = str(sample_files_dir / "some_file_[xyz].tiff")
    dsp = Dataset.from_string(simple_glob_path, deglob=True)
    assert dsp.data_paths == [
        SimpleDataPath(sample_files_dir / "some_file_x.tiff"),
        SimpleDataPath(sample_files_dir / "some_file_y.tiff"),
        SimpleDataPath(sample_files_dir / "some_file_z.tiff"),
    ]


def test_dataset_split(sample_files_dir: Path):
    paths = [
        sample_files_dir / "some_file[1].tiff",
        sample_files_dir / "some_h5_file_[xy].hdf5/some/data_[xyz]",
        sample_files_dir / "some_npz_file_[xy].npz/data_[xyz]",
    ]
    dsp_mixed = Dataset.split(os.path.pathsep.join(str(p) for p in paths), deglob=True)
    assert dsp_mixed.data_paths == [
        SimpleDataPath(sample_files_dir / "some_file[1].tiff"),
        H5DataPath(sample_files_dir / "some_h5_file_x.hdf5", PurePosixPath("/some/data_x")),
        H5DataPath(sample_files_dir / "some_h5_file_x.hdf5", PurePosixPath("/some/data_y")),
        H5DataPath(sample_files_dir / "some_h5_file_x.hdf5", PurePosixPath("/some/data_z")),
        H5DataPath(sample_files_dir / "some_h5_file_y.hdf5", PurePosixPath("/some/data_x")),
        H5DataPath(sample_files_dir / "some_h5_file_y.hdf5", PurePosixPath("/some/data_y")),
        H5DataPath(sample_files_dir / "some_h5_file_y.hdf5", PurePosixPath("/some/data_z")),
        NpzDataPath(sample_files_dir / "some_npz_file_x.npz", PurePosixPath("data_x")),
        NpzDataPath(sample_files_dir / "some_npz_file_x.npz", PurePosixPath("data_y")),
        NpzDataPath(sample_files_dir / "some_npz_file_x.npz", PurePosixPath("data_z")),
        NpzDataPath(sample_files_dir / "some_npz_file_y.npz", PurePosixPath("data_x")),
    ]


def test_getting_archive_siblings(sample_files_dir: Path):
    dsp = Dataset(
        [
            SimpleDataPath(sample_files_dir / "some_file[1].tiff"),
            H5DataPath(sample_files_dir / "some_h5_file_x.hdf5", PurePosixPath("/some/data_x")),
            NpzDataPath(sample_files_dir / "some_npz_file_x.npz", PurePosixPath("/data_x")),
        ]
    )
    assert dsp.archive_siblings() == [
        H5DataPath(sample_files_dir / "some_h5_file_x.hdf5", PurePosixPath("/some/data[1]")),
        H5DataPath(sample_files_dir / "some_h5_file_x.hdf5", PurePosixPath("/some/data_x")),
        H5DataPath(sample_files_dir / "some_h5_file_x.hdf5", PurePosixPath("/some/data_y")),
        H5DataPath(sample_files_dir / "some_h5_file_x.hdf5", PurePosixPath("/some/data_z")),
        NpzDataPath(sample_files_dir / "some_npz_file_x.npz", PurePosixPath("/data_x")),
        NpzDataPath(sample_files_dir / "some_npz_file_x.npz", PurePosixPath("/data_y")),
        NpzDataPath(sample_files_dir / "some_npz_file_x.npz", PurePosixPath("/data_z")),
    ]


def test_is_under(sample_files_dir: Path):
    dsp = Dataset(
        [
            SimpleDataPath(sample_files_dir / "some_file[1].tiff"),
            H5DataPath(sample_files_dir / "some_h5_file_x.hdf5", PurePosixPath("/some/data_x")),
            NpzDataPath(sample_files_dir / "some_npz_file_x.npz", PurePosixPath("/data_x")),
        ]
    )
    assert dsp.is_under(sample_files_dir)


def test_is_archive(sample_files_dir: Path):
    assert ArchiveDataPath.is_archive_path("/blas/bles.h5/some/data")
    assert not ArchiveDataPath.is_archive_path("/blas/bles.tiff")


def test_common_paths(sample_files_dir: Path):
    dsp1 = Dataset([H5DataPath(sample_files_dir / "some_h5_file_x.hdf5", PurePosixPath("/some/data_x"))])
    dsp2 = Dataset([N5DataPath(sample_files_dir / "some_n5_file_y.n5", PurePosixPath("/some/data_x"))])
    dsp3_no_internals = Dataset([SimpleDataPath(sample_files_dir / "some_file_z.tiff")])

    assert Dataset.common_internal_paths([dsp1, dsp2, dsp3_no_internals]) == [
        PurePosixPath("/some/data[1]"),
        PurePosixPath("/some/data_x"),
    ]
