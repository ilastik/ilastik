# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Copyright 2011-2014, the ilastik developers

from lazyflow.graph import Operator, InputSlot, OutputSlot

import vigra
import numpy
import copy

class OpNpyFileReader(Operator):
    name = "OpNpyFileReader"
    category = "Input"

    FileName = InputSlot(stype='filestring')
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
            rawNumpyArray = numpy.load(str(fileName), 'r')
            self._memmapFile = rawNumpyArray._mmap
        except:
            raise OpNpyFileReader.DatasetReadError( "Unable to open numpy dataset: {}".format( fileName ) )

        axisorders = { 2 : 'xy',
                       3 : 'xyz',
                       4 : 'xyzc',
                       5 : 'txyzc' }

        shape = rawNumpyArray.shape
        ndims = len( shape )
        assert ndims != 0, "OpNpyFileReader: Support for 0-D data not yet supported"
        assert ndims != 1, "OpNpyFileReader: Support for 1-D data not yet supported"
        assert ndims <= 5, "OpNpyFileReader: No support for data with more than 5 dimensions."

        axisorder = axisorders[ndims]
        if ndims == 3 and shape[2] <= 4:
            # Special case: If the 3rd dim is small, assume it's 'c', not 'z'
            axisorder = 'xyc'

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
            self.Output.setDirty( slice(None) )
        
    def cleanUp(self):
        if self._memmapFile is not None:
            self._memmapFile.close()
        super(OpNpyFileReader, self).cleanUp()
