###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2026, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#          http://ilastik.org/license.html
###############################################################################
import logging
from functools import partial
from typing import Dict, List, Tuple

import vigra
from qtpy.QtCore import Qt

from ilastik.widgets.labelExplorer import LabelExplorerBase, LookupDelegate, AnnotationAnchor
from lazyflow.base import SPATIAL_AXES, Axiskey
from lazyflow.request.request import Request, RequestPool
from lazyflow.roi import getIntersectingBlocks, roiToSlice
from lazyflow.slot import OutputSlot
from lazyflow.utility.timer import timeLogged

from .connectBlockedLabels import Block, Neighborhood, SpatialAxesKeys, connect_regions, extract_annotations

logger = logging.getLogger(__name__)


class PixelLabelExplorerWidget(LabelExplorerBase):
    """Label Explorer for workflows with sparse pixel annotations

    Has 2 modes of operation:
      * if `label_slot.meta.is_blocked_cache` is True it is assumed to be connected to a blocked cache
        (as in Pixel Classification and derived workflows).
        `label_slot.meta.ideal_blockshape` must be set and should correspond to the block size signaled
        through `nonzero_block_slot`. -> Neighborhood.SINGLE
        Note: Neighborhood.NDIM would lead to perfect results in every situation. In practice considering
        Neighborhood,SINGLE would diverge from the perfect result only if the label has exactly 1Pixel wide
        annotations in diagonal blocks.
      * if `label_slot.meta.is_blocked_cache` is not True it indicates a non-blocked cache - as used in
        Carving and Counting. In this case it is assumed that any update will require update of the
        whole label array. -> Neighborhood.NONE
    """

    display_text = "Label Explorer"

    def __init__(
        self,
        nonzero_blocks_slot: OutputSlot,
        label_slot: OutputSlot,
        parent=None,
    ):
        axiskeys = label_slot.meta.getAxisKeys()
        super().__init__(axiskeys=axiskeys, parent=parent)
        self._nonzero_blocks_slot = nonzero_blocks_slot
        self._label_slot = label_slot
        self._block_cache: Dict[Tuple[int, ...], Block] = {}
        self._neighborhood = (
            Neighborhood.SINGLE if getattr(self._label_slot.meta, "is_blocked_cache", False) else Neighborhood.NONE
        )

        self._setupUi()

        self.add_unsubscribe_fn(label_slot.notifyDirty(self.update_table))

    def _clear_blocking(self):
        self._block_cache = {}

    def initialize_table(self):
        """
        Do a full recalculation of annotations from the connected label cache slot
        """
        if self._table_initialized:
            return

        self._clear_blocking()

        non_zero_slicings: List[Tuple[slice, ...]] = self._nonzero_blocks_slot.value
        self.populate_table(non_zero_slicings)
        self._table_initialized = True
        self.resize_columns_to_contents()

    def update_table(self, slot, roi, **kwargs):
        """
        Request updated label blocks and recalculate connected labels

        as reaction to dirty notification from output slot.
        """
        if self._neighborhood is Neighborhood.NONE:
            self._clear_blocking()
            non_zero_slicings: List[Tuple[slice, ...]] = self._nonzero_blocks_slot.value
            self.populate_table(non_zero_slicings)
        else:
            blockShape = self._label_slot.meta.ideal_blockshape
            block_starts = getIntersectingBlocks(blockshape=blockShape, roi=(roi.start, roi.stop))
            block_rois = [(bl, bl + blockShape) for bl in block_starts]
            block_slicings = [roiToSlice(*br) for br in block_rois]
            self.populate_table(block_slicings)

    def _update_blocks(self, block_slicings):
        """Request data from label slot and save them in `self._block_cache`"""

        def extract_single(roi):
            labels_data = vigra.taggedView(self._label_slot[roi].wait(), "".join(self._axiskeys))

            spatial_axes = [SpatialAxesKeys(x) for x in self._axiskeys if x in SPATIAL_AXES]

            labels_data = labels_data.withAxes("".join(spatial_axes))
            block_regions = extract_annotations(labels_data)

            block = Block(
                axistags="".join(self._axiskeys), slices=roi, regions=block_regions, neighborhood=self._neighborhood
            )

            if block_regions:
                self._block_cache[block.block_start] = block
            else:
                if block.block_start in self._block_cache:
                    del self._block_cache[block.block_start]

        # only go through the overhead of a requestpool if there are many blocks to request
        if len(block_slicings) > 1:
            pool = RequestPool()
            for roi in block_slicings:
                pool.add(Request(partial(extract_single, roi)))

            pool.wait()
            pool.clean()
        elif len(block_slicings) == 1:
            extract_single(block_slicings[0])

    @timeLogged(logger, logging.INFO, "_populate_table")
    def _populate_table(self, block_slicings):
        self._update_blocks(block_slicings)
        self._regions_dict = connect_regions(self._block_cache)
        annotation_anchors: list[AnnotationAnchor] = []
        for k, v in self._regions_dict.items():
            if k == v:
                annotation_anchors.append(AnnotationAnchor(label=k.label, position=k.tagged_pixel_anchor))
        return annotation_anchors
