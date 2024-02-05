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

import numpy
import vigra

import lazyflow.roi
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.operators.opBlockedArrayCache import OpBlockedArrayCache
from lazyflow.utility.helpers import bigintprod
from lazyflow.utility.io_util.OMEZarrRemoteStore import OMEZarrRemoteStore

logger = logging.getLogger(__name__)


class OpOMEZarrRemoteReaderNoCache(Operator):

    name = "OpOMEZarrRemoteReaderNoCache"

    BaseUrl = InputSlot()
    Scale = InputSlot(optional=True)

    Output = OutputSlot()
    ChunkSize = OutputSlot()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._store = None

    def setupOutputs(self):
        if self._store is None or self._store.url != self.BaseUrl.value:
            self._store = OMEZarrRemoteStore(self.BaseUrl.value)

        active_scale = self.Scale.value if self.Scale.ready() else self._store.lowest_resolution_key
        self.ChunkSize.setValue(self._store.get_chunk_size(active_scale))
        self.Output.meta.shape = self._store.get_shape(active_scale)
        self.Output.meta.dtype = self._store.dtype
        self.Output.meta.axistags = vigra.defaultAxistags(self._store.axes)
        self.Output.meta.scales = self._store.scales
        # To feed back to DatasetInfo and hence the project file
        self.Output.meta.lowest_scale = self._store.lowest_resolution_key
        self.Output.meta.prefer_2d = True

    def execute(self, slot, subindex, roi, result):
        """
        Args:
            slot (OutputSlot): Requested slot
            subindex (tuple): Subslot index for multi-level slots
            roi (rtype.Roi): we assume tczyx order here
            result (ndarray): array in which the results are written in

        """
        scale = self.Scale.value if self.Scale.ready() and self.Scale.value else self._store.lowest_resolution_key
        result[...] = self._store.request(roi, scale)
        return result

    def propagateDirty(self, slot, subindex, roi):
        self.Output.setDirty(slice(None))


class OpOMEZarrRemoteReader(Operator):
    fixAtCurrent = InputSlot(value=False, stype="bool")

    BaseUrl = InputSlot()
    Scale = InputSlot(optional=True)

    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reader = OpOMEZarrRemoteReaderNoCache(parent=self)
        self.reader.BaseUrl.connect(self.BaseUrl)
        self.reader.Scale.connect(self.Scale)

        self.cache = OpBlockedArrayCache(parent=self)
        self.cache.name = "input_image_cache"
        self.cache.fixAtCurrent.connect(self.fixAtCurrent)
        self.cache.BlockShape.connect(self.reader.ChunkSize)
        self.cache.Input.connect(self.reader.Output)
        self.Output.connect(self.cache.Output)

    def propagateDirty(self, slot, subindex, roi):
        self.Output.setDirty(slice(None))

    def cleanUp(self):
        self.cache.Input.disconnect()
        self.cache.BlockShape.disconnect()


if __name__ == "__main__":
    # assumes there is a server running at localhost
    logging.basicConfig(level=logging.DEBUG)
    volume_url = "https://uk1s3.embassy.ebi.ac.uk/idr/zarr/v0.1/12689244.zarr/"

    from lazyflow import graph

    g = graph.Graph()
    op = OpOMEZarrRemoteReader(graph=g)
    op.BaseUrl.setValue(volume_url)
    print(f"Number of scales: {len(op.Output.meta.scales)}")

    op.Scale.setValue(op.Output.meta.lowest_scale)
    # get some data
    roi = ((0, 0, 0, 0, 0), (1, 1, 10, 66, 78))
    data = op.Output(*roi).wait()
    import h5py

    with h5py.File("C:\\Users\\root\\temph5.h5", "w") as f:
        f.create_dataset("exported", data=data)

    # get some data for the second time, check on server that it has only
    # been requested once
    data2 = op.Output(*roi).wait()
