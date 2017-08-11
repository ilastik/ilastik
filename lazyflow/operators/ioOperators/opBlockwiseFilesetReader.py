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
#		   http://ilastik.org/license/
###############################################################################
import os
import vigra
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.utility.io_util.blockwiseFileset import BlockwiseFileset
from lazyflow.operators import OpDummyData

import logging
logger = logging.getLogger(__name__)

class OpBlockwiseFilesetReader(Operator):
    """
    Adapter that provides an operator interface to the BlockwiseFileset class for reading ONLY.
    """
    name = "OpBlockwiseFilesetReader"

    DescriptionFilePath = InputSlot(stype='filestring')
    Output = OutputSlot()

    class MissingDatasetError(Exception):
        pass

    def __init__(self, *args, **kwargs):
        super(OpBlockwiseFilesetReader, self).__init__(*args, **kwargs)
        self._blockwiseFileset = None
        self._opDummyData = OpDummyData( parent=self )
        
    def setupOutputs(self):
        if not os.path.exists(self.DescriptionFilePath.value):
            raise OpBlockwiseFilesetReader.MissingDatasetError("Dataset description not found: {}".format( self.DescriptionFilePath.value ) )

        # Load up the class that does the real work
        self._blockwiseFileset = BlockwiseFileset( self.DescriptionFilePath.value )

        # Check for errors in the description file
        descriptionFields = self._blockwiseFileset.description
        axes = descriptionFields.axes
        assert False not in [a in 'txyzc' for a in axes], "Unknown axis type.  Known axes: txyzc  Your axes:".format(axes)

        self.Output.meta.shape = tuple(descriptionFields.view_shape)
        self.Output.meta.dtype = descriptionFields.dtype
        self.Output.meta.axistags = vigra.defaultAxistags(str(descriptionFields.axes))
        drange = descriptionFields.drange
        if drange is not None:
            self.Output.meta.drange = drange

    def execute(self, slot, subindex, roi, result):
        assert slot == self.Output, "Unknown output slot"
        try:
            self._blockwiseFileset.readData( (roi.start, roi.stop), result )
        except BlockwiseFileset.BlockNotReadyError:
            result[:] = self._opDummyData.execute( slot, subindex, roi, result )
        return result

    def propagateDirty(self, slot, subindex, roi):
        assert slot == self.DescriptionFilePath, "Unknown input slot."
        self.Output.setDirty( slice(None) )
        
    def cleanUp(self):
        if self._blockwiseFileset is not None:
            self._blockwiseFileset.close()
        super(OpBlockwiseFilesetReader, self).cleanUp()

