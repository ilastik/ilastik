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
import numpy
import os
import uuid
import vigra
import copy
import h5py
from enum import Enum, unique

from lazyflow.graph import Operator, InputSlot, OutputSlot, OperatorWrapper
from lazyflow.metaDict import MetaDict
from lazyflow.operators.ioOperators import (
    OpStreamingH5N5Reader, OpStreamingH5N5SequenceReaderS, OpInputDataReader
)
from lazyflow.operators.valueProviders import OpMetadataInjector, OpZeroDefault
from lazyflow.operators.opArrayPiper import OpArrayPiper
from ilastik.applets.base.applet import DatasetConstraintError

from ilastik.utility import OpMultiLaneWrapper
from lazyflow.array5d import Point5D, Shape5D
from lazyflow.graph import Graph
from lazyflow.utility import PathComponents, isUrl, make_absolute
from lazyflow.utility.helpers import get_default_axisordering
from lazyflow.operators.opReorderAxes import OpReorderAxes


class DatasetInfo(object):
    """
    Struct-like class for describing dataset info.
    """
    @unique
    class Location(Enum):
        FileSystem = 0
        ProjectInternal = 1
        PreloadedArray = 2

    def __init__(self, filepath=None, jsonNamespace=None, cwd=None,
                 preloaded_array=None, sequence_axis=None, allowLabels=True,
                 subvolume_roi=None, location=Location.FileSystem,
                 fromstack=False, axistags=None, drange=None, display_mode='default',
                 nickname='', original_axistags=None, shape=None, normalizeDisplay:bool=None,
                 sequenceAxis:str=None, dtype=None, datasetId:str=""):
        """
        filepath: may be a globstring or a full hdf5 path+dataset

        jsonNamespace: If provided, overrides default settings after filepath is applied

        cwd: The working directory for interpeting relative paths.  If not provided, os.getcwd() is used.

        preloaded_array: Instead of providing a filePath to read from, a pre-loaded array can be directly provided.
                         In that case, you'll probably want to configure the axistags member, or provide a tagged
                         vigra.VigraArray.

        sequence_axis: Axis along which to stack (only applicable for stacks).
        """
        assert preloaded_array is None or not filepath, "You can't provide filepath and a preloaded_array"
        cwd = cwd or os.getcwd()
        self.preloaded_array = preloaded_array  # See description above.
        Location = DatasetInfo.Location
        # The original path to the data (also used as a fallback if the data isn't in the project yet)
        self._filePath = ""
        self._datasetId = datasetId # The name of the data within the project file (if it is stored locally)
        # OBSOLETE: Whether or not this dataset should be used for training a classifier.
        self.allowLabels = allowLabels
        self.drange = drange
        self.normalizeDisplay = (drange is not None) if normalizeDisplay is None else normalizeDisplay
        self.sequenceAxis = sequenceAxis
        self.fromstack = fromstack
        self.nickname = nickname
        self.axistags = axistags
        self.original_axistags = original_axistags
        self.shape = shape
        self.dtype = dtype
        # Necessary in headless mode in order to recover the shape of the raw data
        self.laneShape = None
        self.laneDtype = None
        # A flag indicating whether the dataset is backed by a real source (e.g. file)
        # or by the fake provided (e.g. in headless mode when raw data are not necessary)
        self.realDataSource = True
        self.subvolume_roi = subvolume_roi
        self.location = location
        self.display_mode = display_mode  # choices: default, grayscale, rgba, random-colortable, binary-mask.

        if self.preloaded_array is not None:
            self.filePath = ""  # set property to ensure unique _datasetId
            self.location = Location.PreloadedArray
            self.nickname = "preloaded-{}-array".format(self.preloaded_array.dtype.name)
            if hasattr(self.preloaded_array, 'axistags'):
                self.axistags = self.preloaded_array.axistags

        # Set defaults for location, nickname, filepath, and fromstack
        if filepath:
            # Check for sequences (either globstring or separated paths),
            file_list = None

            # To support h5 sequences, filepath may contain external and
            # internal path components
            if not isUrl(filepath):
                file_list = filepath.split(os.path.pathsep)

                pathComponents = [PathComponents(x) for x in file_list]
                externalPaths = [pc.externalPath for pc in pathComponents]
                internalPaths = [pc.internalPath for pc in pathComponents]

                if len(file_list) > 0:
                    if len(externalPaths) == 1:
                        if '*' in externalPaths[0]:
                            if internalPaths[0] is not None:
                                assert ('*' not in internalPaths[0]), (
                                    "Only internal OR external glob placeholder supported"
                                )
                            file_list = sorted(glob.glob(filepath))
                        else:
                            file_list = [externalPaths[0]]
                            if internalPaths[0] is not None:
                                if '*' in internalPaths[0]:
                                    # overwrite internalPaths, will be assembled further down
                                    glob_string = "{}{}".format(externalPaths[0], internalPaths[0])
                                    internalPaths = \
                                        OpStreamingH5N5SequenceReaderS.expandGlobStrings(
                                            externalPaths[0], glob_string)
                                    if internalPaths:
                                        file_list = [externalPaths[0]] * len(internalPaths)
                                    else:
                                        file_list = None

                    else:
                        assert (not any('*' in ep for ep in externalPaths)), (
                            "Multiple glob paths shouldn't be happening"
                        )
                        file_list = [ex for ex in externalPaths]

                    assert all(pc.extension == pathComponents[0].extension
                               for pc in pathComponents[1::]), (
                        "Supplied multiple files with multiple extensions"
                    )
                    # The following is necessary for h5 as well as npz-files
                    internalPathExts = (
                        OpInputDataReader.h5_n5_Exts +
                        OpInputDataReader.npzExts
                    )
                    internalPathExts = [".{}".format(ipx) for ipx in internalPathExts]

                    if pathComponents[0].extension in internalPathExts and internalPaths:
                        if len(file_list) == len(internalPaths):
                            # assuming a matching internal paths to external paths
                            file_list_with_internal = []
                            for external, internal in zip(file_list, internalPaths):
                                if internal:
                                    file_list_with_internal.append('{}/{}'.format(external, internal))
                                else:
                                    file_list_with_internal.append(external)
                            file_list = file_list_with_internal
                        else:
                            # sort of fallback, in case of a mismatch in lengths
                            for i in range(len(file_list)):
                                file_list[i] += '/' + internalPaths[0]

            # For stacks, choose nickname based on a common prefix
            if len(file_list) > 1:
                fromstack = True
                # Convert all paths to absolute
                file_list = [make_absolute(f, cwd) for f in file_list]
                if '*' in filepath:
                    filepath = make_absolute(filepath, cwd)
                else:
                    filepath = os.path.pathsep.join(file_list)

                # Add an underscore for each wildcard digit
                prefix = os.path.commonprefix(file_list)
                num_wildcards = len(file_list[-1]) - len(prefix) - len(os.path.splitext(file_list[-1])[1])
                nickname = PathComponents(prefix).filenameBase + ("_" * num_wildcards)
            else:
                fromstack = False
                if not isUrl(filepath):
                    # Convert all (non-url) paths to absolute
                    filepath = make_absolute(filepath, cwd)
                nickname = PathComponents(filepath).filenameBase

            self.location = DatasetInfo.Location.FileSystem
            self.nickname = nickname
            self.filePath = filepath #FIXME: stop clobbering user-provided id
            if datasetId:
                self._datasetId = datasetId #FIXME: stop clobbering user-provided id
            self.fromstack = fromstack
            self.sequenceAxis = sequence_axis

        if jsonNamespace is not None:
            self.updateFromJson(jsonNamespace)

    def modified_with(self, **kwargs):
        #FIXME: call the constructor again
        info = copy.copy(self)
        for k, v in kwargs.items():
            setattr(info, k, v)
        return info

    @classmethod
    def default(cls, filepath:str, sequence_axis=None, **kwargs) -> 'DatasetInfo':
        op_reader = OpInputDataReader(graph=Graph())
        if 'cwd' in kwargs:
            op_reader.WorkingDirectory.setValue(kwargs['cwd'])
        if sequence_axis is not None:
            op_reader.SequenceAxis.setValue(sequence_axis)
        op_reader.FilePath.setValue(filepath)
        return cls.from_slot(op_reader.Output, filepath, **kwargs)

    @classmethod
    def from_slot(cls, slot, filepath:str, **kwargs):
        meta = slot.meta
        info_params = {
            'filepath': filepath,
            'axistags': meta.axistags,
            'shape': meta.shape,
        }
        for key in ('drange', 'display_mode', 'normalizeDisplay', 'dtype'):
            if key in meta:
                info_params[key] = meta[key]
        info_params.update(kwargs)
        return cls(**info_params)

    @classmethod
    def generate_id(cls) -> str:
        return str(uuid.uuid1())

    @property
    def filePath(self):
        return self._filePath

    @filePath.setter
    def filePath(self, newPath):
        self._filePath = newPath
        # Reset our id any time the filepath changes
        self._datasetId = self.generate_id()

    @property
    def externalPath(self) -> str:
        return PathComponents(self.filePath).externalPath

    @property
    def internalPath(self) -> str:
        return PathComponents(self.filePath).internalPath

    @property
    def fileExtension(self) -> str:
        return os.path.splitext(self.externalPath)[1]

    @classmethod
    def pathIsHdf5(cls, path:str) -> bool:
        return os.path.splitext(path)[1].lower() in ('.ilp', '.h5', '.hdf5')

    def isHdf5(self) -> bool:
        return self.pathIsHdf5(self.externalPath)

    @classmethod
    def pathIsN5(cls, path:str) -> bool:
        return os.path.splitext(path)[1].lower() in ('.n5')

    def isN5(self) -> bool:
        return self.pathIsN5(self.externalPath)

    @classmethod
    def fileHasInternalPaths(cls, path:str) -> bool:
        return cls.pathIsHdf5(path) or cls.pathIsN5(path)

    @classmethod
    def getPossibleInternalPathsFor(cls, file_path:str, min_ndim=2, max_ndim=5):
        datasetNames = []

        if cls.pathIsHdf5(file_path):
            with h5py.File(file_path, 'r') as f:
                def accumulateDatasetPaths(name, val):
                    if type(val) == h5py._hl.dataset.Dataset and min_ndim <= len(val.shape) <= max_ndim:
                        datasetNames.append( '/' + name )
                f.visititems(accumulateDatasetPaths)
        elif cls.pathIsN5(file_path):
            with z5py.N5File(file_path, mode='r+') as f:
                def accumulate_names(path, val):
                    if isinstance(val, z5py.dataset.Dataset) and min_ndim <= len(val.shape) <= max_ndim:
                        name = path.replace(file_path, '')  #FIXME: re.sub(r'^' + file_path, ...) ?
                        datasetNames.append(name)
                f.visititems(accumulate_names)

        return datasetNames

    def getPossibleInternalPaths(self):
        assert self.fileHasInternalPaths(self.externalPath)
        return self.getPossibleInternalPathsFor(self.externalPath)

    @property
    def datasetId(self):
        return self._datasetId

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
        if self.fromstack:
            s += "fromstack: {}\n".format(self.fromstack)
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

    def __init__(self, forceAxisOrder=['tczyx'], *args, **kwargs):
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
        self.ProjectDataGroup.notifyUnready(self.internalCleanup)
        self.WorkingDirectory.notifyUnready(self.internalCleanup)
        self.Dataset.notifyUnready(self.internalCleanup)

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
            # Data only comes from the project file if the user said so AND it exists in the project
            datasetInProject = (datasetInfo.location == DatasetInfo.Location.ProjectInternal)
            datasetInProject &= self.ProjectFile.ready()
            if datasetInProject:
                internalPath = self.ProjectDataGroup.value + '/' + datasetInfo.datasetId
                datasetInProject &= internalPath in self.ProjectFile.value

            # If we should find the data in the project file, use a dataset reader
            if datasetInProject:
                opReader = OpStreamingH5N5Reader(parent=self)
                opReader.H5N5File.setValue(self.ProjectFile.value)
                opReader.InternalPath.setValue(internalPath)
                providerSlot = opReader.OutputImage
            elif datasetInfo.location == DatasetInfo.Location.PreloadedArray:
                preloaded_array = datasetInfo.preloaded_array
                assert preloaded_array is not None
                if not hasattr(preloaded_array, 'axistags'):
                    axisorder = get_default_axisordering(preloaded_array.shape)
                    preloaded_array = vigra.taggedView(preloaded_array, axisorder)

                opReader = OpArrayPiper(parent=self)
                opReader.Input.setValue(preloaded_array)
                providerSlot = opReader.Output
            else:
                if datasetInfo.realDataSource:
                    # Use a normal (filesystem) reader
                    opReader = OpInputDataReader(parent=self)
                    if datasetInfo.subvolume_roi is not None:
                        opReader.SubVolumeRoi.setValue(datasetInfo.subvolume_roi)
                    opReader.WorkingDirectory.setValue(self.WorkingDirectory.value)
                    opReader.SequenceAxis.setValue(datasetInfo.sequenceAxis)
                    opReader.FilePath.setValue(datasetInfo.filePath)
                else:
                    # Use fake reader: allows to run the project in a headless
                    # mode without the raw data
                    opReader = OpZeroDefault(parent=self)
                    opReader.MetaInput.meta = MetaDict(
                        shape=datasetInfo.laneShape,
                        dtype=datasetInfo.laneDtype,
                        drange=datasetInfo.drange,
                        axistags=datasetInfo.axistags)
                    opReader.MetaInput.setValue(numpy.zeros(datasetInfo.laneShape, dtype=datasetInfo.laneDtype))
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
                metadata['channel_names'] = ["{}-{}".format(role_name, i) for i in range(num_channels)]
            else:
                metadata['channel_names'] = [role_name]

            if datasetInfo.drange is not None:
                metadata['drange'] = datasetInfo.drange
            elif providerSlot.meta.dtype == numpy.uint8:
                metadata['drange'] = (0, 255)
            if datasetInfo.normalizeDisplay is not None:
                metadata['normalizeDisplay'] = datasetInfo.normalizeDisplay
            if datasetInfo.axistags is not None:
                info_keys = [tag.key for tag in datasetInfo.axistags]
                provider_shape = providerSlot.meta.shape
                provider_keys = providerSlot.meta.getAxisKeys()
                provider_squeezed_shape = providerSlot.meta.getShape5D().to_squeezed_dict()
                print(f"info_keys: {info_keys}   provider_shape: {providerSlot.meta.getTaggedShape()}")
                if len(info_keys) == len(provider_shape):
                    metadata['axistags'] = datasetInfo.axistags
                elif len(info_keys) == len(provider_shape) - 1 and set(provider_keys) - set(info_keys) == set('c'):
                    metadata['axistags'] = vigra.defaultAxistags(''.join(info_keys) + 'c')
                elif len(info_keys) == len(provider_squeezed_shape.keys()):
                    dummy_axes = set(Point5D.LABELS) - set(info_keys)
                    out_axes = ""
                    for k, v in providerSlot.meta.getTaggedShape().items():
                        if k in provider_squeezed_shape:
                            out_axes += info_keys.pop(0)
                        else:
                            out_axes += dummy_axes.pop()
                    metadata['axistags'] = vigra.defaultAxistags(out_axes)
                else:
                    raise Exception(f"Cannot reinterpret input with shape {providerSlot.meta.getTaggedShape()} using "
                                    f"given axis order of {info_keys}")
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
