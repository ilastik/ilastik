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
import glob
import os
import uuid
import copy
from enum import Enum, unique
from typing import List, Iterable, Tuple, Callable
from numbers import Number
import re
import functools
from pathlib import Path

import numpy
import vigra
import h5py
import z5py

from lazyflow.graph import Operator, InputSlot, OutputSlot, OperatorWrapper
from lazyflow.metaDict import MetaDict
from lazyflow.operators.ioOperators import OpStreamingH5N5Reader
from lazyflow.operators.ioOperators import OpInputDataReader, OpH5N5WriterBigDataset
from lazyflow.operators.valueProviders import OpMetadataInjector, OpZeroDefault
from lazyflow.operators.opArrayPiper import OpArrayPiper
from ilastik.applets.base.applet import DatasetConstraintError

from ilastik.utility import OpMultiLaneWrapper
from lazyflow.graph import Graph
from lazyflow.utility import PathComponents, isUrl, make_absolute
from lazyflow.utility.pathHelpers import splitPath, globH5N5, globNpz
from lazyflow.utility.helpers import get_default_axisordering
from lazyflow.operators.opReorderAxes import OpReorderAxes
from lazyflow.graph import Graph

def getTypeRange(numpy_type):
    type_info = numpy.iinfo(numpy_type)
    return (type_info.min, type_info.max)

class DatasetInfo(object):
    """
    Struct-like class for describing dataset info.
    """
    @unique
    class Location(Enum):
        FileSystem = 0 #deprecated
        ProjectInternal = 1
        PreloadedArray = 2
        FileSystemRelativePath = 3
        FileSystemAbsolutePath = 4

    def __init__(self, *,
                 filepath:str=None,
                 project_file:h5py.File=None,
                 preloaded_array=None,
                 sequence_axis=None, allowLabels=True,
                 subvolume_roi=None, location=None,
                 axistags=None, fill_in_dummy_axes:bool=False,
                 display_mode='default',
                 nickname='', original_axistags=None,
                 normalizeDisplay:bool=None, drange:Tuple[Number, Number]=None,
                 jsonNamespace=None,
    ):
        """
        filepath: may be a globstring or a full hdf5 path+dataset

        jsonNamespace: If provided, overrides default settings after filepath is applied

        preloaded_array: Instead of providing a filepath to read from, a pre-loaded array can be directly provided.
                         In that case, you'll probably want to configure the axistags member, or provide a tagged
                         vigra.VigraArray.

        sequence_axis: Axis along which to stack (only applicable for stacks).
        """
        assert (preloaded_array is not None) ^ bool(filepath), "Provide either preloaded_array or filepath"
        self.filePath = filepath or ''
        self.preloaded_array = preloaded_array
        self.project_file = project_file
        # OBSOLETE: Whether or not this dataset should be used for training a classifier.
        self.allowLabels = allowLabels
        self.sequenceAxis = sequence_axis
        self.original_axistags = original_axistags
        self.subvolume_roi = subvolume_roi
        self.display_mode = display_mode  # choices: default, grayscale, rgba, random-colortable, binary-mask.
        self.original_paths = []
        self.location = location
        self.drange = drange
        self.normalizeDisplay = (self.drange is not None) if normalizeDisplay is None else normalizeDisplay
        self.expanded_paths = []
        self.base_dir = str(Path(project_file.filename).absolute().parent) if project_file else os.getcwd()
        assert os.path.isabs(self.base_dir) #FIXME: if file_project was opened as a relative path, this would break

        if location == self.Location.PreloadedArray:
            assert preloaded_array is not None
            self.preloaded_array = vigra.taggedView(preloaded_array, axistags or get_default_axisordering(preloaded_array.shape))
            self.nickname = "preloaded-{}-array".format(self.preloaded_array.dtype.name)
            self.laneShape = preloaded_array.shape
            self.laneDtype = preloaded_array.dtype
            self.location = self.Location.PreloadedArray
            default_tags = getattr(self.preloaded_array, 'axistags')
        elif location == self.Location.ProjectInternal:
            dataset = project_file[filepath]
            default_tags = vigra.AxisTags.fromJSON(dataset.attrs['axistags'])
            self.laneShape = dataset.shape
            self.laneDtype = dataset.dtype
            self.nickname = nickname
        elif filepath and not isUrl(filepath):
            self.original_paths = splitPath(filepath)
            self.expanded_paths = self.expand_path(filepath, cwd=self.base_dir)
            assert len(self.expanded_paths) == 1 or self.sequenceAxis
            if len({PathComponents(ep).extension for ep in self.expanded_paths}) > 1:
                raise Exception(f"Multiple extensions unsupported as a single data source: {self.expanded_paths}")
            self.nickname = self.create_nickname(self.expanded_paths)
            self.filePath = os.path.pathsep.join(self.expanded_paths)
            op_reader = OpInputDataReader(graph=Graph(),
                                          WorkingDirectory=self.base_dir,
                                          FilePath=self.filePath,
                                          SequenceAxis=self.sequenceAxis)
            meta = op_reader.Output.meta
            default_tags = meta.axistags
            self.laneShape = meta.shape
            self.laneDtype = meta.dtype
            self.drange = drange or meta.get('drange')
        else: # path is url
            self.filePath = filepath
            self.expanded_paths = [filepath]

        if isinstance(self.laneDtype, numpy.dtype):
            self.laneDtype = numpy.typeDict[self.laneDtype.name]

        if jsonNamespace is not None:
            self.updateFromJson(jsonNamespace)
        if nickname:
            self.nickname = nickname

        self.axistags = axistags or default_tags
        if len(self.axistags) != len(self.laneShape):
            if not fill_in_dummy_axes:
                raise Exception("Axistags {self.axistags} don't fit data shape {self.laneShape}")
            default_keys = [tag.key for tag in default_tags]
            tagged_shape = {k: v for k, v in zip(default_keys, self.laneShape)}
            squeezed_shape = {k: v for k, v in tagged_shape.items() if v != 1}
            requested_keys = [tag.key for tag in axistags]
            if len(requested_keys) == len(squeezed_shape):
                dummy_axes = [key for key in 'ctzxy' if key not in requested_keys]
                out_axes = ""
                for k, v in tagged_shape.items():
                    if v > 1:
                        out_axes += requested_keys.pop(0)
                    else:
                        out_axes += dummy_axes.pop()
                self.axistags = vigra.defaultAxistags(out_axes)
            else:
                raise Exception(f"Cannot reinterpret input with shape {self.laneShape} using aksiskeys {requested_keys}")

        if self.location is None:
            if self.relative_paths:
                self.location = self.Location.FileSystemRelativePath
            else:
                self.location = self.Location.FileSystemAbsolutePath

        if self.location == self.Location.FileSystemRelativePath and not self.relative_paths:
            raise Exception(f"\"{self.original_paths}\" can't be expressed relative to {self.base_dir}")

    def is_in_filesystem(self) -> bool:
        return self.location in (self.Location.FileSystemRelativePath, self.Location.FileSystemAbsolutePath)

    @classmethod
    def create_nickname(cls, expanded_paths:List[str]):
        components = [PathComponents(ep) for ep in expanded_paths]
        external_nickname = os.path.commonprefix([re.sub(comp.extension + '$', '', comp.externalPath) for comp in components])
        if external_nickname:
            external_nickname = external_nickname.split(os.path.sep)[-1]
        else:
            external_nickname = "stack_at-" + components[0].filenameBase
        internal_nickname = os.path.commonprefix([comp.internalPath or "" for comp in components]).lstrip('/')
        nickname = external_nickname + ('-' + internal_nickname.replace('/', '-') if internal_nickname else '')
        return nickname

    @property
    def effective_uris(self):
        if self.location == self.Location.PreloadedArray:
            return []
        elif self.location == self.Location.ProjectInternal:
            return [self.filePath]
        elif self.location == self.Location.FileSystemRelativePath:
            return self.relative_paths
        elif self.location == self.Location.FileSystemAbsolutePath:
            return self.expanded_paths[:]
        else:
            raise Exception(f"Bad location: {self.location}")

    @property
    def persistent_path(self) -> str:
        return os.path.pathsep.join(self.effective_uris)

    @property
    def relative_paths(self) -> List[str]:
        if self.location in (self.Location.ProjectInternal, self.Location.PreloadedArray):
            return []
        external_paths = [Path(PathComponents(path).externalPath) for path in self.expanded_paths]
        try:
            return sorted([str(ext_path.absolute().relative_to(self.base_dir)) for ext_path in external_paths])
        except ValueError:
            return []

    @classmethod
    def generate_id(cls) -> str:
        return str(uuid.uuid1())

    @property
    def external_paths(self) -> List[str]:
        return [PathComponents(ep).externalPath for ep in self.expanded_paths]

    @property
    def internal_paths(self) -> List[str]:
        return [PathComponents(ep).internalPath for ep in self.expanded_paths]

    @property
    def file_extensions(self) -> str:
        return [PathComponents(ep).extension for ep in self.expanded_paths]

    @classmethod
    def expand_path(cls, file_path:str, cwd:str=None) -> List[str]:
        """Expands path with globs and colons into a list of absolute paths"""
        cwd = cwd or os.getcwd()
        pathComponents = [PathComponents(path) for path in splitPath(file_path)]
        expanded_paths = []
        for components in pathComponents:
            if os.path.isabs(components.externalPath):
                externalPath = components.externalPath
            else:
                externalPath = os.path.join(cwd, components.externalPath)
            unglobbed_paths = glob.glob(os.path.expanduser(externalPath))
            if not unglobbed_paths:
                raise FileNotFoundError(externalPath)
            for ext_path in unglobbed_paths:
                if not cls.fileHasInternalPaths(ext_path) or not components.internalPath:
                    expanded_paths.append(ext_path)
                    continue
                internal_paths = cls.globInternalPaths(ext_path, components.internalPath)
                expanded_paths.extend([os.path.join(ext_path, int_path) for int_path in internal_paths])
        return sorted(expanded_paths)

    @classmethod
    def globInternalPaths(cls, file_path:str, glob_str:str, cwd:str=None) -> List[str]:
        glob_str = glob_str.lstrip('/')
        internal_paths = set()
        for path in cls.expand_path(file_path, cwd=cwd):
            f = None
            try:
                if cls.pathIsNpz(path):
                    internal_paths |= set(globNpz(path, glob_str))
                    continue
                elif cls.pathIsHdf5(path):
                    f = h5py.File(path, 'r')
                elif cls.pathIsN5(path):
                    f = z5py.N5File(path) #FIXME
                else:
                    raise Exception(f"{path} is not an 'n5' or 'h5' file")
                internal_paths |= set(globH5N5(f, glob_str))
            finally:
                if f is not None:
                    f.close()
        return sorted(internal_paths)

    @classmethod
    def pathIsHdf5(cls, path:str) -> bool:
        return PathComponents(path).extension in ['.ilp', '.h5', '.hdf5']

    def isHdf5(self) -> bool:
        return any(self.pathIsHdf5(ep) for ep in self.external_paths)

    @classmethod
    def pathIsNpz(cls, path:str) -> bool:
        return PathComponents(path).extension in ['.npz']

    def isNpz(self) -> bool:
        return any(self.pathIsNpz(ep) for ep in self.external_paths)

    @classmethod
    def pathIsN5(cls, path:str) -> bool:
        return PathComponents(path).extension in ['.n5']

    def isN5(self) -> bool:
        return any(self.pathIsN5(ep) for ep in self.external_paths)

    @classmethod
    def fileHasInternalPaths(cls, path:str) -> bool:
        return cls.pathIsHdf5(path) or cls.pathIsN5(path) or cls.pathIsNpz(path)

    @classmethod
    def getPossibleInternalPathsFor(cls, file_path:str, min_ndim=2, max_ndim=5):
        datasetNames = []

        if cls.pathIsHdf5(file_path):
            def accumulateDatasetPaths(name, val):
                if type(val) == h5py._hl.dataset.Dataset and min_ndim <= len(val.shape) <= max_ndim:
                    datasetNames.append(name)
            with h5py.File(file_path, 'r') as f:
                f.visititems(accumulateDatasetPaths)
        elif cls.pathIsN5(file_path):
            def accumulate_names(path, val):
                if isinstance(val, z5py.dataset.Dataset) and min_ndim <= len(val.shape) <= max_ndim:
                    name = path.replace(file_path, '')  #FIXME: re.sub(r'^' + file_path, ...) ?
                    datasetNames.append(name)
            with z5py.N5File(file_path, mode='r+') as f:
                f.visititems(accumulate_names)

        return datasetNames

    def getPossibleInternalPaths(self):
        possible_internal_paths = set()
        for expanded_path in self.expanded_paths:
            external_path = PathComponents(expanded_path).externalPath
            possible_internal_paths |= set(self.getPossibleInternalPathsFor(external_path))
        return possible_internal_paths

    @property
    def datasetId(self):
        #FIXME: this prop should not be necessary, we should just trust
        #the filePath to retrieve the data out of the .ilp file
        assert self.location == self.Location.ProjectInternal
        return self.filePath.split(os.path.sep)[-1] #is this a problem in windows?

    @property
    def axiskeys(self):
        return "".join(tag.key for tag in self.axistags)

    def __str__(self):
        s = "{ "
        s += "filepath: {},\n".format(self.filePath)
        s += "location: {}\n".format({DatasetInfo.Location.FileSystem: "FileSystem",
                                      DatasetInfo.Location.ProjectInternal: "ProjectInternal",
                                      DatasetInfo.Location.PreloadedArray: "PreloadedArray"
                                      }[self.location])
        s += "nickname: {},\n".format(self.nickname)
        if self.axistags:
            s += "axistags: {},\n".format(self.axistags)
        if self.drange:
            s += "drange: {},\n".format(self.drange)
        s += "normalizeDisplay: {}\n".format(self.normalizeDisplay)
        if self.subvolume_roi:
            s += "subvolume_roi: {},\n".format(self.subvolume_roi)
        s += " }\n"
        return s

    def updateFromJson(self, namespace):
        """
        Given a namespace object returned by a JsonConfigParser,
        update the corresponding non-None fields of this DatasetInfo.
        """
        self.filePath = namespace.filepath or self.filePath
        self.drange = namespace.drange or self.drange
        self.nickname = namespace.nickname or self.nickname
        if namespace.axistags is not None:
            self.axistags = vigra.defaultAxistags(namespace.axistags)
        self.subvolume_roi = namespace.subvolume_roi or self.subvolume_roi

    @classmethod
    def from_file_path(cls, instance, file_path):
        """
        Creates a shallow copy of a given DatasetInfo instance
        with filePath and related attributes overridden
        """
        default_info = cls(file_path)
        result = copy.copy(instance)
        result.filePath = default_info.filePath
        result.location = default_info.location
        result.nickname = default_info.nickname
        return result

class OpDataSelection(Operator):
    """
    The top-level operator for the data selection applet, implemented as a single-image operator.
    The applet uses an OperatorWrapper to make it suitable for use in a workflow.
    """
    name = "OpDataSelection"
    category = "Top-level"

    SupportedExtensions = OpInputDataReader.SupportedExtensions

    # Inputs
    RoleName = InputSlot(stype='string', value='')
    ProjectFile = InputSlot(stype='object', optional=True)  # : The project hdf5 File object (already opened)
    # : The internal path to the hdf5 group where project-local datasets are stored within the project file
    ProjectDataGroup = InputSlot(stype='string', optional=True)
    WorkingDirectory = InputSlot(stype='filestring')  # : The filesystem directory where the project file is located
    Dataset = InputSlot(stype='object')  # : A DatasetInfo object

    # Outputs
    Image = OutputSlot()  # : The output image
    AllowLabels = OutputSlot(stype='bool')  # : A bool indicating whether or not this image can be used for training

    # : The output slot, in the data's original axis ordering (regardless of forceAxisOrder)
    _NonTransposedImage = OutputSlot()

    ImageName = OutputSlot(stype='string')  # : The name of the output image

    class InvalidDimensionalityError(Exception):
        """Raised if the user tries to replace the dataset with a new one of differing dimensionality."""

        def __init__(self, message):
            super(OpDataSelection.InvalidDimensionalityError, self).__init__()
            self.message = message

        def __str__(self):
            return self.message

    def __init__(self, forceAxisOrder:List[str]=['tczyx'], ProjectFile:h5py.File=None, ProjectDataGroup=None,
                 WorkingDirectory=None, Dataset:DatasetInfo=None, *args, **kwargs):
        """
        forceAxisOrder: How to auto-reorder the input data before connecting it to the rest of the workflow.
                        Should be a list of input orders that are allowed by the workflow
                        For example, if the workflow can handle 2D and 3D, you might pass ['yxc', 'zyxc'].
                        If it only handles exactly 5D, you might pass 'tzyxc', assuming that's how you wrote the
                        workflow.
                        todo: move toward 'tczyx' standard.
        """
        super(OpDataSelection, self).__init__(*args, **kwargs)
        self.forceAxisOrder = forceAxisOrder
        self._opReaders = []

        # If the gui calls disconnect() on an input slot without replacing it with something else,
        #  we still need to clean up the internal operator that was providing our data.
        self.ProjectFile.notifyUnready(self.internalCleanup)
        self.ProjectFile.setOrConnectIfAvailable(ProjectFile)

        self.ProjectDataGroup.notifyUnready(self.internalCleanup)
        self.ProjectDataGroup.setOrConnectIfAvailable(ProjectDataGroup)

        self.WorkingDirectory.notifyUnready(self.internalCleanup)
        self.WorkingDirectory.setOrConnectIfAvailable(WorkingDirectory)

        self.Dataset.notifyUnready(self.internalCleanup)
        self.Dataset.setOrConnectIfAvailable(Dataset)

    def internalCleanup(self, *args):
        if len(self._opReaders) > 0:
            self.Image.disconnect()
            self._NonTransposedImage.disconnect()
            for reader in reversed(self._opReaders):
                reader.cleanUp()
            self._opReaders = []

    def setupOutputs(self):
        self.internalCleanup()
        datasetInfo = self.Dataset.value

        try:
            # If we should find the data in the project file, use a dataset reader
            if datasetInfo.location == DatasetInfo.Location.ProjectInternal:
                opReader = OpStreamingH5N5Reader(parent=self)
                opReader.H5N5File.setValue(self.ProjectFile.value)
                opReader.InternalPath.setValue(datasetInfo.filePath)
                providerSlot = opReader.OutputImage
            elif datasetInfo.location == DatasetInfo.Location.PreloadedArray:
                opReader = OpArrayPiper(parent=self)
                opReader.Input.setValue(datasetInfo.preloaded_array)
                providerSlot = opReader.Output
            else:
                opReader = OpInputDataReader(parent=self)
                if datasetInfo.subvolume_roi is not None:
                    opReader.SubVolumeRoi.setValue(datasetInfo.subvolume_roi)
                opReader.WorkingDirectory.setValue(self.WorkingDirectory.value)
                opReader.SequenceAxis.setValue(datasetInfo.sequenceAxis)
                opReader.FilePath.setValue(datasetInfo.filePath)
                providerSlot = opReader.Output
            self._opReaders.append(opReader)

            # Inject metadata if the dataset info specified any.
            # Also, inject if if dtype is uint8, which we can reasonably assume has drange (0,255)
            metadata = {}
            metadata['display_mode'] = datasetInfo.display_mode

            role_name = self.RoleName.value
            if 'c' not in providerSlot.meta.getTaggedShape():
                num_channels = 0
            else:
                num_channels = providerSlot.meta.getTaggedShape()['c']
            if num_channels > 1:
                metadata['channel_names'] = [f"{role_name}-{i}" for i in range(num_channels)]
            else:
                metadata['channel_names'] = [role_name]

            if datasetInfo.drange is not None:
                metadata['drange'] = datasetInfo.drange
            elif providerSlot.meta.dtype == numpy.uint8:
                metadata['drange'] = (0, 255)
            if datasetInfo.normalizeDisplay is not None:
                metadata['normalizeDisplay'] = datasetInfo.normalizeDisplay
            if datasetInfo.axistags is not None:
                metadata['axistags'] = datasetInfo.axistags
            if datasetInfo.original_axistags is not None:
                metadata['original_axistags'] = datasetInfo.original_axistags

            if datasetInfo.subvolume_roi is not None:
                metadata['subvolume_roi'] = datasetInfo.subvolume_roi

                # FIXME: We are overwriting the axistags metadata to intentionally allow
                #        the user to change our interpretation of which axis is which.
                #        That's okay, but technically there's a special corner case if
                #        the user redefines the channel axis index.
                #        Technically, it invalidates the meaning of meta.ram_usage_per_requested_pixel.
                #        For most use-cases, that won't really matter, which is why I'm not worrying about it right now.

            opMetadataInjector = OpMetadataInjector(parent=self)
            opMetadataInjector.Input.connect(providerSlot)
            opMetadataInjector.Metadata.setValue(metadata)
            providerSlot = opMetadataInjector.Output
            self._opReaders.append(opMetadataInjector)

            self._NonTransposedImage.connect(providerSlot)

            # make sure that x and y axes are present in the selected axis order
            if 'x' not in providerSlot.meta.axistags or 'y' not in providerSlot.meta.axistags:
                raise DatasetConstraintError("DataSelection",
                                             "Data must always have at leaset the axes x and y for ilastik to work.")

            if self.forceAxisOrder:
                assert isinstance(self.forceAxisOrder, list), \
                    "forceAxisOrder should be a *list* of preferred axis orders"

                # Before we re-order, make sure no non-singleton
                #  axes would be dropped by the forced order.
                tagged_provider_shape = providerSlot.meta.getTaggedShape()
                minimal_axes = {k for k, v in tagged_provider_shape.items() if v > 1}

                # Pick the shortest of the possible 'forced' orders that
                # still contains all the axes of the original dataset.
                candidate_orders = list(self.forceAxisOrder)
                candidate_orders = [order for order in candidate_orders if minimal_axes.issubset(set(order))]

                if len(candidate_orders) == 0:
                    msg = (f"The axes of your dataset ({providerSlot.meta.getAxisKeys()}) are not compatible with "
                           f"any of the allowed axis configurations used by this workflow ({self.forceAxisOrder}).")
                    raise DatasetConstraintError("DataSelection", msg)

                output_order = sorted(candidate_orders, key=len)[0]  # the shortest one
                output_order = "".join(output_order)
            else:
                # No forced axisorder is supplied. Use original axisorder as
                # output order: it is assumed by the export-applet, that the
                # an OpReorderAxes operator is added in the beginning
                output_order = providerSlot.meta.getAxisKeys()
            if 'c' not in output_order:
                output_order += 'c'

            op5 = OpReorderAxes(parent=self, AxisOrder=output_order, Input=providerSlot)
            self._opReaders.append(op5)

            self.Image.connect(op5.Output)

            self.AllowLabels.setValue(datasetInfo.allowLabels)

            if self.Image.meta.nickname is not None:
                datasetInfo.nickname = self.Image.meta.nickname

            imageName = datasetInfo.nickname
            if imageName == "":
                imageName = datasetInfo.filePath
            self.ImageName.setValue(imageName)

        except:
            self.internalCleanup()
            raise

    def propagateDirty(self, slot, subindex, roi):
        # Output slots are directly connected to internal operators
        pass

    @classmethod
    def getInternalDatasets(cls, filePath):
        return OpInputDataReader.getInternalDatasets(filePath)


class OpDataSelectionGroup(Operator):
    # Inputs
    ProjectFile = InputSlot(stype='object', optional=True)
    ProjectDataGroup = InputSlot(stype='string', optional=True)
    WorkingDirectory = InputSlot(stype='filestring')
    DatasetRoles = InputSlot(stype='object')

    # Must mark as optional because not all subslots are required.
    DatasetGroup = InputSlot(stype='object', level=1, optional=True)

    # Outputs
    ImageGroup = OutputSlot(level=1)

    # These output slots are provided as a convenience, since otherwise it is tricky to create a lane-wise multislot of
    # level-1 for only a single role.
    # (It can be done, but requires OpTransposeSlots to invert the level-2 multislot indexes...)
    Image = OutputSlot()  # The first dataset. Equivalent to ImageGroup[0]
    Image1 = OutputSlot()  # The second dataset. Equivalent to ImageGroup[1]
    Image2 = OutputSlot()  # The third dataset. Equivalent to ImageGroup[2]
    AllowLabels = OutputSlot(stype='bool')  # Pulled from the first dataset only.

    _NonTransposedImageGroup = OutputSlot(level=1)

    # Must be the LAST slot declared in this class.
    # When the shell detects that this slot has been resized,
    #  it assumes all the others have already been resized.
    ImageName = OutputSlot()  # Name of the first dataset is used.  Other names are ignored.

    def __init__(self, forceAxisOrder=None, *args, **kwargs):
        super(OpDataSelectionGroup, self).__init__(*args, **kwargs)
        self._opDatasets = None
        self._roles = []
        self._forceAxisOrder = forceAxisOrder

        def handleNewRoles(*args):
            self.DatasetGroup.resize(len(self.DatasetRoles.value))
        self.DatasetRoles.notifyReady(handleNewRoles)

    def setupOutputs(self):
        # Create internal operators
        if self.DatasetRoles.value != self._roles:
            self._roles = self.DatasetRoles.value
            # Clean up the old operators
            self.ImageGroup.disconnect()
            self.Image.disconnect()
            self.Image1.disconnect()
            self.Image2.disconnect()
            self._NonTransposedImageGroup.disconnect()
            if self._opDatasets is not None:
                self._opDatasets.cleanUp()

            self._opDatasets = OperatorWrapper(OpDataSelection, parent=self,
                                               operator_kwargs={'forceAxisOrder': self._forceAxisOrder},
                                               broadcastingSlotNames=['ProjectFile', 'ProjectDataGroup',
                                                                      'WorkingDirectory'])
            self.ImageGroup.connect(self._opDatasets.Image)
            self._NonTransposedImageGroup.connect(self._opDatasets._NonTransposedImage)
            self._opDatasets.Dataset.connect(self.DatasetGroup)
            self._opDatasets.ProjectFile.connect(self.ProjectFile)
            self._opDatasets.ProjectDataGroup.connect(self.ProjectDataGroup)
            self._opDatasets.WorkingDirectory.connect(self.WorkingDirectory)

        for role_index, opDataSelection in enumerate(self._opDatasets):
            opDataSelection.RoleName.setValue(self._roles[role_index])

        if len(self._opDatasets.Image) > 0:
            self.Image.connect(self._opDatasets.Image[0])

            if len(self._opDatasets.Image) >= 2:
                self.Image1.connect(self._opDatasets.Image[1])
            else:
                self.Image1.disconnect()
                self.Image1.meta.NOTREADY = True

            if len(self._opDatasets.Image) >= 3:
                self.Image2.connect(self._opDatasets.Image[2])
            else:
                self.Image2.disconnect()
                self.Image2.meta.NOTREADY = True

            self.ImageName.connect(self._opDatasets.ImageName[0])
            self.AllowLabels.connect(self._opDatasets.AllowLabels[0])
        else:
            self.Image.disconnect()
            self.Image1.disconnect()
            self.Image2.disconnect()
            self.ImageName.disconnect()
            self.AllowLabels.disconnect()
            self.Image.meta.NOTREADY = True
            self.Image1.meta.NOTREADY = True
            self.Image2.meta.NOTREADY = True
            self.ImageName.meta.NOTREADY = True
            self.AllowLabels.meta.NOTREADY = True

    def execute(self, slot, subindex, rroi, result):
        assert False, "Unknown or unconnected output slot: {}".format(slot.name)

    def propagateDirty(self, slot, subindex, roi):
        # Output slots are directly connected to internal operators
        pass


class OpMultiLaneDataSelectionGroup(OpMultiLaneWrapper):
    # TODO: Provide output slots DatasetsByRole and ImagesByRole as a convenience
    #       to save clients the trouble of instantiating/using OpTransposeSlots.
    def __init__(self, forceAxisOrder=False, *args, **kwargs):
        kwargs.update({'operator_kwargs': {'forceAxisOrder': forceAxisOrder},
                       'broadcastingSlotNames': ['ProjectFile', 'ProjectDataGroup', 'WorkingDirectory',
                                                 'DatasetRoles']})
        super(OpMultiLaneDataSelectionGroup, self).__init__(OpDataSelectionGroup, *args, **kwargs)

        # 'value' slots
        assert self.ProjectFile.level == 0
        assert self.ProjectDataGroup.level == 0
        assert self.WorkingDirectory.level == 0
        assert self.DatasetRoles.level == 0

        # Indexed by [lane][role]
        assert self.DatasetGroup.level == 2, "DatasetGroup is supposed to be a level-2 slot, indexed by [lane][role]"

    def addLane(self, laneIndex):
        """Reimplemented from base class."""
        numLanes = len(self.innerOperators)

        # Only add this lane if we don't already have it
        # We might be called from within the context of our own insertSlot signal.
        if numLanes == laneIndex:
            super(OpMultiLaneDataSelectionGroup, self).addLane(laneIndex)

    def removeLane(self, laneIndex, finalLength):
        """Reimplemented from base class."""
        numLanes = len(self.innerOperators)
        if numLanes > finalLength:
            super(OpMultiLaneDataSelectionGroup, self).removeLane(laneIndex, finalLength)
