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

import logging
import pathlib

import numpy as np
import psutil
import tifffile

from lazyflow.graph import InputSlot, Operator
from lazyflow.operators.opReorderAxes import OpReorderAxes
from lazyflow.utility import OrderedSignal, RoiRequestBufferIter


logger = logging.getLogger(__name__)


class OpExportMultipageTiff(Operator):
    """Export to multi-page OME-TIFF.

    Attributes:
        Input: Image data source (input slot).
        Filepath: Path to the exported image (input slot).
        progressSignal: Subscribe to this signal to receive export progress updates.
    """

    Input = InputSlot()
    Filepath = InputSlot()

    _DEFAULT_BATCH_SIZE = 4
    # OME-TIFF requires 5D with arbitrary order.
    _EXPORT_AXES = "tzcyx"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.progressSignal = OrderedSignal()

        self._opReorderAxes = OpReorderAxes(parent=self)
        self._opReorderAxes.Input.connect(self.Input)
        self._opReorderAxes.AxisOrder.setValue(self._EXPORT_AXES)

    def setupOutputs(self):
        pass

    def execute(self, slot, subindex, roi, result):
        pass

    def propagateDirty(self, slot, subindex, roi):
        pass

    def run_export(self) -> None:
        """Export an image from Input to Filepath."""
        path = pathlib.Path(self.Filepath.value)
        if path.exists():
            path.unlink()

        dtype = self._opReorderAxes.Output.meta.dtype
        if isinstance(dtype, type):
            dtype = dtype().dtype

        page_buf = RoiRequestBufferIter(self._opReorderAxes.Output, self._batch_size)
        page_buf.progress_signal.subscribe(self.progressSignal)

        with tifffile.TiffWriter(self.Filepath.value, byteorder="<", ome=True) as writer:
            writer.write(
                data=page_buf,
                shape=self._opReorderAxes.Output.meta.shape,
                dtype=dtype,
                software="ilastik",
                metadata={"axes": "".join(self._opReorderAxes.Output.meta.getAxisKeys())},
            )

    @property
    def _batch_size(self) -> int:
        bytes_per_pixel = self.Input.meta.ram_usage_per_requested_pixel
        if not bytes_per_pixel:
            return self._DEFAULT_BATCH_SIZE

        shape = self._opReorderAxes.Output.meta.shape

        nchannels = self.Input.meta.getTaggedShape().get("c", 1)
        pixels_per_page = np.prod(shape[-2:]) // nchannels
        bytes_per_page = bytes_per_pixel * pixels_per_page

        total_bytes = psutil.virtual_memory().available // 2
        batch_size = total_bytes // bytes_per_page

        npages = np.prod(shape[:-2])
        return min(batch_size, npages)
