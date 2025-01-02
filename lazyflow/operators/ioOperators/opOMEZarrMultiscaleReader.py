###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2024, the ilastik developers
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
from lazyflow.utility.io_util.OMEZarrStore import OMEZarrStore
from lazyflow.utility.io_util.multiscaleStore import DEFAULT_SCALE_KEY

logger = logging.getLogger(__name__)


class OpOMEZarrMultiscaleReader(Operator):
    """
    Operator to plug the OME-Zarr loader into lazyflow.

    :param metadata_only_mode: Passed through to the internal OMEZarrStore.
        If True, only the last scale is loaded to determine the dtype. Used to shorten init time
        when DatasetInfo instantiates an OpInputDataReader to get lane shape and dtype.
    """

    name = "OpOMEZarrMultiscaleReader"

    Uri = InputSlot()  # May point to any path within an OME-Zarr group
    Scale = InputSlot(optional=True)  # Selected through GUI

    Output = OutputSlot()

    def __init__(self, metadata_only_mode=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._load_only_one_scale = metadata_only_mode
        self._store = None

    def setupOutputs(self):
        if self._store is not None and self._store.base_uri in self.Uri.value:
            # Must not set Output.meta here, because downstream ilastik can't handle changing lane shape
            return
        # self.Scale is not ready when coming through instantiate_dataset_info -> MultiscaleUrlDatasetInfo.__init__
        # it's ready but == DEFAULT_SCALE_KEY when coming through OpDataSelection after first loading the dataset
        # it's ready and != DEFAULT_SCALE_KEY after selecting a scale in the GUI
        selected_scale = self.Scale.value if self.Scale.ready() and self.Scale.value != DEFAULT_SCALE_KEY else None
        self._store = OMEZarrStore(self.Uri.value, selected_scale, single_scale_mode=self._load_only_one_scale)
        active_scale = selected_scale or self._store.scale_sub_path or self._store.lowest_resolution_key
        self.Output.meta.shape = self._store.get_shape(active_scale)
        self.Output.meta.dtype = self._store.dtype
        self.Output.meta.axistags = self._store.axistags
        self.Output.meta.scales = self._store.multiscales
        # Used to correlate export with input scale, to feed back to DatasetInfo, and in execute
        self.Output.meta.active_scale = active_scale
        # Many public OME-Zarr datasets are chunked as full xy slices,
        # so orthoviews lead to downloading the entire dataset.
        self.Output.meta.prefer_2d = True
        # Add OME-Zarr metadata to slot so that it can be ported over to an export
        self.Output.meta.ome_zarr_meta = self._store.ome_meta_for_export

    def execute(self, slot, subindex, roi, result):
        result[...] = self._store.request(roi, self.Output.meta.active_scale)
        return result

    def propagateDirty(self, slot, subindex, roi):
        self.Output.setDirty(slice(None))
