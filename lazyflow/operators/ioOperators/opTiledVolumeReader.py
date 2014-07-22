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
import vigra
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.utility.io.tiledVolume import TiledVolume
import logging
logger = logging.getLogger(__name__)

class OpTiledVolumeReader(Operator):
    """
    An operator to retrieve volumes from a remote server that provides volumes via image tiles.
    The operator requires a LOCAL json config file that describes the remote dataset and interface.
    (See tiledVolume.py)
    """
    DescriptionFilePath = InputSlot(stype='filestring')
    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpTiledVolumeReader, self).__init__(*args, **kwargs)
        self._volumeObject = None

    def setupOutputs(self):
        # Create a TiledVolume object to read the description file and do the downloads.
        self._volumeObject = TiledVolume( self.DescriptionFilePath.value )

        self.Output.meta.shape = tuple(self._volumeObject.description.shape)
        self.Output.meta.dtype = self._volumeObject.description.dtype
        self.Output.meta.axistags = vigra.defaultAxistags(self._volumeObject.description.axes)

    def execute(self, slot, subindex, roi, result):
        self._volumeObject.read( (roi.start, roi.stop), result )
        return result

    def propagateDirty(self, slot, subindex, roi):
        assert slot == self.DescriptionFilePath, "Unknown input slot."
        self.Output.setDirty( slice(None) )
