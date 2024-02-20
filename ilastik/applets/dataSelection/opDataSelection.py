###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
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
from abc import abstractmethod, ABC
import glob
import os
import uuid
from typing import List, Tuple, Dict, Optional, Union, Callable
from numbers import Number
import re
from pathlib import Path
import errno

import numpy
import vigra
from vigra import AxisTags
import h5py
import z5py
from ndstructs import Shape5D

from lazyflow.graph import InputSlot, OutputSlot, OperatorWrapper
from lazyflow.operators.ioOperators import OpStreamingH5N5Reader
from lazyflow.operators.ioOperators import OpInputDataReader
from lazyflow.operators.opArrayPiper import OpArrayPiper
from ilastik.applets.base.applet import DatasetConstraintError

from ilastik import Project
from ilastik.utility import OpMultiLaneWrapper
from ilastik.workflow import Workflow
from lazyflow.utility.io_util.RESTfulPrecomputedChunkedVolume import DEFAULT_LOWEST_SCALE_KEY
from lazyflow.utility.pathHelpers import splitPath, globH5N5, globNpz, PathComponents
from lazyflow.utility.helpers import get_default_axisordering
from lazyflow.operators.opReorderAxes import OpReorderAxes
from lazyflow.operators import OpMissingDataSource
from lazyflow.operators.ioOperators import OpH5N5WriterBigDataset
from lazyflow.graph import Graph, Operator


def getTypeRange(numpy_type):
    type_info = numpy.iinfo(numpy_type)
    return (type_info.min, type_info.max)


class CantSaveAsRelativePathsException(Exception):
    def __init__(self, file_path: str, base_dir: str):
        super().__init__(f"Can't represent {file_path} relative to {base_dir}")


class InconsistentAxisMetaException(Exception):
    def __init__(self, axistags: AxisTags, shape):
        if len(axistags) > len(shape):
            problem = "More axes than data dimensions."
        else:
            problem = "Some data dimensions have no axis interpretation."
        super().__init__(
            f"Unable to load: {problem}. Please check if all files have the same dimensionality.\n"
            f"Reported axes: {', '.join([tag.key for tag in axistags])}\n"
            f"Actual data dimensions: {', '.join([str(s) for s in shape])} (pixels/channels/timepoints)"
        )


class UnsuitedAxistagsException(Exception):
    def __init__(self, axistags: AxisTags, shape):
        if len(axistags) > len(shape):
            problem = "No data for some axes."
        else:
            problem = "Some data dimensions have no axis interpretation."
        super().__init__(
            f"The given axis interpretation does not match the data shape: {problem}\n"
            f"Specified axes: {', '.join([tag.key for tag in axistags])}\n"
            f"Actual data dimensions: {', '.join([str(s) for s in shape])} (pixels/channels/timepoints)"
        )


class DatasetInfo(ABC):
    def __init__(
        self,
        *,
        laneShape: Tuple,
        laneDtype: type,
        default_tags: AxisTags,  # inferred from dataset or another data lane
        axistags: AxisTags = None,  # given through datasetInfoEditorWidget or cmdline
        allowLabels: bool = True,
        subvolume_roi: Tuple = None,
        display_mode: str = "default",
        nickname: str = "",
        project_file: h5py.File = None,
        normalizeDisplay: bool = None,
        drange: Tuple[Number, Number] = None,
        working_scale: str = DEFAULT_LOWEST_SCALE_KEY,
        scale_locked: bool = False,
    ):
        if axistags and len(axistags) != len(laneShape):
            raise UnsuitedAxistagsException(axistags, laneShape)
        if not axistags and len(default_tags) != len(laneShape):
            raise InconsistentAxisMetaException(default_tags, laneShape)
        self.default_tags = default_tags
        self.axistags = axistags or default_tags
        self.laneShape = laneShape
        self.laneDtype = laneDtype
        if isinstance(self.laneDtype, numpy.dtype):
            self.laneDtype = numpy.sctypeDict[self.laneDtype.name]
        self.allowLabels = allowLabels
        self.subvolume_roi = subvolume_roi
        self.drange = drange
        self.display_mode = display_mode  # choices: default, grayscale, rgba, random-colortable, binary-mask.
        self.nickname = nickname
        self.project_file = project_file
        self.normalizeDisplay = (self.drange is not None) if normalizeDisplay is None else normalizeDisplay
        self.legacy_datasetId = self.generate_id()
        self.working_scale = working_scale
        self.scale_locked = scale_locked
        self.scales = {}  # {scale_key: scale_object}, dependent on data format

    @property
    def shape5d(self) -> Shape5D:
        return Shape5D(**dict(zip(self.axiskeys, self.laneShape)))

    @property
    @abstractmethod
    def legacy_location(self) -> str:
        pass

    def get_provider_slot(self, parent: Optional[Operator] = None, graph: Optional[Graph] = None) -> OutputSlot:
        metadata = {"display_mode": self.display_mode, "axistags": self.axistags}

        if self.drange is not None:
            metadata["drange"] = self.drange
        elif self.laneDtype == numpy.uint8:
            metadata["drange"] = (0, 255)
        if self.normalizeDisplay is not None:
            metadata["normalizeDisplay"] = self.normalizeDisplay
        if self.subvolume_roi is not None:
            metadata["subvolume_roi"] = self.subvolume_roi

        provider_slot = self.create_data_reader(parent=parent, graph=graph)
        provider_slot.meta.update(metadata)
        return provider_slot

    @abstractmethod
    def create_data_reader(self, parent: Optional[Operator] = None, graph: Optional[Graph] = None) -> OutputSlot:
        """Instantiate e.g. an OpInputDataReader that can read this DatasetInfo's data source.

        Return the OutputSlot that provides the data.

        Like with operators, either parent or graph must be provided, but not both"""
        pass

    def to_json_data(self) -> Dict:
        return {
            "axistags": self.axistags.toJSON().encode("utf-8"),
            "shape": self.laneShape,
            "allowLabels": self.allowLabels,
            "subvolume_roi": self.subvolume_roi,
            "display_mode": self.display_mode.encode("utf-8"),
            "nickname": self.nickname.encode("utf-8"),
            "normalizeDisplay": self.normalizeDisplay,
            "drange": self.drange,
            "working_scale": self.working_scale.encode("utf-8"),
            "scale_locked": self.scale_locked,
            "location": self.legacy_location.encode("utf-8"),  # legacy support
            "filePath": self.effective_path.encode("utf-8"),  # legacy support
            "datasetId": self.legacy_datasetId.encode("utf-8"),  # legacy support
            "__class__": self.__class__.__name__.encode("utf-8"),
        }

    @classmethod
    def from_h5_group(cls, data: h5py.Group, params: Dict = None):
        params = params or {}
        params.update(
            {
                "allowLabels": data["allowLabels"][()],
                "nickname": data["nickname"][()].decode("utf-8"),
                "project_file": data.file,
            }
        )
        if "axistags" in data:
            params["axistags"] = AxisTags.fromJSON(data["axistags"][()].decode("utf-8"))
        elif "axisorder" in data:  # legacy support
            axisorder = data["axisorder"][()].decode("utf-8")
            params["axistags"] = vigra.defaultAxistags(axisorder)

        if "subvolume_roi" in data:
            params["subvolume_roi"] = tuple(data["subvolume_roi"][()])
        if "normalizeDisplay" in data:
            params["normalizeDisplay"] = bool(data["normalizeDisplay"][()])
        if "drange" in data:
            params["drange"] = tuple(data["drange"])
        if "display_mode" in data:
            params["display_mode"] = data["display_mode"][()].decode("utf-8")
        if "working_scale" in data:
            try:
                params["working_scale"] = data["working_scale"][()].decode("utf-8")
            except AttributeError:
                # Support for projects created with ilastik 1.4.1b13
                saved_scale = int(data["working_scale"][()])
                if saved_scale == 0:  # 0 by default (in all project files).
                    params["working_scale"] = DEFAULT_LOWEST_SCALE_KEY
                elif saved_scale > 0:  # Precomputed dataset with non-default scale selected
                    from lazyflow.utility.io_util.RESTfulPrecomputedChunkedVolume import RESTfulPrecomputedChunkedVolume

                    url = params["url"]  # Should have url in this case
                    remote_source = RESTfulPrecomputedChunkedVolume(url.lstrip("precomputed://"))
                    scales = remote_source.get_scales_list_legacy()
                    params["working_scale"] = scales[saved_scale]["key"]
        if "scale_locked" in data:
            params["scale_locked"] = bool(data["scale_locked"][()])
        return cls(**params)

    def is_in_filesystem(self) -> bool:
        return False

    def is_hierarchical(self):
        return False

    @property
    @abstractmethod
    def display_string(self) -> str:
        pass

    @property
    def default_output_dir(self) -> Path:
        if self.project_file:
            return Path(self.project_file.filename).absolute().parent
        return Path.home()

    @classmethod
    def create_nickname(cls, expanded_paths: List[str]):
        components = [PathComponents(ep) for ep in expanded_paths]
        external_nickname = os.path.commonprefix(
            [re.sub(comp.extension + "$", "", comp.externalPath) for comp in components]
        )
        if external_nickname:
            external_nickname = Path(external_nickname).name
        else:
            external_nickname = "stack_at-" + components[0].filenameBase
        internal_nickname = os.path.commonprefix([comp.internalPath or "" for comp in components]).lstrip("/")
        nickname = external_nickname + ("-" + internal_nickname.replace("/", "-") if internal_nickname else "")
        return nickname

    @classmethod
    def generate_id(cls) -> str:
        return str(uuid.uuid1())

    @classmethod
    def expand_path(cls, file_path: str, cwd: str = None) -> List[str]:
        """Expands path with globs and colons into a list of absolute paths"""
        cwd = Path(cwd) if cwd else Path.cwd()
        pathComponents = [PathComponents(path) for path in splitPath(file_path)]
        expanded_paths = []
        missing_files = []
        for components in pathComponents:
            externalPath = cwd / Path(components.externalPath).expanduser()
            unglobbed_paths = glob.glob(str(externalPath))
            if not unglobbed_paths:
                missing_files.append(components.externalPath)
                continue
            for ext_path in unglobbed_paths:
                if not cls.fileHasInternalPaths(ext_path) or not components.internalPath:
                    expanded_paths.append(ext_path)
                    continue
                internal_paths = cls.globInternalPaths(ext_path, components.internalPath)
                expanded_paths.extend([os.path.join(ext_path, int_path) for int_path in internal_paths])

        if missing_files:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), os.path.pathsep.join(missing_files))
        return sorted(p.replace("\\", "/") for p in expanded_paths)

    @classmethod
    def globInternalPaths(cls, file_path: str, glob_str: str, cwd: str = None) -> List[str]:
        glob_str = glob_str.lstrip("/")
        internal_paths = set()
        for path in cls.expand_path(file_path, cwd=cwd):
            f = None
            try:
                if cls.pathIsNpz(path):
                    internal_paths |= set(globNpz(path, glob_str))
                    continue
                elif cls.pathIsHdf5(path):
                    f = h5py.File(path, "r")
                elif cls.pathIsN5(path):
                    f = z5py.N5File(path)  # FIXME
                else:
                    raise ValueError(f"{path} is not an 'n5' or 'h5' file")
                internal_paths |= set(globH5N5(f, glob_str))
            finally:
                if f is not None:
                    f.close()
        return sorted(internal_paths)

    @classmethod
    def pathIsHdf5(cls, path: Path) -> bool:
        return PathComponents(Path(path).as_posix()).extension in [".ilp", ".h5", ".hdf5"]

    @classmethod
    def pathIsNpz(cls, path: Path) -> bool:
        return PathComponents(Path(path).as_posix()).extension in [".npz"]

    @classmethod
    def pathIsN5(cls, path: Path) -> bool:
        return PathComponents(Path(path).as_posix()).extension in [".n5"]

    @classmethod
    def fileHasInternalPaths(cls, path: str) -> bool:
        return cls.pathIsHdf5(path) or cls.pathIsN5(path) or cls.pathIsNpz(path)

    @classmethod
    def getPossibleInternalPathsFor(cls, file_path: Path, min_ndim=2, max_ndim=5) -> List[str]:
        datasetNames = []

        def accumulateInternalPaths(name, val):
            if isinstance(val, (h5py.Dataset, z5py.dataset.Dataset)) and min_ndim <= len(val.shape) <= max_ndim:
                datasetNames.append("/" + name)

        if cls.pathIsHdf5(file_path):
            with h5py.File(file_path, "r") as f:
                f.visititems(accumulateInternalPaths)
        elif cls.pathIsN5(file_path):
            with z5py.N5File(file_path, mode="r+") as f:
                f.visititems(accumulateInternalPaths)

        return datasetNames

    @property
    def axiskeys(self):
        return "".join(tag.key for tag in self.axistags)

    def __str__(self):
        return str(self.__dict__)

    def importAsLocalDataset(
        self, project_file: h5py.File, progress_signal: Callable[[int], None] = lambda x: None
    ) -> str:
        project = Project(project_file)
        inner_path = project.local_data_group.name + "/" + self.legacy_datasetId
        if project_file.get(inner_path) is not None:
            return inner_path
        self.dumpToHdf5(h5_file=project_file, inner_path=inner_path, progress_signal=progress_signal)
        return inner_path

    def dumpToHdf5(
        self, h5_file: h5py.File, inner_path: str, progress_signal: Callable[[int], None] = lambda x: None
    ) -> str:
        progress_signal(0)
        try:
            h5_file.require_group(Path("/").joinpath(inner_path).parent.as_posix())
            graph = Graph()
            op_writer = OpH5N5WriterBigDataset(
                graph=graph,
                h5N5File=h5_file,
                h5N5Path=inner_path,
                CompressionEnabled=False,
                BatchSize=1,
                Image=self.get_provider_slot(graph=graph),
            )
            op_writer.progressSignal.subscribe(progress_signal)
            _ = op_writer.WriteImage.value  # reading this slot triggers the write
        finally:
            progress_signal(100)

    def is_stack(self) -> bool:
        return len(splitPath(self.effective_path)) > 1


class ProjectInternalDatasetInfo(DatasetInfo):
    def __init__(self, *, inner_path: str, project_file: h5py.File, nickname: str = "", **info_kwargs):
        self.inner_path = inner_path
        self.project_file = project_file
        self.dataset = project_file[inner_path]
        if "axistags" in self.dataset.attrs:
            default_tags = vigra.AxisTags.fromJSON(self.dataset.attrs["axistags"])
        else:
            default_tags = vigra.defaultAxistags(get_default_axisordering(self.dataset.shape))
        super().__init__(
            default_tags=default_tags,
            laneShape=self.dataset.shape,
            laneDtype=self.dataset.dtype,
            nickname=nickname or os.path.split(self.inner_path)[-1],
            project_file=project_file,
            **info_kwargs,
        )
        self.legacy_datasetId = Path(inner_path).name

    @property
    def legacy_location(self) -> str:
        return "ProjectInternal"

    def to_json_data(self) -> Dict:
        out = super().to_json_data()
        out["inner_path"] = self.inner_path.encode("utf-8")
        out["fromstack"] = True  # legacy support
        return out

    @classmethod
    def from_h5_group(cls, data: h5py.Group, params: Dict = None):
        params = params or {}
        if "datasetId" in data and "inner_path" not in data:  # legacy format
            dataset_id = data["datasetId"][()].decode("utf-8")
            inner_path = None

            def grab_inner_path(h5_path, dataset):
                nonlocal inner_path
                if h5_path.endswith(dataset_id):
                    inner_path = h5_path

            data.file.visititems(grab_inner_path)
            params["inner_path"] = inner_path
        else:
            params["inner_path"] = data["inner_path"][()].decode("utf-8")
        return super().from_h5_group(data, params)

    @property
    def effective_path(self):
        return self.inner_path

    @property
    def display_string(self) -> str:
        return "Project Internal: " + self.inner_path

    def create_data_reader(self, parent: Optional[Operator] = None, graph: Optional[Graph] = None) -> OutputSlot:
        opReader = OpStreamingH5N5Reader(parent=parent, graph=graph)
        opReader.H5N5File.setValue(self.project_file)
        opReader.InternalPath.setValue(self.inner_path)
        return opReader.OutputImage

    @property
    def internal_paths(self) -> List[str]:
        return []


class PreloadedArrayDatasetInfo(DatasetInfo):
    def __init__(self, *, preloaded_array: numpy.ndarray, axistags: AxisTags = None, nickname: str = "", **info_kwargs):
        self.preloaded_array = vigra.taggedView(
            preloaded_array, axistags or get_default_axisordering(preloaded_array.shape)
        )
        super().__init__(
            nickname=nickname or "preloaded-{}-array".format(self.preloaded_array.dtype.name),
            default_tags=self.preloaded_array.axistags,
            laneShape=preloaded_array.shape,
            laneDtype=preloaded_array.dtype,
            **info_kwargs,
        )

    @property
    def effective_path(self) -> str:
        return "Preloaded Array"

    @property
    def legacy_location(self) -> str:
        return "PreloadedArray"

    def to_json_data(self) -> Dict:
        out = super().to_json_data()
        out["preloaded_array"] = self.preloaded_array
        return out

    @property
    def display_string(self) -> str:
        return "Preloaded Array"

    def create_data_reader(self, parent: Optional[Operator] = None, graph: Optional[Graph] = None) -> OutputSlot:
        opReader = OpArrayPiper(parent=parent, graph=graph)
        opReader.Input.setValue(self.preloaded_array)
        return opReader.Output


class DummyDatasetInfo(DatasetInfo):
    """Special DatasetInfo for datasets that can't be found in headless mode"""

    def __init__(self, **info_kwargs):
        super().__init__(**info_kwargs)

    @property
    def legacy_location(self) -> str:
        return "Outer Space"

    @property
    def effective_path(self) -> str:
        return "Outer Space"

    @property
    def display_string(self) -> str:
        return "Dummy Zero Array"

    def to_json_data(self) -> Dict:
        raise NotImplementedError("Dummy Slots should not be serialized!")

    def create_data_reader(self, parent: Optional[Operator] = None, graph: Optional[Graph] = None) -> OutputSlot:
        opZero = OpMissingDataSource(
            shape=self.laneShape, dtype=self.laneDtype, axistags=self.axistags, parent=parent, graph=graph
        )
        return opZero.Output

    @classmethod
    def from_h5_group(cls, data: h5py.Group, params: Dict = None):
        laneShape = tuple(data["shape"])
        default_tags = get_default_axisordering(laneShape)

        params = params or {}
        if "laneShape" not in params:
            params["laneShape"] = laneShape
        if "default_tags" not in params:
            params["default_tags"] = default_tags
        if "laneDtype" not in params:
            params["laneDtype"] = numpy.uint8
        return super().from_h5_group(data, params)


class MultiscaleUrlDatasetInfo(DatasetInfo):
    def __init__(self, *, url: str, nickname: str = "", **info_kwargs):
        self.url = url
        op_reader = OpInputDataReader(graph=Graph(), FilePath=self.url)
        meta = op_reader.Output.meta.copy()
        super().__init__(
            default_tags=meta.axistags,
            nickname=nickname or self._nickname_from_url(url),
            laneShape=meta.shape,
            laneDtype=meta.dtype,
            **info_kwargs,
        )

    @property
    def legacy_location(self) -> str:
        return "FileSystem"

    @property
    def effective_path(self) -> str:
        return self.url

    def create_data_reader(self, parent: Optional[Operator] = None, graph: Optional[Graph] = None) -> OutputSlot:
        scale_input_slot = getattr(parent, "ActiveScale", None)
        op_reader = OpInputDataReader(parent=parent, graph=graph, FilePath=self.url, ActiveScale=scale_input_slot)
        return op_reader.Output

    @property
    def display_string(self):
        return "Remote: " + self.url

    def to_json_data(self) -> Dict:
        out = super().to_json_data()
        out["url"] = self.url
        return out

    @classmethod
    def from_h5_group(cls, group: h5py.Group, params: Dict = None):
        params = params or {}
        if "url" not in params:
            params["url"] = group["filePath"][()].decode()
        return super().from_h5_group(group, params)

    @staticmethod
    def _nickname_from_url(url: str) -> str:
        last_url_component = url.rstrip("/").rpartition("/")[2]
        filename_safe = re.sub(r"[^a-zA-Z0-9_.-]", "_", last_url_component)
        return filename_safe


class UrlDatasetInfo(MultiscaleUrlDatasetInfo):
    """
    Legacy variant of MultiscaleUrlDatasetInfo to support loading HBP-mode projects
    with Neuroglancer Precomputed data sources.
    Such old project files contain a UrlDatasetInfo missing the working_scale and scale_locked attributes.
    The working scale would always be the dataset's original resolution (last index in the list ilastik-internally),
    and since scale change was not possible, the scale would inherently be locked.
    """

    def to_json_data(self) -> Dict:
        """
        Returns a serializable dict that claims to represent, and is equivalent to, a MultiscaleUrlDatasetInfo.
        Saving this prevents older ilastik versions from loading the project file (since they only know UrlDatasetInfo),
        and potentially misinterpreting what we have stored.
        As of 1.4.1, there would not actually be any incompatibility. But we do not want to guarantee this in the future,
        therefore we forcefully break it.
        """
        out = super().to_json_data()
        out["__class__"] = "MultiscaleUrlDatasetInfo".encode()
        return out

    @classmethod
    def from_h5_group(cls, group: h5py.Group, params: Dict = None):
        """
        Returns a deserialized DatasetInfo dict equivalent to a dict from a MultiscaleUrlDatasetInfo
        """
        from lazyflow.utility.io_util.RESTfulPrecomputedChunkedVolume import RESTfulPrecomputedChunkedVolume

        deserialized = super().from_h5_group(group)
        remote_source = RESTfulPrecomputedChunkedVolume(deserialized.url.lstrip("precomputed://"))
        deserialized.nickname = cls._nickname_from_url(deserialized.nickname)
        deserialized.working_scale = remote_source.highest_resolution_key
        deserialized.scale_locked = True
        return deserialized


class FilesystemDatasetInfo(DatasetInfo):
    def __init__(
        self,
        *,
        filePath: str,
        project_file: h5py.File = None,
        sequence_axis: str = None,
        nickname: str = "",
        drange: Tuple[Number, Number] = None,
        **info_kwargs,
    ):
        self.sequence_axis = sequence_axis  # Only relevant for file series: Axis along which to stack files
        self.base_dir = str(Path(project_file.filename).absolute().parent) if project_file else os.getcwd()
        assert os.path.isabs(self.base_dir)
        self.expanded_paths = self.expand_path(filePath, cwd=self.base_dir)
        assert len(self.expanded_paths) == 1 or self.sequence_axis
        if len({PathComponents(ep).extension for ep in self.expanded_paths}) > 1:
            raise ValueError(f"Multiple extensions unsupported as a single data source: {self.expanded_paths}")
        self.filePath = os.path.pathsep.join(self.expanded_paths)

        op_reader = OpInputDataReader(
            graph=Graph(), WorkingDirectory=self.base_dir, FilePath=self.filePath, SequenceAxis=self.sequence_axis
        )
        meta = op_reader.Output.meta.copy()
        op_reader.cleanUp()

        super().__init__(
            default_tags=meta.axistags,
            nickname=nickname or self.create_nickname(self.expanded_paths),
            laneShape=meta.shape,
            laneDtype=meta.dtype,
            drange=drange or meta.get("drange"),
            project_file=project_file,
            **info_kwargs,
        )

    @property
    def legacy_location(self) -> str:
        return "FileSystem"

    @property
    def default_output_dir(self) -> Path:
        first_external_path = PathComponents(self.filePath.split(os.path.pathsep)[0]).externalPath
        return Path(first_external_path).parent

    def create_data_reader(self, parent: Optional[Operator] = None, graph: Optional[Graph] = None) -> OutputSlot:
        op_reader = OpInputDataReader(
            parent=parent,
            graph=graph,
            WorkingDirectory=self.base_dir,
            FilePath=self.filePath,
            SequenceAxis=self.sequence_axis,
        )
        return op_reader.Output

    @classmethod
    def from_h5_group(cls, data: h5py.Group):
        params = {"project_file": data.file, "filePath": data["filePath"][()].decode("utf-8")}
        return super().from_h5_group(data, params)

    def isHdf5(self) -> bool:
        return any(self.pathIsHdf5(ep) for ep in self.external_paths)

    def isNpz(self) -> bool:
        return any(self.pathIsNpz(ep) for ep in self.external_paths)

    def isN5(self) -> bool:
        return any(self.pathIsN5(ep) for ep in self.external_paths)

    def is_hierarchical(self):
        return self.isHdf5() or self.isNpz() or self.isN5()

    def is_in_filesystem(self) -> bool:
        return True

    @property
    def display_string(self):
        return "Absolute Link: " + self.effective_path

    @property
    def effective_path(self) -> str:
        return os.path.pathsep.join(self.expanded_paths)

    def is_under_project_file(self) -> bool:
        try:
            self.get_relative_paths()
            return True
        except CantSaveAsRelativePathsException:
            return False

    def get_relative_paths(self) -> List[str]:
        external_paths = [Path(PathComponents(path).externalPath) for path in self.expanded_paths]
        try:
            return sorted([str(ep.absolute().relative_to(self.base_dir)) for ep in external_paths])
        except ValueError:
            raise CantSaveAsRelativePathsException(self.filePath, self.base_dir)

    @property
    def external_paths(self) -> List[str]:
        return [PathComponents(ep).externalPath for ep in self.expanded_paths]

    @property
    def internal_paths(self) -> List[str]:
        return [PathComponents(ep).internalPath for ep in self.expanded_paths]

    @property
    def file_extensions(self) -> List[str]:
        return [PathComponents(ep).extension for ep in self.expanded_paths]

    def getPossibleInternalPaths(self):
        possible_internal_paths = set()
        for expanded_path in self.expanded_paths:
            external_path = PathComponents(expanded_path).externalPath
            possible_internal_paths |= set(self.getPossibleInternalPathsFor(external_path))
        return possible_internal_paths


class RelativeFilesystemDatasetInfo(FilesystemDatasetInfo):
    def __init__(self, **fs_info_kwargs):
        super().__init__(**fs_info_kwargs)
        if not self.is_under_project_file():
            raise CantSaveAsRelativePathsException(self.filePath, self.base_dir)

    @classmethod
    def create_or_fallback_to_absolute(cls, *args, **kwargs):
        try:
            return cls(*args, **kwargs)
        except CantSaveAsRelativePathsException:
            return FilesystemDatasetInfo(*args, **kwargs)

    @property
    def display_string(self):
        return "Relative Link: " + self.effective_path

    @property
    def effective_path(self) -> str:
        return os.path.pathsep.join(str(Path(p).relative_to(self.base_dir)) for p in self.expanded_paths)


class OpDataSelection(Operator):
    """
    The primary operator for handling a single dataset, e.g. raw data or a prediction mask.
    """

    name = "OpDataSelection"
    category = "Top-level"

    SupportedExtensions = OpInputDataReader.SupportedExtensions

    # Inputs
    RoleName = InputSlot(stype="string", value="")
    ProjectFile = InputSlot(stype="object", optional=True)  # : The project hdf5 File object (already opened)
    # : The internal path to the hdf5 group where project-local datasets are stored within the project file
    ProjectDataGroup = InputSlot(stype="string", optional=True)
    WorkingDirectory = InputSlot(stype="filestring")  # : The filesystem directory where the project file is located
    Dataset = InputSlot(stype="object")  # : A DatasetInfo object
    ActiveScale = InputSlot(stype="string", optional=True)  # : The currently selected scale (for multiscale data)

    # Outputs
    Image = OutputSlot()  # : The output image
    AllowLabels = OutputSlot(stype="bool")  # : A bool indicating whether or not this image can be used for training

    ImageName = OutputSlot(stype="string")  # : The name of the output image

    def __init__(
        self,
        forceAxisOrder: List[str] = ["tczyx"],
        ProjectFile: h5py.File = None,
        ProjectDataGroup=None,
        WorkingDirectory=None,
        Dataset: DatasetInfo = None,
        *args,
        **kwargs,
    ):
        """
        forceAxisOrder: How to auto-reorder the input data before connecting it to the rest of the workflow.
                        Should be a list of input orders that are allowed by the workflow
                        For example, if the workflow can handle 2D and 3D, you might pass ['yxc', 'zyxc'].
                        If it only handles exactly 5D, you might pass 'tzyxc', assuming that's how you wrote the
                        workflow.
                        todo: move toward 'tczyx' standard.
        """
        super().__init__(*args, **kwargs)
        self.forceAxisOrder = forceAxisOrder

        # If the gui calls disconnect() on an input slot without replacing it with something else,
        #  we still need to clean up the internal operator that was providing our data.
        self.ProjectFile.notifyUnready(self._clean_up_all_children)
        self.ProjectFile.setOrConnectIfAvailable(ProjectFile)

        self.ProjectDataGroup.notifyUnready(self._clean_up_all_children)
        self.ProjectDataGroup.setOrConnectIfAvailable(ProjectDataGroup)

        self.WorkingDirectory.notifyUnready(self._clean_up_all_children)
        self.WorkingDirectory.setOrConnectIfAvailable(WorkingDirectory)

        self.Dataset.notifyUnready(self._clean_up_all_children)
        self.Dataset.setOrConnectIfAvailable(Dataset)

    def _clean_up_all_children(self, *args) -> None:
        self.Image.disconnect()
        # This relies on self.children being in the same order as the graph.
        for op in reversed(self.children):
            op.cleanUp()

    def setupOutputs(self):
        self._clean_up_all_children()
        datasetInfo: DatasetInfo = self.Dataset.value

        try:
            data_provider = datasetInfo.get_provider_slot(parent=self)
            if "x" not in data_provider.meta.axistags or "y" not in data_provider.meta.axistags:
                raise DatasetConstraintError(
                    "DataSelection", "Data must always have at leaset the axes x and y for ilastik to work."
                )

            role_name = self.RoleName.value
            if datasetInfo.shape5d.c > 1:
                meta = {"channel_names": [f"{role_name}-{i}" for i in range(datasetInfo.shape5d.c)]}
            else:
                meta = {"channel_names": [role_name]}
            data_provider.meta.update(meta)
            if data_provider.meta.scales:
                datasetInfo.laneShape = data_provider.meta.shape
                datasetInfo.scales = data_provider.meta.scales
                if datasetInfo.working_scale == DEFAULT_LOWEST_SCALE_KEY:
                    # datasetInfo.working_scale may be saved to the project file, so we want a real key here
                    # if we didn't already load one from the file.
                    datasetInfo.working_scale = data_provider.meta.lowest_scale

            output_order = self._get_output_axis_order(data_provider)
            # Export applet assumes this OpReorderAxes exists.
            op5 = OpReorderAxes(parent=self, AxisOrder=output_order, Input=data_provider)
            self.Image.connect(op5.Output)
            self.AllowLabels.setValue(datasetInfo.allowLabels)
            if self.Image.meta.nickname is not None:
                datasetInfo.nickname = self.Image.meta.nickname
            self.ImageName.setValue(datasetInfo.nickname)

        except:
            self._clean_up_all_children()
            raise

    def _get_output_axis_order(self, data_provider: OutputSlot) -> str:
        if self.forceAxisOrder:
            assert isinstance(self.forceAxisOrder, list), "forceAxisOrder should be a *list* of preferred axis orders"
            # Forced axis order must include all non-singleton axes from the original dataset.
            required_axes = {axis for axis, size in data_provider.meta.getTaggedShape().items() if size > 1}
            compliant_orders = [o for o in self.forceAxisOrder if required_axes.issubset(set(o))]
            output_order = min(compliant_orders, default=(), key=len)  # Pick the shortest one
            if not output_order:
                msg = (
                    f"The axes of your dataset ({data_provider.meta.getAxisKeys()}) are not compatible with "
                    f"any of the allowed axis configurations used by this workflow ({self.forceAxisOrder})."
                )
                raise DatasetConstraintError("DataSelection", msg)
        else:
            output_order = data_provider.meta.getAxisKeys()
        if "c" not in output_order:
            output_order += "c"
        output_order = "".join(output_order)
        return output_order

    def propagateDirty(self, slot, subindex, roi):
        # Output slots are directly connected to internal operators
        pass


class OpDataSelectionGroup(Operator):
    """
    Handles a single data lane, i.e. a row, across the different tabs in the input data table.
    This primarily means managing copies of slots for all roles (Raw Data, Prediction Mask,...) in the lane.
    User actions that affect all roles in the lane also interact with this operator,
    e.g. changing axistags (through DatasetInfos passed into .configure()).
    """

    # Inputs
    ProjectFile = InputSlot(stype="object", optional=True)
    ProjectDataGroup = InputSlot(stype="string", optional=True)  # "Group" here refers to hdf5-group
    WorkingDirectory = InputSlot(stype="filestring")
    DatasetRoles = InputSlot(stype="object")

    # Must mark as optional because not all subslots are required.
    DatasetGroup = InputSlot(stype="object", level=1, optional=True)  # "Group" as in group of slots
    ActiveScaleGroup = InputSlot(stype="string", level=1, optional=True, value=DEFAULT_LOWEST_SCALE_KEY)

    # Outputs
    ImageGroup = OutputSlot(level=1)  # "Group" as in group of slots
    Image = OutputSlot()  # Alias for ImageGroup[0]

    AllowLabels = OutputSlot(stype="bool")  # Taken from dataset in first role (usually Raw Data)

    # Must be the LAST slot declared in this class.
    # When the shell detects that this slot has been resized,
    #  it assumes all the others have already been resized.
    ImageName = OutputSlot()  # Taken from dataset in first role (usually Raw Data)

    def __init__(self, forceAxisOrder=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._opDatasets = None
        self._roles = []
        self._forceAxisOrder = forceAxisOrder

        def handleNewRoles(*args):
            self.DatasetGroup.resize(len(self.DatasetRoles.value))
            self.ActiveScaleGroup.resize(len(self.DatasetRoles.value))

        self.DatasetRoles.notifyReady(handleNewRoles)

    @property
    def role_names(self) -> List[str]:
        return self.DatasetRoles.value

    def get_role_info_slot(self, role: Union[str, int]) -> InputSlot:
        role_index = role if isinstance(role, int) else self.role_names.index(role)
        return self.DatasetGroup[role_index]

    def get_dataset_info(self, role: Union[str, int]) -> Optional[DatasetInfo]:
        slot = self.get_role_info_slot(role)
        if not slot.ready():
            return None
        return slot.value

    def get_infos(self) -> Dict[str, Optional[DatasetInfo]]:
        return {role_name: self.get_dataset_info(role_name) for role_name in self.role_names}

    def get_axistags(self) -> Dict[str, Optional[AxisTags]]:
        return {role_name: info and info.axistags for role_name, info in self.get_infos().items()}

    def configure(self, infos: Dict[str, DatasetInfo]):
        for role_index, role_name in enumerate(self.role_names):
            if role_name in infos:
                self.DatasetGroup[role_index].setValue(infos[role_name])

    def setupOutputs(self):
        # Create internal operators
        if self.DatasetRoles.value != self._roles:
            self._roles = self.DatasetRoles.value
            # Clean up the old operators
            self.ImageGroup.disconnect()
            self.Image.disconnect()
            if self._opDatasets is not None:
                self._opDatasets.cleanUp()

            self._opDatasets = OperatorWrapper(
                OpDataSelection,
                parent=self,
                operator_kwargs={"forceAxisOrder": self._forceAxisOrder},
                broadcastingSlotNames=["ProjectFile", "ProjectDataGroup", "WorkingDirectory"],
            )
            self.ImageGroup.connect(self._opDatasets.Image)
            self._opDatasets.Dataset.connect(self.DatasetGroup)
            self._opDatasets.ProjectFile.connect(self.ProjectFile)
            self._opDatasets.ProjectDataGroup.connect(self.ProjectDataGroup)
            self._opDatasets.WorkingDirectory.connect(self.WorkingDirectory)
            self._opDatasets.ActiveScale.connect(self.ActiveScaleGroup)

        for role_index, opDataSelection in enumerate(self._opDatasets):
            opDataSelection.RoleName.setValue(self._roles[role_index])

        if len(self._opDatasets.Image) > 0:
            self.Image.connect(self._opDatasets.Image[0])
            self.ImageName.connect(self._opDatasets.ImageName[0])
            self.AllowLabels.connect(self._opDatasets.AllowLabels[0])
        else:
            self.Image.disconnect()
            self.ImageName.disconnect()
            self.AllowLabels.disconnect()
            self.Image.meta.NOTREADY = True
            self.ImageName.meta.NOTREADY = True
            self.AllowLabels.meta.NOTREADY = True

    def execute(self, slot, subindex, rroi, result):
        assert False, "Unknown or unconnected output slot: {}".format(slot.name)

    def propagateDirty(self, slot, subindex, roi):
        # Output slots are directly connected to internal operators
        pass


class OpMultiLaneDataSelectionGroup(OpMultiLaneWrapper):
    """
    Wraps OpDataSelectionGroup, the single-lane operator that handles different roles.
    Lanes correspond to rows in the input data table. Each lane may receive input data in more than one role,
    corresponding to tabs in the input data table (e.g. Raw Data, Prediction Maps).
    """

    def __init__(self, forceAxisOrder=False, *args, **kwargs):
        kwargs.update(
            {
                "operator_kwargs": {"forceAxisOrder": forceAxisOrder},
                "broadcastingSlotNames": ["ProjectFile", "ProjectDataGroup", "WorkingDirectory", "DatasetRoles"],
            }
        )
        super().__init__(OpDataSelectionGroup, *args, **kwargs)

        # 'value' slots
        assert self.ProjectFile.level == 0
        assert self.ProjectDataGroup.level == 0
        assert self.WorkingDirectory.level == 0
        assert self.DatasetRoles.level == 0

        # Indexed by [lane][role]
        assert self.DatasetGroup.level == 2, "DatasetGroup is supposed to be a level-2 slot, indexed by [lane][role]"

    def addLane(self, laneIndex) -> OpDataSelectionGroup:
        """Reimplemented from base class."""
        numLanes = len(self.innerOperators)

        # Only add this lane if we don't already have it
        # We might be called from within the context of our own insertSlot signal.
        if numLanes == laneIndex:
            super().addLane(laneIndex)
        return self.get_lane(laneIndex)

    def removeLane(self, laneIndex, finalLength):
        """Reimplemented from base class."""
        numLanes = len(self.innerOperators)
        if numLanes > finalLength:
            super().removeLane(laneIndex, finalLength)

    @property
    def workflow(self) -> Workflow:
        return self.parent

    @property
    def role_names(self) -> List[str]:
        return self.DatasetRoles.value

    def pushLane(self, role_infos: Dict[str, DatasetInfo]):
        original_num_lanes = self.num_lanes
        try:
            lane = self.addLane(self.num_lanes)
            lane.configure(infos=role_infos)
            self.workflow.handleNewLanesAdded()
        except Exception as e:
            self.removeLane(original_num_lanes, original_num_lanes)
            raise e

    def dropLastLane(self):
        self.removeLane(self.num_lanes - 1, self.num_lanes - 1)

    @property
    def num_lanes(self) -> int:
        return len(self.innerOperators)

    def get_lane(self, lane_idx: int) -> OpDataSelectionGroup:
        return self.innerOperators[lane_idx]

    def lock_scale_selection(self):
        for lane in self.innerOperators:
            for info_slot in lane.DatasetGroup:
                if not info_slot.ready():
                    continue
                info: DatasetInfo = info_slot.value
                if info.scales:
                    info.scale_locked = True
