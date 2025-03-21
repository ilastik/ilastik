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
from functools import wraps

from PyQt5.QtCore import Qt, QAbstractItemModel, QModelIndex

from lazyflow.utility import PathComponents
from ilastik.utility import bind
from .opDataSelection import RelativeFilesystemDatasetInfo, FilesystemDatasetInfo
from .opDataSelection import PreloadedArrayDatasetInfo, ProjectInternalDatasetInfo, MultiscaleUrlDatasetInfo


class LaneColumn(object):
    NumColumns = 0


class DatasetInfoColumn(object):
    Name = 0
    NumColumns = 1


def rowOfButtonsProxy(model_cls):
    """
    Given a TableModel class, return a new class that pretends to have an
    extra row at the end. This row is used to display "Add..." buttons in
    the GUI.
    """

    @wraps(model_cls, updated=())
    class ProxyModel(model_cls):
        def __init__(self, *args, **kwds):
            super(ProxyModel, self).__init__(*args, **kwds)

        def rowCount(self, parent=QModelIndex()):
            """
            Return number of rows in the model.

            This proxy model keeps an extra row at the end for buttons.
            """
            return super(ProxyModel, self).rowCount(parent) + 1

        def headerData(self, section, orientation, role=Qt.DisplayRole):
            """
            Return header information for row/column.

            Skip vertical header for the last row, which is used for buttons.
            """
            if role == Qt.DisplayRole and orientation == Qt.Vertical:
                if section >= super(ProxyModel, self).rowCount():
                    return ""
            return super(ProxyModel, self).headerData(section, orientation, role)

        def _getDisplayRoleData(self, index):
            # Last row is just buttons
            if index.row() >= super(ProxyModel, self).rowCount():
                return ""
            return model_cls._getDisplayRoleData(self, index)

    return ProxyModel


@rowOfButtonsProxy
class DataLaneSummaryTableModel(QAbstractItemModel):
    def __init__(self, parent, topLevelOperator):
        """
        :param topLevelOperator: An instance of OpMultiLaneDataSelectionGroup
        """
        # super does not work here in Python 2.x, decorated class confuses it
        QAbstractItemModel.__init__(self, parent)
        self._op = topLevelOperator

        def handleNewLane(multislot, laneIndex):
            assert multislot is self._op.DatasetGroupOut
            self.beginInsertRows(QModelIndex(), laneIndex, laneIndex)
            self.endInsertRows()

            def handleDatasetInfoChanged(slot):
                # Get the row of this slot
                assert slot.subindex, f"BUG: Expected nested slot {slot}"
                laneIndex = slot.subindex[0]
                # FIXME: For now, we update the whole row.
                #        Later, update only the columns that correspond to this dataset.
                firstIndex = self.createIndex(laneIndex, 0)
                lastIndex = self.createIndex(laneIndex, self.columnCount() - 1)
                self.dataChanged.emit(firstIndex, lastIndex)

            def handleNewDatasetInserted(mslot, index):
                mslot[index].notifyDirty(bind(handleDatasetInfoChanged))

            for laneIndex, datasetMultiSlot in enumerate(self._op.DatasetGroupOut):
                datasetMultiSlot.notifyInserted(bind(handleNewDatasetInserted))
                for roleIndex, datasetSlot in enumerate(datasetMultiSlot):
                    handleNewDatasetInserted(datasetMultiSlot, roleIndex)

        self._op.DatasetGroupOut.notifyInserted(bind(handleNewLane))

        def handleLaneRemoved(multislot, laneIndex):
            assert multislot is self._op.DatasetGroupOut
            self.beginRemoveRows(QModelIndex(), laneIndex, laneIndex)
            self.endRemoveRows()

        self._op.DatasetGroupOut.notifyRemoved(bind(handleLaneRemoved))

        # Any lanes that already exist must be added now.
        for laneIndex, slot in enumerate(self._op.DatasetGroupOut):
            handleNewLane(self._op.DatasetGroupOut, laneIndex)

    def columnCount(self, parent=QModelIndex()):
        if not self._op.DatasetRoles.ready():
            return 0
        roles = self._op.DatasetRoles.value
        return LaneColumn.NumColumns + DatasetInfoColumn.NumColumns * len(roles)

    def rowCount(self, parent=QModelIndex()):
        return len(self._op.ImageGroup)

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return self._getDisplayRoleData(index)

    def index(self, row, column, parent=QModelIndex()):
        return self.createIndex(row, column, object=None)

    def parent(self, index):
        return QModelIndex()

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Vertical:
            return section + 1
        infoColumn = section - LaneColumn.NumColumns
        roleIndex = infoColumn // DatasetInfoColumn.NumColumns
        infoColumn %= DatasetInfoColumn.NumColumns
        if infoColumn == DatasetInfoColumn.Name:
            if self._op.DatasetRoles.ready():
                return self._op.DatasetRoles.value[roleIndex]
            return ""
        assert False, "Unknown header column: {}".format(section)

    def _getDisplayRoleData(self, index):
        laneIndex = index.row()
        ## Dataset info item
        roleIndex = (index.column() - LaneColumn.NumColumns) // DatasetInfoColumn.NumColumns
        datasetInfoIndex = (index.column() - LaneColumn.NumColumns) % DatasetInfoColumn.NumColumns

        datasetSlot = self._op.DatasetGroupOut[laneIndex][roleIndex]
        if not datasetSlot.ready():
            return ""

        UninitializedDisplayData = {DatasetInfoColumn.Name: "<please select>"}

        datasetSlot = self._op.DatasetGroupOut[laneIndex][roleIndex]
        if datasetSlot.ready():
            datasetInfo = self._op.DatasetGroupOut[laneIndex][roleIndex].value
        else:
            return UninitializedDisplayData[datasetInfoIndex]

        if datasetInfoIndex == DatasetInfoColumn.Name:
            if datasetInfo.nickname is not None and datasetInfo.nickname != "":
                return datasetInfo.nickname
            return PathComponents(datasetInfo.filePath).filename

        if datasetInfoIndex == DatasetInfoColumn.Location:
            LocationNames = {
                RelativeFilesystemDatasetInfo: "External File",
                FilesystemDatasetInfo: "External File",
                MultiscaleUrlDatasetInfo: "Multiscale Data",
                PreloadedArrayDatasetInfo: "Preloaded Array",
                ProjectInternalDatasetInfo: "Project File",
            }
            return LocationNames[datasetInfo.__class__]

        assert False, "Unknown column"
