###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
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
from PyQt5.QtCore import Qt, QAbstractItemModel, QModelIndex
from ilastik.utility import bind
from ilastik.utility.gui import ThreadRouter, threadRouted
from .opDataSelection import DatasetInfo
from .dataLaneSummaryTableModel import rowOfButtonsProxy


class DatasetColumn:
    Nickname = 0
    Location = 1
    InternalID = 2
    AxisOrder = 3
    Shape = 4
    Scale = 5
    Range = 6
    NumColumns = 7


def _resolution_to_display_string(resolution: list[int]):
    return ", ".join(map(str, resolution))


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

        self._op.DatasetGroup.notifyInsert(self.prepareForNewLane)  # pre
        self._op.DatasetGroup.notifyInserted(self.handleNewLane)  # post

        self._op.DatasetGroup.notifyRemove(self.handleLaneRemove)  # pre
        self._op.DatasetGroup.notifyRemoved(self.handleLaneRemoved)  # post

        # Any lanes that already exist must be added now.
        for laneIndex, slot in enumerate(self._op.DatasetGroup):
            self.prepareForNewLane(self._op.DatasetGroup, laneIndex)
            self.handleNewLane(self._op.DatasetGroup, laneIndex)

    @threadRouted
    def prepareForNewLane(self, multislot, laneIndex, *args):
        assert multislot is self._op.DatasetGroup
        self.beginInsertRows(QModelIndex(), laneIndex, laneIndex)
        self._currently_inserting = True

    @threadRouted
    def handleNewLane(self, multislot, laneIndex, *args):
        assert multislot is self._op.DatasetGroup
        self.endInsertRows()
        self._currently_inserting = False

        for laneIndex, datasetMultiSlot in enumerate(self._op.DatasetGroup):
            datasetMultiSlot.notifyInserted(bind(self.handleNewDatasetInserted))
            if self._roleIndex < len(datasetMultiSlot):
                self.handleNewDatasetInserted(datasetMultiSlot, self._roleIndex)

    @threadRouted
    def handleLaneRemove(self, multislot, laneIndex, *args):
        assert multislot is self._op.DatasetGroup
        self.beginRemoveRows(QModelIndex(), laneIndex, laneIndex)
        self._currently_removing = True

    @threadRouted
    def handleLaneRemoved(self, multislot, laneIndex, *args):
        assert multislot is self._op.DatasetGroup
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
        return self._op.DatasetGroup[row][self._roleIndex].ready()

    def getNumRoles(self):
        # Return the number of possible roles in the workflow
        if self._op.DatasetRoles.ready():
            return len(self._op.DatasetRoles.value)
        return 0

    def columnCount(self, parent=QModelIndex()):
        return DatasetColumn.NumColumns

    def rowCount(self, parent=QModelIndex()):
        return len(self._op.DatasetGroup)

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
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
                DatasetColumn.AxisOrder: "Axes",
                DatasetColumn.Shape: "Shape",
                DatasetColumn.Range: "Data Range",
                DatasetColumn.Scale: "Resolution Level",
            }
            return InfoColumnNames[section]
        elif orientation == Qt.Vertical:
            return section + 1

    def isEmptyRow(self, index):
        return not self._op.DatasetGroup[index][self._roleIndex].ready()

    def _getDisplayRoleData(self, index):
        laneIndex = index.row()

        UninitializedDisplayData = {
            DatasetColumn.Nickname: "<empty>",
            DatasetColumn.Location: "",
            DatasetColumn.InternalID: "",
            DatasetColumn.AxisOrder: "",
            DatasetColumn.Shape: "",
            DatasetColumn.Range: "",
            DatasetColumn.Scale: "",
        }

        if len(self._op.DatasetGroup) <= laneIndex or len(self._op.DatasetGroup[laneIndex]) <= self._roleIndex:
            return UninitializedDisplayData[index.column()]

        datasetSlot = self._op.DatasetGroup[laneIndex][self._roleIndex]

        # Default
        if not datasetSlot.ready():
            return UninitializedDisplayData[index.column()]

        datasetInfo: DatasetInfo = datasetSlot.value

        ## Input meta-data fields
        if DatasetColumn.Nickname == index.column():
            return datasetInfo.nickname
        if DatasetColumn.Location == index.column():
            return datasetInfo.display_string
        if DatasetColumn.InternalID == index.column():
            return str(getattr(datasetInfo, "internal_paths", ""))

        ## Output meta-data fields
        # Defaults
        imageSlot = self._op.ImageGroup[laneIndex][self._roleIndex]
        if not imageSlot.ready():
            return UninitializedDisplayData[index.column()]

        if DatasetColumn.AxisOrder == index.column():
            return datasetInfo.axiskeys
        if DatasetColumn.Shape == index.column():
            return str(datasetInfo.laneShape)
        if DatasetColumn.Range == index.column():
            return str(datasetInfo.drange or "")
        if DatasetColumn.Scale == index.column():
            if datasetInfo.scales:
                return _resolution_to_display_string(datasetInfo.scales[datasetInfo.working_scale]["resolution"])
            return UninitializedDisplayData[index.column()]

        assert False, "Unknown column: row={}, column={}".format(index.row(), index.column())

    def get_scale_options(self, laneIndex) -> list[str]:
        try:
            datasetSlot = self._op.DatasetGroup[laneIndex][self._roleIndex]
        except IndexError:  # This can happen during "Save Project As"
            return []
        if not datasetSlot.ready():
            return []
        datasetInfo = datasetSlot.value
        if not datasetInfo.scales:
            return []
        return [_resolution_to_display_string(s["resolution"]) for s in datasetInfo.scales]

    def is_scale_locked(self, laneIndex) -> bool:
        datasetSlot = self._op.DatasetGroup[laneIndex][self._roleIndex]
        if not datasetSlot.ready():
            return False
        datasetInfo = datasetSlot.value
        return datasetInfo.scale_locked
