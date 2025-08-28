###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2025, the ilastik developers
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
# 		   http://ilastik.org/license.html
###############################################################################
from collections import OrderedDict
from functools import reduce
from typing import Dict, List

from qtpy.QtCore import Qt, QAbstractItemModel, QModelIndex
from ilastik.utility import bind
from ilastik.utility.gui import ThreadRouter, threadRouted
from lazyflow.utility.helpers import bigintprod
from lazyflow.utility.io_util.multiscaleStore import Multiscales
from .opDataSelection import DatasetInfo, eq_shapes
from .dataLaneSummaryTableModel import rowOfButtonsProxy


class DatasetColumn:
    Nickname = 0
    Location = 1
    InternalID = 2
    TaggedShape = 3
    Scale = 4
    Range = 5
    NumColumns = 6


def _dims_to_display_string(dimensions: Dict[str, int], axiskeys: str, dtype: type) -> str:
    """Generate labels to put into the scale combobox / to display in the table.
    XYZ dimensions will be reordered to match axiskeys."""
    reordered_dimensions = [dimensions[axis] for axis in axiskeys if axis in "xyz"]
    shape_string = " / ".join(str(size) for size in reordered_dimensions)
    scale_file_size = bigintprod(reordered_dimensions) * dtype().nbytes
    size_labels = {1e15: "PB", 1e12: "TB", 1e9: "GB", 1e6: "MB", 1e3: "KB", 1: "B"}
    size_factor = [f for f in size_labels.keys() if scale_file_size >= f][0]
    size_string = f"{scale_file_size / size_factor:.1f} {size_labels[size_factor]}"
    return f"{size_string} ({shape_string})"


@rowOfButtonsProxy
class DatasetDetailedInfoTableModel(QAbstractItemModel):
    def __init__(self, parent, topLevelOperator, roleIndex):
        """
        :param topLevelOperator: An instance of OpMultiLaneDataSelectionGroup
        """
        # super does not work here in Python 2.x, decorated class confuses it
        QAbstractItemModel.__init__(self, parent)
        self.threadRouter = ThreadRouter(self)

        self._op = topLevelOperator
        self._roleIndex = roleIndex
        self._currently_inserting = False
        self._currently_removing = False

        self._op.DatasetGroupOut.notifyInsert(self.prepareForNewLane)  # pre
        self._op.DatasetGroupOut.notifyInserted(self.handleNewLane)  # post

        self._op.DatasetGroupOut.notifyRemove(self.handleLaneRemove)  # pre
        self._op.DatasetGroupOut.notifyRemoved(self.handleLaneRemoved)  # post

        # Any lanes that already exist must be added now.
        for laneIndex, slot in enumerate(self._op.DatasetGroupOut):
            self.prepareForNewLane(self._op.DatasetGroupOut, laneIndex)
            self.handleNewLane(self._op.DatasetGroupOut, laneIndex)

    @threadRouted
    def prepareForNewLane(self, multislot, laneIndex, *args):
        assert multislot is self._op.DatasetGroupOut
        self.beginInsertRows(QModelIndex(), laneIndex, laneIndex)
        self._currently_inserting = True

    @threadRouted
    def handleNewLane(self, multislot, laneIndex, *args):
        assert multislot is self._op.DatasetGroupOut
        self.endInsertRows()
        self._currently_inserting = False

        for laneIndex, datasetMultiSlot in enumerate(self._op.DatasetGroupOut):
            datasetMultiSlot.notifyInserted(bind(self.handleNewDatasetInserted))
            if self._roleIndex < len(datasetMultiSlot):
                self.handleNewDatasetInserted(datasetMultiSlot, self._roleIndex)

    @threadRouted
    def handleLaneRemove(self, multislot, laneIndex, *args):
        assert multislot is self._op.DatasetGroupOut
        self.beginRemoveRows(QModelIndex(), laneIndex, laneIndex)
        self._currently_removing = True

    @threadRouted
    def handleLaneRemoved(self, multislot, laneIndex, *args):
        assert multislot is self._op.DatasetGroupOut
        self.endRemoveRows()
        self._currently_removing = False

    @threadRouted
    def handleDatasetInfoChanged(self, slot):
        # Get the row of this slot
        assert slot.subindex, f"BUG: Expected nested slot {slot}"
        laneIndex = slot.subindex[0]
        firstIndex = self.createIndex(laneIndex, 0)
        lastIndex = self.createIndex(laneIndex, self.columnCount() - 1)
        self.dataChanged.emit(firstIndex, lastIndex)

    @threadRouted
    def handleNewDatasetInserted(self, slot, index):
        if index == self._roleIndex:
            slot[self._roleIndex].notifyDirty(bind(self.handleDatasetInfoChanged))
            slot[self._roleIndex].notifyDisconnect(bind(self.handleDatasetInfoChanged))

    def isEditable(self, row):
        return self._op.DatasetGroupOut[row][self._roleIndex].ready()

    def getNumRoles(self):
        # Return the number of possible roles in the workflow
        if self._op.DatasetRoles.ready():
            return len(self._op.DatasetRoles.value)
        return 0

    def columnCount(self, parent=QModelIndex()):
        return DatasetColumn.NumColumns

    def rowCount(self, parent=QModelIndex()):
        return len(self._op.DatasetGroupOut)

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole or role == Qt.ToolTipRole:
            return self._getDisplayRoleData(index)

    def flags(self, index):
        if index.column() == DatasetColumn.Scale:
            return super().flags(index) | Qt.ItemIsEditable
        return super().flags(index)

    def index(self, row, column, parent=QModelIndex()):
        return self.createIndex(row, column, object=None)

    def parent(self, index):
        return QModelIndex()

    def headerData(self, section: int, orientation: int, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None

        if orientation == Qt.Horizontal:
            InfoColumnNames = {
                DatasetColumn.Nickname: "Nickname",
                DatasetColumn.Location: "Location",
                DatasetColumn.InternalID: "Internal Path",
                DatasetColumn.TaggedShape: "Shape",
                DatasetColumn.Range: "Data Range",
                DatasetColumn.Scale: "Resolution Level",
            }
            return InfoColumnNames[section]
        elif orientation == Qt.Vertical:
            return section + 1

    def isEmptyRow(self, index):
        return not self._op.DatasetGroupOut[index][self._roleIndex].ready()

    def _getDisplayRoleData(self, index):
        laneIndex = index.row()

        UninitializedDisplayData = {
            DatasetColumn.Nickname: "",
            DatasetColumn.Location: "",
            DatasetColumn.InternalID: "",
            DatasetColumn.TaggedShape: "",
            DatasetColumn.Range: "",
            DatasetColumn.Scale: "",
        }

        if len(self._op.DatasetGroupOut) <= laneIndex or len(self._op.DatasetGroupOut[laneIndex]) <= self._roleIndex:
            return UninitializedDisplayData[index.column()]

        datasetSlot = self._op.DatasetGroupOut[laneIndex][self._roleIndex]

        # Default
        if not datasetSlot.ready():
            return UninitializedDisplayData[index.column()]

        datasetInfo: DatasetInfo = datasetSlot.value

        ## Input meta-data fields
        if index.column() == DatasetColumn.Nickname:
            return datasetInfo.nickname
        if index.column() == DatasetColumn.Location:
            return datasetInfo.display_string
        if index.column() == DatasetColumn.InternalID:
            paths = [p for p in getattr(datasetInfo, "internal_paths", []) if p is not None]
            return "\n".join(paths)

        ## Output meta-data fields
        # Defaults
        imageSlot = self._op.ImageGroup[laneIndex][self._roleIndex]
        if not imageSlot.ready():
            return UninitializedDisplayData[index.column()]

        if index.column() == DatasetColumn.TaggedShape:
            return ", ".join([f"{axis}: {size}" for axis, size in zip(datasetInfo.axiskeys, datasetInfo.laneShape)])
        if index.column() == DatasetColumn.Range:
            return str(datasetInfo.drange or "")
        if index.column() == DatasetColumn.Scale:
            if datasetInfo.scales:
                return _dims_to_display_string(
                    datasetInfo.scales[datasetInfo.working_scale], datasetInfo.axiskeys, datasetInfo.laneDtype
                )
            return UninitializedDisplayData[index.column()]

        raise NotImplementedError(f"Unknown column: row={index.row()}, column={index.column()}")

    def get_scale_options(self, laneIndex) -> OrderedDict[str, str]:
        """
        Returns { scale_key : display string }
        """
        try:
            datasetSlot = self._op.DatasetGroupOut[laneIndex][self._roleIndex]
        except IndexError:  # This can happen during "Save Project As"
            return OrderedDict()
        if not datasetSlot.ready():
            return OrderedDict()
        datasetInfo = datasetSlot.value
        if not datasetInfo.scales:
            return OrderedDict()
        # Multiscale datasets always list scales from original (largest) to most-downscaled (smallest).
        # We display them in reverse order so that the default loaded scale (the smallest)
        # is the first option in the drop-down box
        return OrderedDict(
            {
                key: _dims_to_display_string(tagged_shape, datasetInfo.axiskeys, datasetInfo.laneDtype)
                for key, tagged_shape in reversed(datasetInfo.scales.items())
            }
        )

    def get_common_scale_option_indices(self, laneIndex) -> List[int]:
        """
        Check all datasets and scales across all roles.
        Return indices of the options from `get_scale_options` that have matching scales in all other roles.
        """

        def shapes_intersection(shapes1: List[Dict[str, int]], shapes2: List[Dict[str, int]]):
            return [s1 for s1 in shapes1 if any(eq_shapes(s1, s2) for s2 in shapes2)]

        # Checking if ready etc. shouldn't be necessary here because this should only be called
        # while building the scale dropdown (by which point everything should be ready).
        scale_shapes_per_role: List[List[OrderedDict[str, int]]] = [
            (
                list(role_slot.value.scales.values())
                if role_slot.value.scales
                else [dict(zip(role_slot.value.axistags.keys(), role_slot.value.laneShape))]
            )
            for role_slot in self._op.DatasetGroupOut[laneIndex]
            if role_slot.ready()
        ]
        common_scale_shapes = reduce(shapes_intersection, scale_shapes_per_role)

        scale_options: Multiscales = self._op.DatasetGroupOut[laneIndex][self._roleIndex].value.scales
        indices_of_common_scales = []
        for i, shape in enumerate(reversed(scale_options.values())):
            if any(eq_shapes(shape, common_shape) for common_shape in common_scale_shapes):
                indices_of_common_scales.append(i)
        return indices_of_common_scales

    def is_scale_locked(self, laneIndex) -> bool:
        datasetSlot = self._op.DatasetGroupOut[laneIndex][self._roleIndex]
        if not datasetSlot.ready():
            return False
        datasetInfo = datasetSlot.value
        return datasetInfo.scale_locked
