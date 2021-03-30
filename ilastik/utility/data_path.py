from abc import ABC, abstractmethod
from typing import Mapping, Set, Tuple, TypeVar, Sequence, Optional, List, Type, Iterable, Union, cast
from pathlib import PurePosixPath, Path
import errno
import glob
import os
import re
from urllib.parse import urlencode, urlsplit, parse_qs
import enum

import numpy as np
import z5py
import h5py

from lazyflow.utility.pathHelpers import lsH5N5, globH5N5, globNpz

# pyright: strict

S = TypeVar("S", bound="Scheme")


class Scheme(enum.Enum):
    HTTP = "http"
    HTTPS = "https"
    FILE = "file"

    @classmethod
    def from_string(cls, value: str) -> "Scheme":
        if value == "":
            return Scheme.FILE
        for item in cls:
            if item.value == value:
                return cast(S, item)
        raise ValueError(f"Could not convert {value} to a valid Scheme")

    @classmethod
    def contains(cls, value: str) -> bool:
        return value in [s.value for s in Scheme]

    def __str__(self) -> str:
        return self.value


class DataUrl(ABC):
    def __init__(
        self,
        *,
        scheme: Scheme,
        netloc: str,
        path: PurePosixPath,
        query: Optional[Mapping[str, List[str]]] = None,
        fragment: Optional[str] = None,
    ):
        assert path.is_absolute()
        self.scheme = scheme
        self.netloc = netloc
        self.path = path
        self.query: Mapping[str, List[str]] = query or {}
        self.fragment = fragment

    def raw(self) -> str:
        query_str = urlencode(self.query)
        if query_str:
            query_str = "?" + query_str
        fragment_str = self.fragment or ""
        if fragment_str:
            fragment_str = "#" + fragment_str
        return f"{self.scheme}://{self.netloc}{self.path}{query_str}{fragment_str}"


class PrecomputedChunksUrl(DataUrl):
    @classmethod
    def create(cls, url: str) -> "PrecomputedChunksUrl":
        url = re.sub(r"^(\w+)://(\w+)://", r"\1+\2://", url)
        parsed = urlsplit(url)
        scheme_components = parsed.scheme.split("+")
        if len(scheme_components) > 2 or scheme_components[0] != "precomputed":
            raise ValueError(f"Url scheme must be 'precomputed+<scheme>': {url}")
        scheme = scheme_components[1]
        if not Scheme.contains(scheme):
            raise ValueError(f"Bad scheme in url: {url}")
        query_dict = parse_qs(parsed.query)

        return PrecomputedChunksUrl(
            scheme=Scheme.from_string(scheme), netloc=parsed.netloc, path=PurePosixPath(parsed.path), query=query_dict
        )


DP = TypeVar("DP", bound="DataPath")


class DataPath(DataUrl):
    def __init__(self, file_path: Path):
        self.file_path = file_path.absolute()
        self.raw_file_path = str(self.file_path)
        super().__init__(scheme=Scheme.FILE, netloc="", path=PurePosixPath(file_path))

    def is_under(self, path: Path):
        try:
            self.file_path.relative_to(path)
            return True
        except ValueError:
            return False

    @staticmethod
    def create(path: str) -> "DataPath":
        try:
            return ArchiveDataPath.create(path)
        except ValueError:
            return SimpleDataPath(Path(path))

    @abstractmethod
    def exists(self) -> bool:
        pass

    @abstractmethod
    def relative_to(self: DP, other: Path) -> DP:
        pass

    @abstractmethod
    def glob(self, smart: bool = True) -> Sequence["DataPath"]:
        pass

    def __hash__(self) -> int:
        return hash(self.raw_file_path)

    def __eq__(self, other: "DataPath") -> bool:
        return str(self) == str(other)

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return self.raw_file_path

    def __lt__(self, other: "DataPath") -> bool:
        return str(self) < str(other)


class SimpleDataPath(DataPath):
    def __init__(self, file_path: Path):
        super().__init__(file_path=file_path)

    def exists(self) -> bool:
        return self.file_path.exists()

    def relative_to(self, other: Path) -> "SimpleDataPath":
        return SimpleDataPath(self.file_path.relative_to(other))

    def glob(self, smart: bool = True) -> Sequence["DataPath"]:
        if smart and self.exists():
            return [self]
        expanded_paths = [DataPath.create(p) for p in glob.glob(self.raw_file_path)]
        if not expanded_paths:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), str(self.file_path))
        return expanded_paths


ADP = TypeVar("ADP", bound="ArchiveDataPath")


class ArchiveDataPath(DataPath):
    def __init__(self, file_path: Path, internal_path: PurePosixPath):
        if file_path.suffix.lower()[1:] not in self.suffixes():
            raise ValueError(f"External path for {self.__class__.__name__} must end in {self.suffixes()}")
        super().__init__(file_path=file_path)
        self.internal_path = PurePosixPath("/") / internal_path

    def __str__(self) -> str:
        return str(self.file_path / self.internal_path.relative_to("/"))

    def with_internal_path(self: ADP, internal_path: PurePosixPath) -> ADP:
        return self.__class__(self.file_path, internal_path=internal_path)

    def siblings(self: ADP) -> List[ADP]:
        return [
            self.__class__(self.file_path, internal_path) for internal_path in self.list_internal_paths(self.file_path)
        ]

    @staticmethod
    def is_archive_path(path: Union[str, Path]) -> bool:
        try:
            ArchiveDataPath.split_archive_path(str(path))
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
        file_path, _ = ArchiveDataPath.split_archive_path(path)
        external_suffix = file_path.suffix.lower()[1:]
        for klass in ArchiveDataPath.__subclasses__():
            if external_suffix in klass.suffixes():
                return klass
        raise ValueError(f"Could not find a subclass of ArchiveDataPath for path {path}")

    @staticmethod
    def create(path: str) -> "ArchiveDataPath":
        file_path, internal_path = ArchiveDataPath.split_archive_path(path)
        if internal_path == PurePosixPath("/"):
            raise ValueError(f"Path to archive file has empty path: '{str(file_path) + str(internal_path)}'")
        return ArchiveDataPath.pick_archive_class_for(path)(file_path=file_path, internal_path=internal_path)

    def relative_to(self, other: Path) -> "DataPath":
        return self.__class__(self.file_path.relative_to(other), self.internal_path)

    def glob(self, smart: bool = True) -> Sequence["ArchiveDataPath"]:
        if smart and self.file_path.exists():
            externally_expanded_paths = [self]
        else:
            externally_expanded_paths = [
                self.__class__(file_path=Path(ep), internal_path=self.internal_path)
                for ep in glob.glob(str(self.file_path))
            ]
            if not externally_expanded_paths:
                raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), str(self.file_path))

        all_paths: List["ArchiveDataPath"] = []
        for data_path in sorted(externally_expanded_paths):
            all_paths += [data_path] if (smart and data_path.exists()) else sorted(data_path.glob_internal())
        return all_paths

    @classmethod
    @abstractmethod
    def list_internal_paths(cls, path: Path) -> List[PurePosixPath]:
        return ArchiveDataPath.pick_archive_class_for(str(path)).list_internal_paths(path)

    @abstractmethod
    def glob_internal(self: DP) -> Sequence[DP]:
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
        with h5py.File(str(self.file_path), "r") as f:
            return [
                H5DataPath(self.file_path, internal_path=PurePosixPath(p))
                for p in globH5N5(f, str(self.internal_path).lstrip("/")) or []
            ]

    def exists(self) -> bool:
        if not self.file_path.exists():
            return False
        with h5py.File(str(self.file_path), "r") as f:
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
        with z5py.N5File(str(self.file_path)) as f:
            return [
                N5DataPath(self.file_path, internal_path=PurePosixPath(p))
                for p in globH5N5(f, str(self.internal_path).lstrip("/")) or []
            ]

    def exists(self) -> bool:
        if not self.file_path.exists():
            return False
        with z5py.N5File(str(self.file_path)) as f:
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
            NpzDataPath(self.file_path, internal_path=PurePosixPath(p))
            for p in globNpz(str(self.file_path), str(self.internal_path).lstrip("/"))
        ]

    def exists(self) -> bool:
        if not self.file_path.exists():
            return False
        return self.internal_path in NpzDataPath.list_internal_paths(self.file_path)


class FileDataset:
    """A collection of DataPaths that are present in the filesystem"""

    def __init__(self, data_paths: Sequence[DataPath]):
        if not data_paths:
            raise ValueError(f"Empty data paths")
        assert all(dp.exists() for dp in data_paths)
        self.data_paths = data_paths

    def __repr__(self) -> str:
        return f"<FileDataset {self.data_paths}>"

    def file_paths(self) -> List[Path]:
        return [dp.file_path for dp in self.data_paths]

    def archive_datapaths(self) -> Iterable[ArchiveDataPath]:
        return (dp for dp in self.data_paths if isinstance(dp, ArchiveDataPath))

    def is_under(self, path: Path):
        return all(dp.is_under(path) for dp in self.data_paths)

    def with_internal_path(self, internal_path: PurePosixPath) -> "FileDataset":
        seen_files: Set[Path] = set()
        updated_data_paths: List[DataPath] = []
        for dp in self.data_paths:
            if not isinstance(dp, ArchiveDataPath):
                updated_data_paths.append(dp)
                continue
            else:
                if dp.file_path in seen_files:
                    raise ValueError(
                        f"Switching to internal path {internal_path} would cause repeated DataPaths in {self}"
                    )
                seen_files.add(dp.file_path)
                new_dp = dp.with_internal_path(internal_path)
                if not new_dp.exists():
                    raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), str(new_dp))
                updated_data_paths.append(new_dp)
        return FileDataset(sorted(updated_data_paths))

    @classmethod
    def common_internal_paths(cls, dataset_paths: Iterable["FileDataset"]) -> List[PurePosixPath]:
        """Finds a list of common internal paths that exist in all ArchiveDataPaths contained within dataset_paths.
        Any of the returned paths can be used with any of the dataset_paths via the with_internal_path method"""
        out: Optional[Set[PurePosixPath]] = None
        for dataset_path in dataset_paths:
            for data_path in dataset_path.archive_datapaths():
                internal_paths = set(sibling.internal_path for sibling in data_path.siblings())
                if out is None:
                    out = internal_paths
                else:
                    out &= internal_paths
        return sorted(out or [])

    def archives(self) -> List[Path]:
        return sorted(set(dp.file_path for dp in self.data_paths if isinstance(dp, ArchiveDataPath)))

    def archive_siblings(self) -> Sequence[ArchiveDataPath]:
        out: List[ArchiveDataPath] = []
        for dp in self.data_paths:
            if isinstance(dp, ArchiveDataPath):
                out += dp.siblings()
        return out

    def uses_archive(self) -> bool:
        return any(isinstance(dp, ArchiveDataPath) for dp in self.data_paths)

    def archive_internal_paths(self) -> List[PurePosixPath]:
        return [dp.internal_path for dp in self.data_paths if isinstance(dp, ArchiveDataPath)]

    def to_strings(self) -> List[str]:
        return [str(dp) for dp in self.data_paths]

    @classmethod
    def split(cls, path: str, *, deglob: bool, cwd: Optional[Path] = None) -> "FileDataset":
        try:
            return cls.from_string(path, deglob=deglob)
        except FileNotFoundError:
            return FileDataset.from_strings(path.split(os.path.pathsep), deglob=deglob, cwd=cwd)

    @classmethod
    def from_strings(cls, paths: Iterable[str], *, deglob: bool, cwd: Optional[Path] = None) -> "FileDataset":
        dataset_paths = [FileDataset.from_string(path, deglob=deglob, cwd=cwd) for path in paths]
        return FileDataset([data_path for ds_path in dataset_paths for data_path in ds_path.data_paths])

    @classmethod
    def from_string(cls, path: str, *, deglob: bool, cwd: Optional[Path] = None) -> "FileDataset":
        effective_cwd = cwd or Path.cwd()
        data_path = DataPath.create(str(effective_cwd / path))
        if data_path.exists():
            return FileDataset([data_path])
        elif deglob:
            expanded = data_path.glob(smart=True)
            if expanded:
                return FileDataset(expanded)
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), path)
