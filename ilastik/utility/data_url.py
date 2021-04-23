from abc import ABC, abstractmethod
from typing import ClassVar, Dict, Mapping, Set, Tuple, TypeVar, Sequence, Optional, List, Type, Iterable, Union, cast
from pathlib import PurePosixPath, Path
import errno
import glob
import os
import re
from urllib.parse import urlencode, urlsplit, parse_qs
import enum

import numpy as np
from typing_extensions import final
import z5py
import h5py

from lazyflow.utility.pathHelpers import lsH5N5, globH5N5, globNpz

# pyright: strict


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
                return item
        raise ValueError(f"Could not convert {value} to a valid Scheme")

    @classmethod
    def contains(cls, value: str) -> bool:
        return value in [s.value for s in Scheme]

    def __str__(self) -> str:
        return self.value


DU = TypeVar("DU", bound="DataUrl")


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

    @classmethod
    @abstractmethod
    def from_string(cls: Type[DU], url: str) -> DU:
        raise NotImplementedError


class PrecomputedChunksUrl(DataUrl):
    @classmethod
    def from_string(cls, url: str) -> "PrecomputedChunksUrl":
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
    supported_extensions: ClassVar[Dict[str, Type["DataPath"]]] = {}

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.raw_file_path = str(self.file_path)
        super().__init__(scheme=Scheme.FILE, netloc="", path=PurePosixPath(file_path))

    def __init_subclass__(cls: Type["DataPath"], supported_extensions: List[str]):
        for suffix in supported_extensions:
            DataPath.supported_extensions[suffix] = cls

    def is_absolute(self) -> bool:
        return self.file_path.is_absolute()

    def is_under(self, path: Path):
        try:
            self.file_path.relative_to(path)
            return True
        except ValueError:
            return False

    @classmethod
    def get_handler(cls: Type[DP], extension: str) -> Type[DP]:
        extension = extension.lower().lstrip(".")
        if extension not in DataPath.supported_extensions:
            raise KeyError(f"Extension '{extension}' not supported")
        return cast(Type[DP], DataPath.supported_extensions[extension])

    @classmethod
    @abstractmethod
    def from_string(cls: Type[DP], url: str) -> DP:
        path = Path(url)
        while path != path.parent:
            try:
                handler = cls.get_handler(path.suffix)
                return handler.from_string(url)
            except KeyError:
                pass
            path = path.parent
        raise ValueError(f"Unsupported data format: {url}")

    @abstractmethod
    def exists(self) -> bool:
        pass

    @abstractmethod
    def relative_to(self: DU, other: Path) -> DU:
        pass

    @abstractmethod
    def glob(self, smart: bool = True) -> Sequence["DataPath"]:
        pass

    @classmethod
    @final
    def suffixes(cls) -> List[str]:
        return [suffix for suffix, klass in cls.supported_extensions.items() if issubclass(klass, cls)]

    def __hash__(self) -> int:
        return hash(self.raw_file_path)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return str(self) == str(other)

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return self.raw_file_path

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, DataPath):
            raise TypeError(
                f"'<' not supported between instances of '{self.__class__.__name__}' and '{other.__class__.__name__}'"
            )
        return str(self) < str(other)

    def as_posix(self) -> str:
        return str(self).replace("\\", "/")


class SimpleDataPath(
    DataPath,
    supported_extensions=[  # vigra.impex.listExtensions().split()
        "bmp",
        "exr",
        "gif",
        "hdr",
        "jpeg",
        "jpg",
        "pbm",
        "pgm",
        "png",
        "pnm",
        "ppm",
        "ras",
        "tif",
        "tiff",
        "xv",
        "npy",
    ],
):
    @classmethod
    def from_string(cls, url: str) -> "SimpleDataPath":
        return SimpleDataPath(Path(url))

    def exists(self) -> bool:
        return self.file_path.exists()

    def relative_to(self, other: Path) -> "SimpleDataPath":
        return SimpleDataPath(self.file_path.relative_to(other))

    def glob(self, smart: bool = True) -> Sequence["DataPath"]:
        if smart and self.exists():
            return [self]
        expanded_paths = [DataPath.from_string(p) for p in sorted(glob.glob(self.raw_file_path))]
        return expanded_paths


ADP = TypeVar("ADP", bound="ArchiveDataPath")


class ArchiveDataPath(DataPath, supported_extensions=[]):
    def __init__(self, file_path: Path, internal_path: PurePosixPath):
        if file_path.suffix.lower()[1:] not in self.suffixes():
            raise ValueError(f"External path for {self.__class__.__name__} must end in {self.suffixes()}")
        super().__init__(file_path=file_path)
        self.internal_path = PurePosixPath("/") / internal_path

    @classmethod
    @abstractmethod
    def from_paths(cls: Type[ADP], file_path: Path, internal_path: PurePosixPath) -> ADP:
        handler = cls.get_handler(file_path.suffix)
        return handler.from_paths(file_path, internal_path)

    def __str__(self) -> str:
        return str(self.file_path / self.internal_path.relative_to("/"))

    def with_internal_path(self: ADP, internal_path: PurePosixPath) -> ADP:
        return self.__class__(self.file_path, internal_path=internal_path)

    def siblings(self: ADP) -> List[ADP]:
        return [
            self.__class__(self.file_path, internal_path) for internal_path in self.list_internal_paths(self.file_path)
        ]

    @classmethod
    def common_internal_paths(cls, archives: Iterable[Path]) -> List[PurePosixPath]:
        """Finds a list of common internal paths that exist in all of 'archives'.
        Any of the returned paths can be used with any of archives via the with_internal_path method"""
        if not archives:
            return []
        internal_path_sets = [set(ArchiveDataPath.list_internal_paths(archive)) for archive in archives]
        return sorted(internal_path_sets[0].intersection(*internal_path_sets[1:]))

    @staticmethod
    def is_archive_path(path: Union[str, Path]) -> bool:
        try:
            ArchiveDataPath.split_archive_path(str(path))
            return True
        except ValueError:
            return False

    @staticmethod
    def split_archive_path(path: str) -> Tuple[Path, PurePosixPath]:
        path = path.replace("\\", "/")
        archive_suffix_regex = r"\.(" + "|".join(ArchiveDataPath.suffixes()) + ")(?:$|/)"
        components = re.split(archive_suffix_regex, str(path), maxsplit=1, flags=re.IGNORECASE)
        if len(components) != 3:
            raise ValueError(f"Path '{path}' does not look like an archive path")
        return (Path(components[0] + "." + components[1]), PurePosixPath("/") / components[2])

    @classmethod
    def from_string(cls: Type[ADP], url: str) -> ADP:
        file_path, internal_path = ArchiveDataPath.split_archive_path(url)
        if internal_path == PurePosixPath("/"):
            internal_paths = cls.list_internal_paths(file_path)
            if len(internal_paths) == 1:
                internal_path = internal_paths.pop()
            else:
                raise ValueError(f"Path to archive file has empty path: '{url}'")
        handler = cast(ADP, cls.get_handler(file_path.suffix))
        return handler.from_paths(file_path=file_path, internal_path=internal_path)

    def relative_to(self: ADP, other: Path) -> ADP:
        return self.__class__(self.file_path.relative_to(other), self.internal_path)

    def glob(self, smart: bool = True) -> Sequence["ArchiveDataPath"]:
        if smart and self.file_path.exists():
            externally_expanded_paths = [self]
        else:
            externally_expanded_paths = [
                self.__class__(file_path=Path(ep), internal_path=self.internal_path)
                for ep in glob.glob(str(self.file_path))
            ]

        all_paths: List["ArchiveDataPath"] = []
        for data_path in sorted(externally_expanded_paths):
            all_paths += [data_path] if (smart and data_path.exists()) else sorted(data_path.glob_internal())
        return all_paths

    @classmethod
    @abstractmethod
    def list_internal_paths(cls, path: Path) -> List[PurePosixPath]:
        return cls.get_handler(path.suffix).list_internal_paths(path)

    @abstractmethod
    def glob_internal(self: DU) -> Sequence[DU]:
        pass


class H5DataPath(ArchiveDataPath, supported_extensions=["h5", "hdf5", "ilp"]):
    @classmethod
    def from_paths(cls, file_path: Path, internal_path: PurePosixPath) -> "H5DataPath":
        return H5DataPath(file_path, internal_path)

    @classmethod
    def list_internal_paths(cls, path: Path) -> List[PurePosixPath]:
        with h5py.File(path, "r") as f:
            return sorted([PurePosixPath("/") / p["name"] for p in lsH5N5(f)])

    def glob_internal(self) -> Sequence["H5DataPath"]:
        with h5py.File(str(self.file_path), "r") as f:
            return [
                H5DataPath(self.file_path, internal_path=PurePosixPath(p))
                for p in sorted(globH5N5(f, str(self.internal_path).lstrip("/")) or [])
            ]

    def exists(self) -> bool:
        if not self.file_path.exists():
            return False
        with h5py.File(str(self.file_path), "r") as f:
            return self.internal_path.as_posix() in f


class N5DataPath(ArchiveDataPath, supported_extensions=["n5"]):
    @classmethod
    def from_paths(cls, file_path: Path, internal_path: PurePosixPath) -> "N5DataPath":
        return N5DataPath(file_path, internal_path)

    @classmethod
    def list_internal_paths(cls, path: Path) -> List[PurePosixPath]:
        with z5py.File(path, "r") as f:
            return sorted([PurePosixPath("/") / p["name"] for p in lsH5N5(f)])

    def glob_internal(self) -> Sequence["N5DataPath"]:
        with z5py.N5File(str(self.file_path)) as f:
            return [
                N5DataPath(self.file_path, internal_path=PurePosixPath(p))
                for p in sorted(globH5N5(f, str(self.internal_path).lstrip("/")) or [])
            ]

    def exists(self) -> bool:
        if not self.file_path.exists():
            return False
        with z5py.N5File(str(self.file_path)) as f:
            return self.internal_path.as_posix() in f


class NpzDataPath(ArchiveDataPath, supported_extensions=["npz"]):
    @classmethod
    def from_paths(cls, file_path: Path, internal_path: PurePosixPath) -> "NpzDataPath":
        return NpzDataPath(file_path, internal_path)

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


class Dataset:
    """A collection of DataPaths that are present in the filesystem"""

    def __init__(self, data_paths: Sequence[DataPath]):
        if not data_paths:
            raise ValueError(f"Empty data paths")
        if len(set(data_paths)) != len(data_paths):
            raise ValueError(f"Repeated data paths")
        for dp in data_paths:
            if not dp.exists():
                raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), str(dp))
            if not dp.is_absolute():
                raise ValueError(f"{dp} is not an absolute path")
        self.data_paths = data_paths

    def __repr__(self) -> str:
        return f"<Dataset {self.data_paths}>"

    def to_h5_data(self, legacy: bool, relative_prefix: Optional[Path] = None) -> Union[bytes, List[bytes]]:
        raw_paths = [(dp.relative_to(relative_prefix) if relative_prefix else dp).as_posix() for dp in self.data_paths]
        if legacy:
            return os.path.pathsep.join(raw_paths).encode("utf8")
        else:
            return [rp.encode("utf8") for rp in raw_paths]

    @classmethod
    def from_h5_data(cls, data: h5py.Dataset, legacy: bool, relative_prefix: Path) -> "Dataset":
        assert relative_prefix.is_absolute()
        if legacy:  # legacy filePath as a single (semi-)colon-separated-string
            filePath: str = data[()].decode("utf8").replace("\\", "/")  # type: ignore
            raw_paths: List[str] = [filePath]
        else:
            raw_paths: List[str] = [raw_bytes.decode("utf8") for raw_bytes in data]  # type: ignore
        return Dataset([DataPath.from_string(relative_prefix.joinpath(raw_path).as_posix()) for raw_path in raw_paths])

    def file_paths(self) -> List[Path]:
        return [dp.file_path for dp in self.data_paths]

    def internal_paths(self) -> List[PurePosixPath]:
        return [archive_datapath.internal_path for archive_datapath in self.archive_datapaths()]

    def archive_datapaths(self) -> Iterable[ArchiveDataPath]:
        return (dp for dp in self.data_paths if isinstance(dp, ArchiveDataPath))

    def suffixes(self) -> List[str]:
        return [fp.suffix for fp in self.file_paths()]

    def is_under(self, path: Path):
        return all(dp.is_under(path) for dp in self.data_paths)

    def with_internal_path(self, internal_path: PurePosixPath) -> "Dataset":
        seen_files: Set[Path] = set()
        updated_data_paths: List[DataPath] = []
        for dp in self.data_paths:
            if not isinstance(dp, ArchiveDataPath):
                updated_data_paths.append(dp)
            else:
                if dp.file_path in seen_files:
                    raise ValueError(
                        f"Switching to internal path {internal_path} would cause repeated DataPaths in {self}"
                    )
                seen_files.add(dp.file_path)
                new_dp = dp.with_internal_path(internal_path)
                updated_data_paths.append(new_dp)
        return Dataset(sorted(updated_data_paths))

    @classmethod
    def common_internal_paths(cls, datasets: Iterable["Dataset"]) -> List[PurePosixPath]:
        """Finds a list of common internal paths that exist in all ArchiveDataPaths contained within datasets.
        Any of the returned paths can be used with any of the datasets via the with_internal_path method"""
        archives = [archive.file_path for dataset in datasets for archive in dataset.archive_datapaths()]
        return ArchiveDataPath.common_internal_paths(archives)

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
    def split(cls, path: str, *, deglob: bool, cwd: Optional[Path] = None, separator: str = os.pathsep) -> "Dataset":
        try:
            return cls.from_string(path, deglob=deglob)
        except FileNotFoundError:
            return Dataset.from_strings(path.split(separator), deglob=deglob, cwd=cwd)

    @classmethod
    def from_strings(cls, paths: Iterable[str], *, deglob: bool, cwd: Optional[Path] = None) -> "Dataset":
        stack_paths = [Dataset.from_string(path, deglob=deglob, cwd=cwd) for path in paths]
        return Dataset([data_path for ds_path in stack_paths for data_path in ds_path.data_paths])

    @classmethod
    def from_string(cls, path: str, *, deglob: bool, cwd: Optional[Path] = None) -> "Dataset":
        effective_cwd = cwd or Path.cwd()
        path = str(effective_cwd / Path(path).expanduser())
        expanded: Sequence[DataPath] = []
        try:
            data_path = DataPath.from_string(path)
            if data_path.exists():
                return Dataset([data_path])
            if deglob:
                expanded = data_path.glob(smart=True)
        except ValueError:  # no extension recognized (e.g.: /my/files/*)
            if deglob:
                expanded = [DataPath.from_string(p) for p in glob.glob(path)]
        if expanded:
            return Dataset(expanded)
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), path)
