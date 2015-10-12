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
#           http://ilastik.org/license/
###############################################################################
import os
import re
import numpy
import vigra
from lazyflow.graph import Operator, InputSlot, OutputSlot

class OpRawBinaryFileReader(Operator):
    """
    This operator can be used to read 'raw' binary files from disk,
    i.e. files with no metadata whatsoever, just the raw buffer of pixel values.

    Since there is no metadata in the file, we must infer the volume's shape and
    dtype from the filename. By convention, we expect the volume dimensions to be
    separated by '-'  characters, and the dtype name must be present in the filename.
    
    For example:
        /path/to/myvolume-100-200-300-3-uint8.bin
    
    For now, the axis order is merely guessed. 
    """
    name = "OpRawBinaryFileReader"

    FilePath = InputSlot(stype='filestring')
    Output = OutputSlot()

    class DatasetReadError(Exception):
        pass

    def __init__(self, *args, **kwargs):
        super(OpRawBinaryFileReader, self).__init__(*args, **kwargs)
        self._memmap = None

    def cleanUp(self):
        self._memmap = None # Closes the file
        super(OpRawBinaryFileReader, self).cleanUp()

    def setupOutputs(self):
        self._memmap = None # Closes the file
        filepath = self.FilePath.value
        filename = os.path.split(filepath)[1]
        
        # Infer the dimensions by parsing the filename
        # We split on . and - characters
        shape = ()
        for s in re.split('\.|-', filename):
            try:
                shape += (int(s),)
            except ValueError:
                pass
        
        if not ( 3 <= len(shape) <= 5 ):
            raise OpRawBinaryFileReader.DatasetReadError( "Binary filename does not include a valid shape: {}".format(filename) )
        
        # Uint8 by default, but search for an explicit type in the filename
        dtype = numpy.uint8
        for d in 'uint8 uint16 uint32 uint64 int8 int16 int32 int64 float32 float64'.split():
            if d in filename:
                dtype = numpy.dtype(d).type
                break
        
        try:
            self._memmap = numpy.memmap(filepath, dtype=dtype, shape=shape, mode='r')
        except:
            raise OpRawBinaryFileReader.DatasetReadError( "Unable to open numpy dataset: {}".format( filepath ) )

        axisorders = { 2 : 'yx',
                       3 : 'zyx',
                       4 : 'zyxc',
                       5 : 'tzyxc' }

        ndims = len( shape )
        assert ndims != 0, "OpRawBinaryFileReader: Support for 0-D data not yet supported"
        assert ndims != 1, "OpRawBinaryFileReader: Support for 1-D data not yet supported"
        assert ndims <= 5, "OpRawBinaryFileReader: No support for data with more than 5 dimensions."

        axisorder = axisorders[ndims]
        if ndims == 3 and shape[2] <= 4:
            # Special case: If the 3rd dim is small, assume it's 'c', not 'z'
            axisorder = 'yxc'

        self.Output.meta.dtype = dtype
        self.Output.meta.axistags = vigra.defaultAxistags(axisorder)
        self.Output.meta.shape = shape

    def execute(self, slot, subindex, roi, result):
        result[:] = self._memmap[roi.toSlice()]
        return result

    def propagateDirty(self, slot, subindex, roi):
        if slot == self.FilePath:
            self.Output.setDirty( slice(None) )
