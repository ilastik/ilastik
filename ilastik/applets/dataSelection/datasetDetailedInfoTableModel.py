from PyQt4.QtCore import Qt, QAbstractItemModel, QModelIndex

from ilastik.utility import bind, PathComponents
from opDataSelection import DatasetInfo

class DatasetDetailedInfoColumn():
    Name = 0
    Location = 1
    InternalID = 2
    AxisOrder = 3
    NumColumns = 4

class DatasetDetailedInfoTableModel(QAbstractItemModel):
    def __init__(self, parent, topLevelOperator, roleIndex):
        """
        :param topLevelOperator: An instance of OpMultiLaneDataSelectionGroup
        """
        super( DatasetDetailedInfoTableModel, self ).__init__(parent)
        self._op = topLevelOperator
        self._roleIndex = roleIndex

        def handleNewLane( multislot, laneIndex):
            assert multislot is self._op.DatasetGroup
            self.beginInsertRows( QModelIndex(), laneIndex, laneIndex )
            self.endInsertRows()

            def handleDatasetInfoChanged(slot, roi):
                # Get the row of this slot
                laneSlot = slot.operator
                laneIndex = laneSlot.operator.index( laneSlot )
                firstIndex = self.createIndex(laneIndex, 0)
                lastIndex = self.createIndex(laneIndex, self.columnCount()-1)
                self.dataChanged.emit(firstIndex, lastIndex)
            
            for laneIndex, datasetMultiSlot in enumerate(self._op.DatasetGroup):
                datasetMultiSlot[self._roleIndex].notifyDirty( handleDatasetInfoChanged )

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
        return DatasetDetailedInfoColumn.NumColumns
    
    def rowCount(self, parent=QModelIndex()):
        return len( self._op.ImageGroup )
    
    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return self._getDisplayRoleData(index)
    
    def index(self, row, column, parent=QModelIndex()):
        return self.createIndex( row, column, object=None )
    
    def parent(self, index):
        return QModelIndex()
    
    def headerData(self, section, orientation, role=Qt.DisplayRole ):
        if orientation != Qt.Horizontal or role != Qt.DisplayRole:
            return None

        InfoColumnNames = { DatasetDetailedInfoColumn.Name : "Name",
                            DatasetDetailedInfoColumn.Location : "Location",
                            DatasetDetailedInfoColumn.InternalID : "Internal Path",
                            DatasetDetailedInfoColumn.AxisOrder : "Axis Order" }
        return InfoColumnNames[section]
            
    def _getDisplayRoleData(self, index):
        laneIndex = index.row()

        ## Dataset info item
        datasetSlot = self._op.DatasetGroup[laneIndex][self._roleIndex]
        if not datasetSlot.ready():
            return ""

        UninitializedDisplayData = { DatasetDetailedInfoColumn.Name : "<please select>",
                                     DatasetDetailedInfoColumn.Location : "",
                                     DatasetDetailedInfoColumn.InternalID : "",
                                     DatasetDetailedInfoColumn.AxisOrder : "" }
        
        datasetSlot = self._op.DatasetGroup[laneIndex][self._roleIndex]
        if datasetSlot.ready():
            datasetInfo = self._op.DatasetGroup[laneIndex][self._roleIndex].value
        else:
            return UninitializedDisplayData[ index.column() ]
        
        filePathComponents = PathComponents( datasetInfo.filePath )        
        if index.column() == DatasetDetailedInfoColumn.Name:
            return filePathComponents.filename

        if index.column() == DatasetDetailedInfoColumn.Location:
            LocationNames = { DatasetInfo.Location.FileSystem : "External File",
                              DatasetInfo.Location.ProjectInternal : "Project File" }
            return LocationNames[ datasetInfo.location ]
        
        if index.column() == DatasetDetailedInfoColumn.InternalID:
            return filePathComponents.internalPath
        
        imageSlot = self._op.ImageGroup[laneIndex][self._roleIndex]
        if index.column() == DatasetDetailedInfoColumn.AxisOrder:
            if imageSlot.ready():
                return "".join( imageSlot.meta.getAxisKeys() )
            else:
                return UninitializedDisplayData[DatasetDetailedInfoColumn.AxisOrder]

        assert False, "Unknown column: row={}, column={}".format( index.row(), index.column() )

