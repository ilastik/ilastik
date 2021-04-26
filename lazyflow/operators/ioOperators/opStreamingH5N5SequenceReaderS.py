###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2017, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the Lesser GNU General Public License
# as published by the Free Software Foundation; either version 2.1
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# See the files LICENSE.lgpl2 and LICENSE.lgpl3 for full text of the
# GNU Lesser General Public License version 2.1 and 3 respectively.
# This information is also available on the ilastik web site at:
#          http://ilastik.org/license/
###############################################################################
from ilastik.utility.data_url import ArchiveDataPath
import os
from typing import List

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.operators.generic import OpMultiArrayStacker
from lazyflow.operators.ioOperators.opStreamingH5N5Reader import OpStreamingH5N5Reader
from lazyflow.utility.pathHelpers import PathComponents, globH5N5

import h5py
import z5py
import logging

logger = logging.getLogger(__name__)


class OpStreamingH5N5SequenceReaderS(Operator):
    """
    Imports a sequence of (ND) volumes inside one hdf5/N5 file into a single volume (ND+1)

    The 'S' at the end of the file name implies that this class handles multiple
    volumes in a single file.
    """

    ArchiveDataPaths = InputSlot()  # Union[List[H5DataPath], List[N5DataPath]]
    # The project hdf5 File object (already opened)
    SequenceAxis = InputSlot(optional=True)  # The axis to stack across.
    OutputImage = OutputSlot()

    class WrongFileTypeError(Exception):
        def __init__(self, globString):
            self.filename = globString
            self.msg = f"File is not a HDF5 or N5: {globString}"
            super().__init__(self.msg)

    class InconsistentShape(Exception):
        def __init__(self, fileName, datasetName):
            self.fileName = fileName
            self.msg = (
                f"Cannot stack dataset: {fileName}/{datasetName} because its shape differs from the shape of "
                f"the previous datasets"
            )
            super().__init__(self.msg)

    class InconsistentDType(Exception):
        def __init__(self, fileName, datasetName):
            self.fileName = fileName
            self.msg = (
                f"Cannot stack dataset: {fileName}/{datasetName} because its data type differs from the "
                f"type of the previous datasets"
            )
            super().__init__(self.msg)

    class NotTheSameFileError(Exception):
        def __init__(self, globString):
            self.globString = globString
            self.msg = f"Glob string encompasses more than one HDF5/N5 file: {globString}"
            super().__init__(self.msg)

    class NoInternalPlaceholderError(Exception):
        def __init__(self, globString):
            self.globString = globString
            self.msg = f"Glob string does not contain a placeholder: {globString}"
            super().__init__(self.msg)

    class ExternalPlaceholderError(Exception):
        def __init__(self, globString):
            self.globString = globString
            self.msg = f"Glob string does contains an external placeholder (not supported!): {globString}"
            super().__init__(self.msg)

    class FileOpenError(Exception):
        def __init__(self, fileName):
            self.fileName = fileName
            self.msg = f"Could not read file: {fileName}"
            super().__init__(self.msg)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._h5N5File = None
        self._readers = []
        self._opStacker = OpMultiArrayStacker(parent=self)
        self._opStacker.AxisIndex.setValue(0)

    def cleanUp(self):
        self._opStacker.Images.resize(0)
        for opReader in self._readers:
            opReader.cleanUp()
        if self._h5N5File is not None:
            assert isinstance(self._h5N5File, (h5py.File, z5py.N5File)), "_h5N5File should not be of any other type"
            self._h5N5File.close()

        super().cleanUp()

    def setupOutputs(self):
        archive_data_paths: List[ArchiveDataPath] = self.ArchiveDataPaths.value

        first_data_path = archive_data_paths[0]
        file_path = str(first_data_path.file_path)
        self._h5N5File = OpStreamingH5N5Reader.get_h5_n5_file(file_path, mode="r")

        num_files = len(archive_data_paths)
        self.OutputImage.connect(self._opStacker.Output)
        # Get slice axes from first image
        try:
            opFirstImg = OpStreamingH5N5Reader(parent=self)
            opFirstImg.InternalPath.setValue(str(first_data_path.internal_path))
            opFirstImg.H5N5File.setValue(self._h5N5File)
            slice_axes = opFirstImg.OutputImage.meta.getAxisKeys()
            opFirstImg.cleanUp()
        except RuntimeError as e:
            logger.error(str(e))
            raise OpStreamingH5N5SequenceReaderS.FileOpenError(str(first_data_path.file_path)) from e

        # Use given new axis or try to do something sensible
        if self.SequenceAxis.ready():
            new_axis: str = self.SequenceAxis.value
            assert len(new_axis) == 1
            assert new_axis in "tzyxc"
        else:
            # Try to pick an axis that doesn't already exist in each volume
            for new_axis in "tzc":
                if new_axis not in slice_axes:
                    break
            else:
                # All axes used already.
                # Stack across first existing axis
                new_axis = slice_axes[0]

        self._opStacker.Images.resize(0)
        self._opStacker.Images.resize(num_files)
        self._opStacker.AxisFlag.setValue(new_axis)

        for opReader in self._readers:
            opReader.cleanUp()

        self._readers = []
        dtype = None
        shape = None

        for data_path, stacker_slot in zip(archive_data_paths, self._opStacker.Images):
            internal_path = str(data_path.internal_path)
            opReader = OpStreamingH5N5Reader(parent=self)
            try:
                # Abort if the image-stack has no consistent dtype or shape
                if dtype is None:
                    dtype = self._h5N5File[internal_path].dtype
                    shape = self._h5N5File[internal_path].shape
                else:
                    if dtype != self._h5N5File[internal_path].dtype:
                        raise OpStreamingH5N5SequenceReaderS.InconsistentDType(file_path, internal_path)
                    if shape != self._h5N5File[internal_path].shape:
                        raise OpStreamingH5N5SequenceReaderS.InconsistentShape(file_path, internal_path)

                opReader.InternalPath.setValue(internal_path)
                opReader.H5N5File.setValue(self._h5N5File)
            except RuntimeError as e:
                logger.error(str(e))
                raise OpStreamingH5N5SequenceReaderS.FileOpenError(str(data_path)) from e
            else:
                stacker_slot.connect(opReader.OutputImage)
                self._readers.append(opReader)

    def propagateDirty(self, slot, subindex, roi):
        if slot == self.ArchiveDataPaths or slot == self.SequenceAxis:
            self.OutputImage.setDirty(slice(None))
