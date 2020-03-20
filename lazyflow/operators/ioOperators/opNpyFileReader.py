###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2014, the ilastik developers
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
# 		   http://ilastik.org/license/
###############################################################################
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.utility.helpers import get_default_axisordering

import vigra
import numpy
import copy

import logging

logger = logging.getLogger(__name__)


class OpNpyFileReader(Operator):
    name = "OpNpyFileReader"
    category = "Input"

    FileName = InputSlot(stype="filestring")
    InternalPath = InputSlot(optional=True)

    Output = OutputSlot()

    class DatasetReadError(Exception):
        pass

    def __init__(self, *args, **kwargs):
        super(OpNpyFileReader, self).__init__(*args, **kwargs)
        self._memmapFile = None
        self._rawVigraArray = None

    def setupOutputs(self):
        """
        Load the file specified via our input slot and present its data on the output slot.
        """
        if self._memmapFile is not None:
            self._memmapFile.close()
        fileName = self.FileName.value

        try:
            # Load the file in read-only "memmap" mode to avoid reading it from disk all at once.
            rawLoadedNumpyObject = numpy.load(str(fileName), mmap_mode="r", allow_pickle=False)
        except (ValueError, IOError):
            raise OpNpyFileReader.DatasetReadError("Unable to open numpy dataset: {}".format(fileName))

        # .npy files:
        if isinstance(rawLoadedNumpyObject, numpy.ndarray):
            rawNumpyArray = rawLoadedNumpyObject
            self._memmapFile = rawNumpyArray._mmap
        # .npz files:
        elif isinstance(rawLoadedNumpyObject, numpy.lib.npyio.NpzFile):
            if self.InternalPath.ready():
                try:
                    rawNumpyArray = rawLoadedNumpyObject[self.InternalPath.value]
                except KeyError:
                    raise OpNpyFileReader.DatasetReadError(
                        "InternalPath not found in file. Unable to open numpy npz dataset: "
                        "{fileName}: {internalPath}".format(fileName=fileName, internalPath=self.InternalPath.value)
                    )
            else:
                raise OpNpyFileReader.DatasetReadError(
                    "InternalPath not given. Unable to open numpy npz dataset: " "{fileName}".format(fileName=fileName)
                )

        shape = rawNumpyArray.shape

        axisorder = get_default_axisordering(shape)

        # Cast to vigra array
        self._rawVigraArray = rawNumpyArray.view(vigra.VigraArray)
        self._rawVigraArray.axistags = vigra.defaultAxistags(axisorder)

        self.Output.meta.dtype = self._rawVigraArray.dtype.type
        self.Output.meta.axistags = copy.copy(self._rawVigraArray.axistags)
        self.Output.meta.shape = self._rawVigraArray.shape

    def execute(self, slot, subindex, roi, result):
        key = roi.toSlice()
        result[:] = self._rawVigraArray[key]
        return result

    def propagateDirty(self, slot, subindex, roi):
        if slot == self.FileName:
            self.Output.setDirty(slice(None))

    def cleanUp(self):
        if self._memmapFile is not None:
            self._memmapFile.close()
        super(OpNpyFileReader, self).cleanUp()
