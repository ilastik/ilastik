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
import os
import glob
from typing import List

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.operators.generic import OpMultiArrayStacker
from lazyflow.operators.ioOperators.opStreamingH5N5Reader import OpStreamingH5N5Reader
from lazyflow.utility.pathHelpers import PathComponents
from ilastik.utility.data_url import ArchiveDataPath

import logging

logger = logging.getLogger(__name__)


class OpStreamingH5N5SequenceReaderM(Operator):
    """
    Imports a sequence of (ND) volumes inside multiple hdf5 file into a single volume (ND+1)

    The 'M' at the end of the file name implies that this class handles multiple
    volumes in a multiple files.

    :param globstring: A glob string as defined by the glob module. We
        also support the following special extension to globstring
        syntax: A single string can hold a *list* of globstrings.
        The delimiter that separates the globstrings in the list is
        OS-specific via os.path.pathsep.

        For example, on Linux the pathsep is':', so

            '/a/b/c.txt:/d/e/f.txt:../g/i/h.txt'

        is parsed as

            ['/a/b/c.txt', '/d/e/f.txt', '../g/i/h.txt']
    """

    ArchiveDataPaths = InputSlot()  # Union[List[H5DataPath], List[N5DataPath]]
    SequenceAxis = InputSlot(optional=True)  # The axis to stack across.
    OutputImage = OutputSlot()

    H5EXTS = OpStreamingH5N5Reader.H5EXTS
    N5EXTS = OpStreamingH5N5Reader.N5EXTS

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
                f"Cannot stack dataset: {fileName}/{datasetName} because its data type differs from the type "
                f"of the previous datasets"
            )
            super().__init__(self.msg)

    class NoExternalPlaceholderError(Exception):
        def __init__(self, globString):
            self.globString = globString
            self.msg = f"Glob string does not contain a placeholder: {globString}"
            super().__init__(self.msg)

    class SameFileError(Exception):
        def __init__(self, globString):
            self.globString = globString
            self.msg = f"This reader only works with multiple h5 files: {globString}"
            super().__init__(self.msg)

    class FileOpenError(Exception):
        def __init__(self, fileName):
            self.fileName = fileName
            self.msg = f"Could not read file: {fileName}"
            super().__init__(self.msg)

    class InternalPlaceholderError(Exception):
        def __init__(self, globString):
            self.globString = globString
            self.msg = f"Glob string does contains an internal placeholder " f"(not supported!): {globString}"
            super().__init__(self.msg)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._h5N5Files = []
        self._readers = []
        self._opStacker = OpMultiArrayStacker(parent=self)
        self._opStacker.AxisIndex.setValue(0)

    def cleanUp(self):
        self._opStacker.Images.resize(0)
        for opReader in self._readers:
            opReader.cleanUp()
        for hdfFile in self._h5N5Files:
            hdfFile.close()
        self._h5N5Files = None
        super().cleanUp()

    def setupOutputs(self):
        archive_data_paths: List[ArchiveDataPath] = self.ArchiveDataPaths.value
        external_paths: List[str] = [str(ap.file_path) for ap in archive_data_paths]
        internal_paths: List[str] = [str(ap.internal_path) for ap in archive_data_paths]

        self.OutputImage.connect(self._opStacker.Output)
        # Get slice axes from first image
        try:
            h5N5FirstImage = OpStreamingH5N5Reader.get_h5_n5_file(external_paths[0], mode="r")
            opFirstImg = OpStreamingH5N5Reader(parent=self)
            opFirstImg.InternalPath.setValue(internal_paths[0])
            opFirstImg.H5N5File.setValue(h5N5FirstImage)
            slice_axes = opFirstImg.OutputImage.meta.getAxisKeys()
            opFirstImg.cleanUp()
            h5N5FirstImage.close()
        except RuntimeError as e:
            logger.error(str(e))
            raise OpStreamingH5N5SequenceReaderM.FileOpenError(external_paths[0]) from e

        # Use given new axis or try to do something sensible
        if self.SequenceAxis.ready():
            new_axis = self.SequenceAxis.value
            assert len(new_axis) == 1
            assert new_axis in "tzyxc"
        else:
            # Try to pick an axis that doesn't already exist in each volume
            for new_axis in "tzc0":
                if new_axis not in slice_axes:
                    break

            if new_axis == "0":
                # All axes used already.
                # Stack across first existing axis
                new_axis = slice_axes[0]

        self._opStacker.Images.resize(0)
        self._opStacker.Images.resize(len(external_paths))
        self._opStacker.AxisFlag.setValue(new_axis)

        for opReader in self._readers:
            opReader.cleanUp()

        self._h5N5Files = []
        self._readers = []
        dtype = None
        shape = None
        for external_path, internal_path, stacker_slot in zip(external_paths, internal_paths, self._opStacker.Images):
            opReader = OpStreamingH5N5Reader(parent=self)
            try:
                h5N5File = OpStreamingH5N5Reader.get_h5_n5_file(external_path, mode="r")
                if dtype is None:
                    dtype = h5N5File[internal_path].dtype
                    shape = h5N5File[internal_path].shape
                else:
                    if dtype != h5N5File[internal_path].dtype:
                        raise OpStreamingH5N5SequenceReaderM.InconsistentDType(external_path, internal_path)
                    if shape != h5N5File[internal_path].shape:
                        raise OpStreamingH5N5SequenceReaderM.InconsistentShape(external_path, internal_path)
                opReader.InternalPath.setValue(internal_path)
                opReader.H5N5File.setValue(h5N5File)
            except RuntimeError as e:
                logger.error(str(e))
                raise OpStreamingH5N5SequenceReaderM.FileOpenError(external_path) from e
            else:
                stacker_slot.connect(opReader.OutputImage)
                self._readers.append(opReader)
                self._h5N5Files.append(h5N5File)

    def propagateDirty(self, slot, subindex, roi):
        if slot == self.SequenceAxis or slot == self.ArchiveDataPaths:
            self.OutputImage.setDirty(slice(None))
