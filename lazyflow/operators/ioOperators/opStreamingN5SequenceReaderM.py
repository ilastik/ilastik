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

import z5py

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.operators.generic import OpMultiArrayStacker
from lazyflow.operators.ioOperators.opStreamingN5Reader import OpStreamingN5Reader
from lazyflow.utility.pathHelpers import PathComponents

import logging
logger = logging.getLogger(__name__)


class OpStreamingN5SequenceReaderM(Operator):
    """
    Imports a sequence of (ND) volumes inside multiple n5 file into a single volume (ND+1)

    The 'M' at the end of the file name implies that this class handles multiple
    volumes in multiple files.

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
    GlobString = InputSlot()
    SequenceAxis = InputSlot(optional=True)  # The axis to stack across.
    OutputImage = OutputSlot()
    N5EXTS = OpStreamingN5Reader.N5EXTS

    class WrongFileTypeError(Exception):
        def __init__(self, globString):
            self.filename = globString
            self.msg = "File is not a N5: {}".format(globString)
            super(OpStreamingN5SequenceReaderM.WrongFileTypeError, self).__init__(self.msg)

    class InconsistentShape(Exception):
        def __init__(self, fileName, datasetName):
            self.fileName = fileName
            self.msg = "Cannot stack dataset: {} because its shape differs from the shape of the previous " \
                       "datasets".format(fileName + '/' + datasetName)
            super(OpStreamingN5SequenceReaderM.InconsistentShape, self).__init__(self.msg)

    class InconsistentDType(Exception):
        def __init__(self, fileName, datasetName):
            self.fileName = fileName
            self.msg = "Cannot stack dataset: {} because its data type differs from the type of the previous " \
                       "datasets".format(fileName + '/' + datasetName)
            super(OpStreamingN5SequenceReaderM.InconsistentDType, self).__init__(self.msg)

    class NoExternalPlaceholderError(Exception):
        def __init__(self, globString):
            self.globString = globString
            self.msg = "Glob string does not contain a placeholder: {}".format(globString)
            super(OpStreamingN5SequenceReaderM.NoExternalPlaceholderError, self).__init__(self.msg)

    class SameFileError(Exception):
        def __init__(self, globString):
            self.globString = globString
            self.msg = "This reader only works with multiple n5 files: {}".format(globString)
            super(OpStreamingN5SequenceReaderM.SameFileError, self).__init__(self.msg)

    class FileOpenError(Exception):
        def __init__(self, fileName):
            self.fileName = fileName
            self.msg = "Could not read file: {}".format(fileName)
            super(OpStreamingN5SequenceReaderM.FileOpenError, self).__init__(self.msg)

    class InternalPlaceholderError(Exception):
        def __init__(self, globString):
            self.globString = globString
            self.msg = ("Glob string does contains an internal placeholder "
                        "(not supported!): {}".format(globString))
            super(OpStreamingN5SequenceReaderM.InternalPlaceholderError, self).__init__(self.msg)

    def __init__(self, *args, **kwargs):
        super(OpStreamingN5SequenceReaderM, self).__init__(*args, **kwargs)
        self._n5Files = []
        self._readers = []
        self._opStacker = OpMultiArrayStacker(parent=self)
        self._opStacker.AxisIndex.setValue(0)

    def cleanUp(self):
        self._opStacker.Images.resize(0)
        for opReader in self._readers:
            opReader.cleanUp()
        for n5File in self._n5Files:
            n5File.close()
        self._n5Files = None
        super(OpStreamingN5SequenceReaderM, self).cleanUp()

    def setupOutputs(self):
        self.checkGlobString(self.GlobString.value)
        external_paths, internal_paths = self.expandGlobStrings(
            self.GlobString.value)

        num_files = len(external_paths)
        if num_files == 0:
            self.OutputImage.disconnect()
            self.OutputImage.meta.NOTREADY = True
            return

        self.OutputImage.connect(self._opStacker.Output)
        # Get slice axes from first image
        try:
            n5FirstImage = z5py.N5File(external_paths[0], mode='r+')
            opFirstImg = OpStreamingN5Reader(parent=self)
            opFirstImg.InternalPath.setValue(internal_paths[0])
            opFirstImg.N5File.setValue(n5FirstImage)
            slice_axes = opFirstImg.OutputImage.meta.getAxisKeys()
            opFirstImg.cleanUp()
            n5FirstImage.close()
        except RuntimeError as e:
            logger.error(str(e))
            raise OpStreamingN5SequenceReaderM.FileOpenError(external_paths[0])

        # Use given new axis or try to do something sensible
        if self.SequenceAxis.ready():
            new_axis = self.SequenceAxis.value
            assert len(new_axis) == 1
            assert new_axis in 'tzyxc'
        else:
            # Try to pick an axis that doesn't already exist in each volume
            for new_axis in 'tzc0':
                if new_axis not in slice_axes:
                    break

            if new_axis == '0':
                # All axes used already.
                # Stack across first existing axis
                new_axis = slice_axes[0]

        self._opStacker.Images.resize(0)
        self._opStacker.Images.resize(num_files)
        self._opStacker.AxisFlag.setValue(new_axis)

        for opReader in self._readers:
            opReader.cleanUp()

        self._n5Files = []
        self._readers = []
        dtype = None
        shape = None
        for external_path, internal_path, stacker_slot in zip(
                external_paths, internal_paths, self._opStacker.Images):
            opReader = OpStreamingN5Reader(parent=self)
            try:
                n5File = z5py.N5File(external_path, 'r+')
                # Abort if the image-stack has no consistent dtype or shape
                if dtype is None:
                    dtype = n5File[internal_path].dtype
                    shape = n5File[internal_path].shape
                else:
                    if dtype is not n5File[internal_path].dtype:
                        raise OpStreamingN5SequenceReaderM.InconsistentDType(external_path, internal_path)
                    if shape != n5File[internal_path].shape:
                        raise OpStreamingN5SequenceReaderM.InconsistentShape(external_path, internal_path)
                opReader.InternalPath.setValue(internal_path)
                opReader.N5File.setValue(n5File)
            except RuntimeError as e:
                logger.error(str(e))
                raise OpStreamingN5SequenceReaderM.FileOpenError(external_path)
            else:
                stacker_slot.connect(opReader.OutputImage)
                self._readers.append(opReader)
                self._n5Files.append(n5File)

    def propagateDirty(self, slot, subindex, roi):
        if slot == self.SequenceAxis or slot == self.GlobString:
            self.OutputImage.setDirty(slice(None))

    @staticmethod
    def expandGlobStrings(globStrings):
        """Matches a list of globStrings to internal paths of files

        Args:
            globStrings: string. glob or path strings delimited by os.pathsep

        Returns:
            List of internal paths matching the globstrings that were found in
            the provided z5py.N5File object

        """
        external_paths = []
        internal_paths = []
        # Parse list into separate globstrings and combine them
        for globString in globStrings.split(os.path.pathsep):
            s = globString.strip()
            components = PathComponents(s)
            tmp = sorted(glob.glob(components.externalPath))
            external_paths.extend(tmp)
            internal_paths.extend(
                [components.internalPath for i in range(len(tmp))])
        return external_paths, internal_paths

    @staticmethod
    def checkGlobString(globString):
        """Checks whether globString is valid for this class

        Rules for globString:
            * must contain multiple external paths or
            * placeholder '*' in external path
            * must not contain placeholders in internal paths (for now)

        Args:
            globString (string): String, one or multiple paths separated with
              os.path.pathsep and possibly containing '*' as a placeholder.

        Raises:
            OpStreamingN5SequenceReaderM.InternalPlaceholderError: Raised if
              an internal placeholder is encountered!
            OpStreamingN5SequenceReaderM.NoExternalPlaceholderError: Raised if
              only a single path is supplied and no '*'-placeholder can be
              found. -> OpStreamingN5Reader should be used in this case.
            OpStreamingN5SequenceReaderM.SameFileError: If multiple volumes
              point to the same file this error is raised.
              -> OpStreamingN5SequenceReaderS should be used in this case.
            OpStreamingN5SequenceReaderM.WrongFileTypeError: If file-
              extensions are not among the known N5 extensions, this error is
              raised (see OpStreamingN5Reader.N5EXTS).
        """
        pathStrings = globString.split(os.path.pathsep)

        pathComponents = [PathComponents(p.strip()) for p in pathStrings]
        assert len(pathComponents) > 0

        if not all(p.extension in OpStreamingN5Reader.N5EXTS
                   for p in pathComponents):
            raise OpStreamingN5SequenceReaderM.WrongFileTypeError(globString)

        if len(pathComponents) == 1:
            if '*' in pathComponents[0].internalPath:
                raise OpStreamingN5SequenceReaderM.InternalPlaceholderError(globString)
            if '*' not in pathComponents[0].externalPath:
                raise OpStreamingN5SequenceReaderM.NoExternalPlaceholderError(globString)
        else:
            sameExternal = any(pathComponents[0].externalPath == x.externalPath
                               for x in pathComponents[1::])
            if sameExternal is True:
                raise OpStreamingN5SequenceReaderM.SameFileError(globString)
            internalPlaceHolder = any('*' in x.internalPath for x in pathComponents[1::])
            if internalPlaceHolder is True:
                raise OpStreamingN5SequenceReaderM.InternalPlaceholderError(globString)
