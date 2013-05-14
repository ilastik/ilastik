from PyQt4.QtCore import Qt, QAbstractItemModel, QModelIndex

from ilastik.utility import bind, PathComponents
from opDataSelection import DatasetInfo

class LaneColumn():
    LabelsAllowed = 0
    NumColumns = 1

class DatasetInfoColumn():
    Name = 0
    NumColumns = 1

class DataLaneSummaryTableModel(QAbstractItemModel):
    
    def __init__(self, parent, topLevelOperator):
        """
        :param topLevelOperator: An instance of OpMultiLaneDataSelectionGroup
        """
        super( DataLaneSummaryTableModel, self ).__init__(parent)
        self._op = topLevelOperator

        def handleNewLane( multislot, laneIndex):
            assert multislot is self._op.DatasetGroup
            self.beginInsertRows( QModelIndex(), laneIndex, laneIndex )
            self.endInsertRows()

            def handleDatasetInfoChanged(slot):
                # Get the row of this slot
                laneSlot = slot.operator
                laneIndex = laneSlot.operator.index( laneSlot )
                # FIXME: For now, we update the whole row.
                #        Later, update only the columns that correspond to this dataset.
                firstIndex = self.createIndex(laneIndex, 0)
                lastIndex = self.createIndex(laneIndex, self.columnCount()-1)
                self.dataChanged.emit(firstIndex, lastIndex)

            def handleNewDatasetInserted(mslot, index):
                mslot[index].notifyDirty( bind(handleDatasetInfoChanged) )
            
            for laneIndex, datasetMultiSlot in enumerate(self._op.DatasetGroup):
                datasetMultiSlot.notifyInserted( bind(handleNewDatasetInserted) )
                for roleIndex, datasetSlot in enumerate(datasetMultiSlot):
                    handleNewDatasetInserted( datasetMultiSlot, roleIndex )

        self._op.DatasetGroup.notifyInserted( bind(handleNewLane) )

        def handleLaneRemoved( multislot, laneIndex ):
            assert multislot is self._op.DatasetGroup
            self.beginRemoveRows( QModelIndex(), laneIndex, laneIndex )
            self.endRemoveRows()
        self._op.DatasetGroup.notifyRemoved( bind(handleLaneRemoved) )

        # Any lanes that already exist must be added now.        
        for laneIndex, slot in enumerate(self._op.DatasetGroup):
            handleNewLane( self._op.DatasetGroup, laneIndex )

    def columnCount(self, parent=QModelIndex()):
        if not self._op.DatasetRoles.ready():
            return 0
        roles = self._op.DatasetRoles.value
        return LaneColumn.NumColumns + DatasetInfoColumn.NumColumns * len(roles)
    
    def rowCount(self, parent=QModelIndex()):
        return len( self._op.ImageGroup ) + 1 # Add a row of buttons...
    
    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return self._getDisplayRoleData(index)
    
    def index(self, row, column, parent=QModelIndex()):
        return self.createIndex( row, column, object=None )
    
    def parent(self, index):
        return QModelIndex()
    
    def headerData(self, section, orientation, role=Qt.DisplayRole ):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Vertical:
            if section == self.rowCount()-1:
                return ""
            return section+1
        if section == LaneColumn.LabelsAllowed:
            return "Labelable"
        infoColumn = section - LaneColumn.NumColumns
        roleIndex = infoColumn // DatasetInfoColumn.NumColumns
        infoColumn %= LaneColumn.NumColumns
        if infoColumn == DatasetInfoColumn.Name:
            if self._op.DatasetRoles.ready():
                return self._op.DatasetRoles.value[roleIndex]
            return ""
        assert False, "Unknown header column: {}".format( section )
            
    def _getDisplayRoleData(self, index):
        # Last row is just buttons
        if index.row() >= self.rowCount()-1:
            return ""

        laneIndex = index.row()
        
        if index.column() < LaneColumn.NumColumns:
            if index.column() == LaneColumn.LabelsAllowed:
                firstInfoSlot = self._op.DatasetGroup[laneIndex][0]
                if not firstInfoSlot.ready():
                    return ""
                info = firstInfoSlot.value
                return { True: "True", False : "False" }[ info.allowLabels ]
            else:
                assert False

        ## Dataset info item
        roleIndex = (index.column() - LaneColumn.NumColumns) // DatasetInfoColumn.NumColumns
        datasetInfoIndex = (index.column() - LaneColumn.NumColumns) % DatasetInfoColumn.NumColumns
        
        datasetSlot = self._op.DatasetGroup[laneIndex][roleIndex]
        if not datasetSlot.ready():
            return ""

        UninitializedDisplayData = { DatasetInfoColumn.Name : "<please select>" }
        
        datasetSlot = self._op.DatasetGroup[laneIndex][roleIndex]
        if datasetSlot.ready():
            datasetInfo = self._op.DatasetGroup[laneIndex][roleIndex].value
        else:
            return UninitializedDisplayData[ datasetInfoIndex ]
        
        if datasetInfoIndex == DatasetInfoColumn.Name:
            if datasetInfo.nickname is not None and datasetInfo.nickname != "":
                return datasetInfo.nickname
            return PathComponents( datasetInfo.filePath ).filename

        if datasetInfoIndex == DatasetInfoColumn.Location:
            LocationNames = { DatasetInfo.Location.FileSystem : "External File",
                              DatasetInfo.Location.ProjectInternal : "Project File" }
            return LocationNames[ datasetInfo.location ]

        assert False, "Unknown column"


