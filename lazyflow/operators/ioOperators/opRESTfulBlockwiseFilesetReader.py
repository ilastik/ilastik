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

import os
import vigra
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.utility.io.RESTfulBlockwiseFileset import RESTfulBlockwiseFileset

import logging
logger = logging.getLogger(__name__)

class OpRESTfulBlockwiseFilesetReader(Operator):
    """
    Adapter that provides an operator interface to the BlockwiseFileset class for reading ONLY.
    """
    name = "OpRESTfulBlockwiseFilesetReader"

    DescriptionFilePath = InputSlot(stype='filestring')
    Output = OutputSlot()

    class MissingDatasetError(Exception):
        pass

    def __init__(self, *args, **kwargs):
        super(OpRESTfulBlockwiseFilesetReader, self).__init__(*args, **kwargs)
        self._blockwiseFileset = None

    def setupOutputs(self):
        if not os.path.exists(self.DescriptionFilePath.value):
            raise OpRESTfulBlockwiseFilesetReader.MissingDatasetError("Dataset description not found: {}".format( self.DescriptionFilePath.value ) )
        
        # Load up the class that does the real work
        self._blockwiseFileset = RESTfulBlockwiseFileset( self.DescriptionFilePath.value )

        # Check for errors in the description file
        localDescription = self._blockwiseFileset.compositeDescription.local_description
        axes = localDescription.axes
        assert False not in map(lambda a: a in 'txyzc', axes), "Unknown axis type.  Known axes: txyzc  Your axes:".format(axes)

        self.Output.meta.shape = tuple(localDescription.view_shape)
        self.Output.meta.dtype = localDescription.dtype
        self.Output.meta.axistags = vigra.defaultAxistags(localDescription.axes)
        drange = localDescription.drange
        if drange is not None:
            self.Output.meta.drange = drange

    def execute(self, slot, subindex, roi, result):
        assert slot == self.Output, "Unknown output slot"
        self._blockwiseFileset.readData( (roi.start, roi.stop), result )
        return result

    def propagateDirty(self, slot, subindex, roi):
        assert slot == self.DescriptionFilePath, "Unknown input slot."
        self.Output.setDirty( slice(None) )
        
    def cleanUp(self):
        import sys
        if self._blockwiseFileset is not None:
            self._blockwiseFileset.close()
        super(OpRESTfulBlockwiseFilesetReader, self).cleanUp()

