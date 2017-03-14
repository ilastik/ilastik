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

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.operators.generic import OpMultiArrayStacker
from lazyflow.operators.ioOperators.opStreamingHdf5Reader import OpStreamingHdf5Reader
from lazyflow.utility.pathHelpers import PathComponents, globHdf5

import logging
logger = logging.getLogger(__name__)


class OpStreamingHdf5SequenceReaderM(Operator):
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
    GlobString = InputSlot()
    SequenceAxis = InputSlot(optional=True)  # The axis to stack across.
    OutputImage = OutputSlot()

    class WrongFileTypeError(Exception):
        def __init__(self, globString):
            self.filename = globString
            self.msg = "File is not a HDF5: {}".format(globString)
            super(OpStreamingHdf5SequenceReaderM.WrongFileTypeError, self).__init__(self.msg)

    class NoExternalPlaceholderError(Exception):
        def __init__(self, globString):
            self.globString = globString
            self.msg = "Glob string does not contain a placeholder: {}".format(globString)
            super(OpStreamingHdf5SequenceReaderM.NoExternalPlaceholderError, self).__init__(self.msg)

    class SameFileError(Exception):
        def __init__(self, globString):
            self.globString = globString
            self.msg = "This reader only works with multiple h5 files: {}".format(globString)
            super(OpStreamingHdf5SequenceReaderM.SameFileError, self).__init__(self.msg)

    class SingleFileException(Exception):
        """Summary
        """
        def __init__(self, fileName):
            self.filename = fileName
            self.msg = "Only a single Hdf5 file supplied: {}".format(fileName)
            super(OpStreamingHdf5SequenceReaderM.SingleFileException, self).__init__(self.msg)

    def __init__(self, *args, **kwargs):
        super(OpStreamingHdf5SequenceReaderM, self).__init__(*args, **kwargs)
        self._hdf5Files = None
        self._readers = []
        self._opStacker = OpMultiArrayStacker(parent=self)
        self._opStacker.AxisIndex.setValue(0)

    def cleanUp(self):
        self._opStacker.Images.resize(0)
        for opReader in self._readers:
            opReader.cleanUp()
        self._hdf5Files = None
        super(OpStreamingHdf5SequenceReaderM, self).cleanUp()

    @staticmethod
    def expandGlobStrings(hdf5File, globStrings):
        """Matches a list of globStrings to internal paths of files

        Args:
            hdf5File: h5py.File object
            globStrings: string. glob or path strings delimited by os.pathsep

        Returns:
            List of internal paths matching the globstrings that were found in
            the provided h5py.File object
        """
        ret = []
        # Parse list into separate globstrings and combine them
        for globString in globStrings.split(os.path.pathsep):
            s = globString.strip()
            components = PathComponents(s)
            ret += sorted(
                globHdf5(
                    hdf5File, components.internalPath.lstrip('/')))
        return ret

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

        Returns:
            bool: True if rules are met -> this is the right reader
                  False if rules are not met -> this is not the right reader
        """
        pathStrings = globString.split(os.path.pathsep)

        pathComponents = [PathComponents(p.strip()) for p in pathStrings]
        assert len(pathComponents) > 0

        if not all(p.extension.lstrip('.') in OpStreamingHdf5Reader.H5EXTS
                   for p in pathComponents):
            raise OpStreamingHdf5SequenceReaderM.WrongFileTypeError(globString)

        if len(pathComponents) == 1:
            if '*' in pathComponents[0].externalPath:
                return True
            else:
                raise OpStreamingHdf5SequenceReaderM.NoExternalPlaceholderError(globString)
        else:
            sameExternal = all(pathComponents[0].externalPath == x.externalPath
                               for x in pathComponents[1::])
            if sameExternal is True:
                raise OpStreamingHdf5SequenceReaderM.SameFileError(globString)

        return True
