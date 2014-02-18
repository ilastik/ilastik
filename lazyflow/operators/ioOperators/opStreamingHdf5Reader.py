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

#Python
import logging
import time

#SciPy
import vigra

from lazyflow.graph import Operator, InputSlot, OutputSlot

class OpStreamingHdf5Reader(Operator):
    """
    The top-level operator for the data selection applet.
    """
    name = "OpStreamingHdf5Reader"
    category = "Reader"

    # The project hdf5 File object (already opened)
    Hdf5File = InputSlot(stype='hdf5File')

    # The internal path for project-local datasets
    InternalPath = InputSlot(stype='string')

    # Output data
    OutputImage = OutputSlot()
    
    loggingName = __name__ + ".OpStreamingHdf5Reader"
    logger = logging.getLogger(loggingName)
    
    class DatasetReadError(Exception):
        def __init__(self, internalPath):
            self.internalPath = internalPath
            self.msg = "Unable to open Hdf5 dataset: {}".format( internalPath )
            super(OpStreamingHdf5Reader.DatasetReadError, self).__init__( self.msg )

    def __init__(self, *args, **kwargs):
        super(OpStreamingHdf5Reader, self).__init__(*args, **kwargs)
        self._hdf5File = None

    def setupOutputs(self):
        # Read the dataset meta-info from the HDF5 dataset
        self._hdf5File = self.Hdf5File.value
        internalPath = self.InternalPath.value

        if internalPath not in self._hdf5File:
            raise OpStreamingHdf5Reader.DatasetReadError(internalPath)

        dataset = self._hdf5File[internalPath]

        try:
            # Read the axistags property without actually importing the data
            axistagsJson = self._hdf5File[internalPath].attrs['axistags'] # Throws KeyError if 'axistags' can't be found
            axistags = vigra.AxisTags.fromJSON(axistagsJson)
        except KeyError:
            # No axistags found.
            ndims = len(dataset.shape)
            assert ndims != 0, "OpStreamingHdf5Reader: Zero-dimensional datasets not supported."
            assert ndims != 1, "OpStreamingHdf5Reader: Support for 1-D data not yet supported"
            assert ndims <= 5, "OpStreamingHdf5Reader: No support for data with more than 5 dimensions."

            axisorders = { 2 : 'xy',
                           3 : 'xyz',
                           4 : 'xyzc',
                           5 : 'txyzc' }
    
            axisorder = axisorders[ndims]
            if ndims == 3 and dataset.shape[2] <= 4:
                # Special case: If the 3rd dim is small, assume it's 'c', not 'z'
                axisorder = 'xyc'

            axistags = vigra.defaultAxistags(axisorder)

        assert len(axistags) == len( dataset.shape ),\
            "Mismatch between shape {} and axisorder {}".format( dataset.shape, axisorder )

        # Configure our slot meta-info
        self.OutputImage.meta.dtype = dataset.dtype.type
        self.OutputImage.meta.shape = dataset.shape
        self.OutputImage.meta.axistags = axistags

        # If the dataset specifies a datarange, add it to the slot metadata
        if 'drange' in self._hdf5File[internalPath].attrs:
            self.OutputImage.meta.drange = tuple( self._hdf5File[internalPath].attrs['drange'] )

    def execute(self, slot, subindex, roi, result):
        t = time.time()
        assert self._hdf5File is not None
        # Read the desired data directly from the hdf5File
        key = roi.toSlice()
        hdf5File = self._hdf5File
        internalPath = self.InternalPath.value
        
        if result.flags.c_contiguous:
            hdf5File[internalPath].read_direct( result[...], key )
        else:
            result[...] = hdf5File[internalPath][key]
        if self.logger.getEffectiveLevel() >= logging.DEBUG:
            t = 1000.0*(time.time()-t)
            self.logger.debug("took %f msec." % t)

    def propagateDirty(self, slot, subindex, roi):
        if slot == self.Hdf5File or slot == self.InternalPath:
            self.OutputImage.setDirty( slice(None) )
