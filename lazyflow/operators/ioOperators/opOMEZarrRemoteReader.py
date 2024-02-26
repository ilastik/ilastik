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
import logging

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.utility.io_util.OMEZarrRemoteStore import OMEZarrRemoteStore

logger = logging.getLogger(__name__)


class OpOMEZarrRemoteReader(Operator):

    name = "OpOMEZarrRemoteReader"

    BaseUrl = InputSlot()
    Scale = InputSlot(optional=True)

    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._store = None

    def setupOutputs(self):
        if self._store is None or self._store.url != self.BaseUrl.value:
            self._store = OMEZarrRemoteStore(self.BaseUrl.value)

        active_scale = self.Scale.value if self.Scale.ready() else self._store.lowest_resolution_key
        self.Output.meta.shape = self._store.get_shape(active_scale)
        self.Output.meta.dtype = self._store.dtype
        self.Output.meta.axistags = self._store.axistags
        self.Output.meta.scales = self._store.multiscales
        # To feed back to DatasetInfo and hence the project file
        self.Output.meta.lowest_scale = self._store.lowest_resolution_key
        self.Output.meta.prefer_2d = True

    def execute(self, slot, subindex, roi, result):
        scale = self.Scale.value if self.Scale.ready() and self.Scale.value else self._store.lowest_resolution_key
        result[...] = self._store.request(roi, scale)
        return result

    def propagateDirty(self, slot, subindex, roi):
        self.Output.setDirty(slice(None))
