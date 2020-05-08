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
from fs.base import FS
import numpy as np
import vigra
from pathlib import Path
from typing import Optional, Tuple

from lazyflow.graph import Graph, Operator, OutputSlot
from lazyflow.rtype import Roi
from ndstructs import Point5D, Slice5D, Shape5D
from ndstructs.datasource import PrecomputedChunksDataSource

class OpPrecomputedChunksDataSource(Operator):
    """
    An operator to retrieve precomputed chunked volumes from a remote server.
    These types of volumes are e.g. used in neuroglancer.
    """

    name = "OpPrecomputedChunksDataSource"
    Output = OutputSlot()

    def __init__(
        self,
        path: Path,
        *,
        filesystem: FS,
        chunk_size: Optional[Shape5D] = None,
        parent: Optional[Operator] = None,
        graph: Optional[Graph] = None
    ):
        super().__init__(parent=parent, graph=graph)
        self.datasource = PrecomputedChunksDataSource(path=path, filesystem=filesystem)
        self.Output.meta.shape = self.datasource.shape.to_tuple(self.datasource.axiskeys)
        self.Output.meta.dtype = self.datasource.dtype.type
        self.Output.meta.axistags = vigra.defaultAxistags(self.datasource.axiskeys)
        self.Output.meta.ideal_blockshape = self.datasource.tile_shape.to_tuple(self.datasource.axiskeys)

    def execute(self, slot: OutputSlot, subindex: int, roi: Roi, result: np.ndarray):
        assert slot == self.Output
        start = Point5D.zero(**dict(zip(self.datasource.axiskeys, roi.start)))
        stop = Point5D.one(**dict(zip(self.datasource.axiskeys, roi.stop)))
        slc = Slice5D.create_from_start_stop(start=start, stop=stop)
        data = self.datasource.retrieve(slc)
        result[...] = data.raw(self.datasource.axiskeys)
        return result

    def setupOutputs(self):
        pass

    def propagateDirty(self, slot, subindex, roi):
        pass
