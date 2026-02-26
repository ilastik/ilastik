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

import numpy
import numpy.typing as npt

from ilastik.applets.objectExtraction.opObjectExtraction import default_features_key
from ilastik.widgets.labelExplorer import AnnotationAnchor, LabelExplorerBase
from lazyflow.base import Axiskey
from lazyflow.slot import Slot
from lazyflow.utility.timer import timeLogged

logger = logging.getLogger(__name__)

FeatureDict = dict[str, npt.NDArray[numpy.float64]]
PluginDict = dict[str, FeatureDict]
Timepoint = int


class ObjectLabelExplorerWidget(LabelExplorerBase):
    """Label Explorer for workflows with object labels"""

    display_text = "Label Explorer"

    def __init__(
        self,
        features_slot: Slot,
        label_slot: Slot,
        axiskeys: list[Axiskey],
        parent=None,
    ):
        super().__init__(axiskeys=axiskeys, parent=parent)
        self._features_slot = features_slot
        self._label_slot = label_slot
        self._setupUi()

        self.add_unsubscribe_fn(label_slot.notifyDirty(self.populate_table))

    def initialize_table(self):
        """
        Do a full recalculation of annotations from the connected label cache slot
        """
        if self._table_initialized:
            return

        self.populate_table()
        self._table_initialized = True
        self.resize_columns_to_contents()

    @timeLogged(logger, logging.INFO, "_populate_table")
    def _populate_table(self, *_args):
        labels: dict[int, npt.NDArray[numpy.float64]] = self._label_slot.value

        labels_filtered = {}
        for timestep, labels_time in labels.items():
            nz = numpy.nonzero(labels_time)
            if len(nz[0]) == 0:
                continue
            else:
                labels_filtered[timestep] = nz[0]

        if not labels_filtered:
            return []

        feats: dict[Timepoint, PluginDict] = self._features_slot(list(labels_filtered.keys())).wait()

        labs: list[AnnotationAnchor] = []
        for timepoint, non_zero_indices in labels_filtered.items():
            for n in non_zero_indices:
                region_center = feats[timepoint][default_features_key]["RegionCenter"][n]
                if region_center.shape == (2,):
                    z = 0.0
                    x, y = region_center
                elif region_center.shape == (3,):
                    x, y, z = region_center
                else:
                    raise ValueError(f"unexpected {region_center=}")

                labs.append(
                    AnnotationAnchor(
                        position={"t": timepoint, "x": x, "y": y, "z": z}, label=int((labels[timepoint][n]))
                    )
                )

        return labs
