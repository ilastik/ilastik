from abc import ABC, abstractmethod
import enum
from types import ClassMethodDescriptorType
from typing import Tuple, TypeVar, Sequence, Union, List, Type
from pathlib import PurePosixPath, Path
import errno
import glob
import os
import re

import numpy as np
import z5py
import h5py
import z5py

from lazyflow.utility.pathHelpers import lsH5N5, splitPath, globH5N5, globNpz


DP = TypeVar("DP", bound="DataPath")


class DataPath(ABC):
    def __init__(self, raw_path: str):
        self.raw_path = raw_path

    @staticmethod
    def create(path: str) -> "DataPath":
        try:
            return ArchiveDataPath.create(path)
        except ValueError:
            return SimpleDataPath(path)

    @abstractmethod
    def exists(self) -> bool:
        pass

    @abstractmethod
    def relative_to(self: DP, other: Path) -> DP:
        pass

    @abstractmethod
    def glob(self, smart: bool = True) -> Sequence["DataPath"]:
        pass

    def __eq__(self, other: "DataPath") -> bool:
        return self.raw_path == other.raw_path

    def __repr__(self) -> str:
        return self.raw_path

    def __str__(self) -> str:
        return self.raw_path


class SimpleDataPath(DataPath):
    def __init__(self, raw_path: str):
        super().__init__(raw_path=raw_path)
        self.path = Path(raw_path)

    def exists(self) -> bool:
        return self.path.exists()

    def relative_to(self, other: Path) -> "SimpleDataPath":
        return SimpleDataPath(str(self.path.relative_to(other)))

    def glob(self, smart: bool = True) -> Sequence["DataPath"]:
        if smart and self.exists():
            return [self]
        expanded_paths = [DataPath.create(p) for p in glob.glob(str(self.path))]
        if not expanded_paths:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), str(self.path))
        return expanded_paths


class ArchiveDataPath(DataPath):
    def __init__(self, external_path: Path, internal_path: PurePosixPath):
        if external_path.suffix.lower()[1:] not in self.suffixes():
            raise ValueError(f"External path for {self.__class__.__name__} must end in {self.suffixes()}")
        self.external_path = external_path
        self.internal_path = PurePosixPath("/") / internal_path
        super().__init__(str(external_path / self.internal_path.relative_to("/")))

    @staticmethod
    def is_archive_path(path: str) -> bool:
        try:
            ArchiveDataPath.split_archive_path(path)
            return True
        except ValueError:
            return False

    @staticmethod
    def split_archive_path(path: str) -> Tuple[Path, PurePosixPath]:
        archive_suffix_regex = r"\.(" + "|".join(ArchiveDataPath.suffixes()) + ")(?:$|/)"
        components = re.split(archive_suffix_regex, str(path), maxsplit=1, flags=re.IGNORECASE)
        if len(components) != 3:
            raise ValueError(f"Path '{path}' does not look like an archive path")
        return (Path(components[0] + "." + components[1]), PurePosixPath("/") / components[2])

    @staticmethod
    def pick_archive_class_for(path: str) -> Type["ArchiveDataPath"]:
        external_path, _ = ArchiveDataPath.split_archive_path(path)
        external_suffix = external_path.suffix.lower()[1:]
        for klass in ArchiveDataPath.__subclasses__():
            if external_suffix in klass.suffixes():
                return klass
        raise ValueError(f"Could not find a subclass of ArchiveDataPath for path {path}")

    @staticmethod
    def create(path: str) -> "ArchiveDataPath":
        external_path, internal_path = ArchiveDataPath.split_archive_path(path)
        if internal_path == PurePosixPath("/"):
            raise ValueError(f"Path to archive file has empty path: '{str(external_path) + str(internal_path)}'")
        return ArchiveDataPath.pick_archive_class_for(path)(external_path=external_path, internal_path=internal_path)

    def relative_to(self, other: Path) -> "DataPath":
        return self.__class__(self.external_path.relative_to(other), self.internal_path)

    def __lt__(self, other: "DataPath") -> bool:
        if isinstance(other, ArchiveDataPath):
            return (str(self.external_path), str(self.internal_path)) < (
                str(other.external_path),
                str(other.internal_path),
            )
        else:
            return self.raw_path < other.raw_path

    def glob(self, smart: bool = True) -> Sequence["ArchiveDataPath"]:
        if smart and self.external_path.exists():
            externally_expanded_paths = [self]
        else:
            externally_expanded_paths = [
                self.__class__(external_path=Path(ep), internal_path=self.internal_path)
                for ep in glob.glob(str(self.external_path))
            ]
            if not externally_expanded_paths:
                raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), str(self.external_path))

        all_paths: List["ArchiveDataPath"] = []
        for data_path in sorted(externally_expanded_paths):
            all_paths += [data_path] if (smart and data_path.exists()) else sorted(data_path.glob_internal())
        return all_paths

    @classmethod
    @abstractmethod
    def list_internal_paths(cls, path: str) -> List[PurePosixPath]:
        return ArchiveDataPath.pick_archive_class_for(path).list_internal_paths(path)

    @abstractmethod
    def glob_internal(self: DP) -> List[DP]:
        pass

    @classmethod
    @abstractmethod
    def suffixes(cls) -> Sequence[str]:
        return [suffix for klass in ArchiveDataPath.__subclasses__() for suffix in klass.suffixes()]


class H5DataPath(ArchiveDataPath):
    @classmethod
    def suffixes(cls) -> Sequence[str]:
        return ["h5", "hdf5", "ilp"]

    @classmethod
    def list_internal_paths(cls, path: Path) -> List[PurePosixPath]:
        with h5py.File(path, "r") as f:
            return sorted([PurePosixPath("/") / p["name"] for p in lsH5N5(f)])

    def glob_internal(self) -> Sequence["H5DataPath"]:
        with h5py.File(str(self.external_path), "r") as f:
            return [
                H5DataPath(self.external_path, internal_path=PurePosixPath(p))
                for p in globH5N5(f, str(self.internal_path).lstrip("/"))
            ]

    def exists(self) -> bool:
        if not self.external_path.exists():
            return False
        with h5py.File(str(self.external_path), "r") as f:
            return self.internal_path.as_posix() in f


class N5DataPath(ArchiveDataPath):
    @classmethod
    def suffixes(cls) -> Sequence[str]:
        return ["n5"]

    @classmethod
    def list_internal_paths(cls, path: Path) -> List[PurePosixPath]:
        with z5py.File(path, "r") as f:
            return sorted([PurePosixPath("/") / p["name"] for p in lsH5N5(f)])

    def glob_internal(self) -> Sequence["N5DataPath"]:
        with z5py.N5File(str(self.external_path)) as f:
            return [
                N5DataPath(self.external_path, internal_path=PurePosixPath(p))
                for p in globH5N5(f, str(self.internal_path).lstrip("/"))
            ]

    def exists(self) -> bool:
        if not self.external_path.exists():
            return False
        with z5py.N5File(str(self.external_path)) as f:
            return self.internal_path.as_posix() in f


class NpzDataPath(ArchiveDataPath):
    @classmethod
    def suffixes(cls) -> Sequence[str]:
        return ["npz"]

    @classmethod
    def list_internal_paths(cls, path: Path) -> List[PurePosixPath]:
        return sorted([PurePosixPath("/") / p for p in np.load(path, mmap_mode="r").files])

    def glob_internal(self) -> Sequence["NpzDataPath"]:
        return [
            NpzDataPath(self.external_path, internal_path=PurePosixPath(p))
            for p in globNpz(str(self.external_path), str(self.internal_path).lstrip("/"))
        ]

    def exists(self) -> bool:
        if not self.external_path.exists():
            return False
        return self.internal_path in NpzDataPath.list_internal_paths(self.external_path)


class DatasetPath:
    """A collection of existing DataPaths"""

    def __init__(self, data_paths: Sequence[DataPath]):
        if not data_paths:
            raise ValueError(f"Empty data paths")
        assert all(dp.exists() for dp in data_paths)
        self.data_paths = data_paths

    @classmethod
    def split(cls, path: str, deglob: bool = True) -> "DatasetPath":
        try:
            return cls.from_string(path, deglob=deglob)
        except FileNotFoundError:
            dataset_paths = [DatasetPath.from_string(segment, deglob=deglob) for segment in path.split(os.path.pathsep)]
            return DatasetPath([data_path for ds_path in dataset_paths for data_path in ds_path.data_paths])

    @classmethod
    def from_string(cls, path: str, deglob: bool = True) -> "DatasetPath":
        data_path = DataPath.create(path)
        if data_path.exists():
            return DatasetPath([data_path])
        elif deglob:
            expanded = data_path.glob(smart=True)
            if expanded:
                return DatasetPath(expanded)
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), path)
