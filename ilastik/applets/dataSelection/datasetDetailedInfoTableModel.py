import os

from PyQt4.QtCore import Qt, QAbstractItemModel, QModelIndex

from ilastik.utility import bind, PathComponents
from opDataSelection import DatasetInfo

class DatasetDetailedInfoColumn():
    Nickname = 0
    Location = 1
    InternalID = 2
    AxisOrder = 3
    Shape = 4
    Range = 5
    NumColumns = 6

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

            def handleDatasetInfoChanged(slot):
                # Get the row of this slot
                laneSlot = slot.operator
                if laneSlot is None or laneSlot.operator is None: # This can happen during disconnect
                    return
                laneIndex = laneSlot.operator.index( laneSlot )
                firstIndex = self.createIndex(laneIndex, 0)
                lastIndex = self.createIndex(laneIndex, self.columnCount()-1)
                self.dataChanged.emit(firstIndex, lastIndex)
            
            def handleNewDatasetInserted(slot, index):
                if index == self._roleIndex:
                    datasetMultiSlot[self._roleIndex].notifyDirty( bind(handleDatasetInfoChanged) )
                    datasetMultiSlot[self._roleIndex].notifyDisconnect( bind(handleDatasetInfoChanged) )

            for laneIndex, datasetMultiSlot in enumerate( self._op.DatasetGroup ):
                datasetMultiSlot.notifyInserted( bind(handleNewDatasetInserted) )
                if self._roleIndex < len(datasetMultiSlot):
                    handleNewDatasetInserted(datasetMultiSlot, self._roleIndex)

        self._op.DatasetGroup.notifyInserted( bind(handleNewLane) )

        def handleLaneRemoved( multislot, laneIndex ):
            assert multislot is self._op.DatasetGroup
            self.beginRemoveRows( QModelIndex(), laneIndex, laneIndex )
            self.endRemoveRows()
        self._op.DatasetGroup.notifyRemoved( bind(handleLaneRemoved) )

        # Any lanes that already exist must be added now.        
        for laneIndex, slot in enumerate(self._op.DatasetGroup):
            handleNewLane( self._op.DatasetGroup, laneIndex )

    def isEditable(self, row):
        return self._op.DatasetGroup[row][self._roleIndex].ready()

    def hasInternalPaths(self):
        for mslot in self._op.DatasetGroup:
            if self._roleIndex < len(mslot):
                slot = mslot[self._roleIndex]
                if slot.ready():
                    datasetInfo = slot.value
                    filePathComponents = PathComponents(datasetInfo.filePath)
                    if ( datasetInfo.location == DatasetInfo.Location.FileSystem
                         and filePathComponents.internalPath is not None ):
                        return True
        return False                
    
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
        if  role != Qt.DisplayRole:
            return None

        if orientation == Qt.Horizontal:
            InfoColumnNames = { DatasetDetailedInfoColumn.Nickname : "Nickname",
                                DatasetDetailedInfoColumn.Location : "Location",
                                DatasetDetailedInfoColumn.InternalID : "Internal Path",
                                DatasetDetailedInfoColumn.AxisOrder : "Axes",
                                DatasetDetailedInfoColumn.Shape : "Shape",
                                DatasetDetailedInfoColumn.Range : "Data Range" }
            return InfoColumnNames[section]
        elif orientation == Qt.Vertical:
            return section+1
            
    def _getDisplayRoleData(self, index):
        laneIndex = index.row()

        UninitializedDisplayData = { DatasetDetailedInfoColumn.Nickname : "<empty>",
                                     DatasetDetailedInfoColumn.Location : "",
                                     DatasetDetailedInfoColumn.InternalID : "",
                                     DatasetDetailedInfoColumn.AxisOrder : "",
                                     DatasetDetailedInfoColumn.Shape : "",
                                     DatasetDetailedInfoColumn.Range : "" }

        datasetSlot = self._op.DatasetGroup[laneIndex][self._roleIndex]

        # Default
        if not datasetSlot.ready():
            return UninitializedDisplayData[ index.column() ]
        
        datasetInfo = self._op.DatasetGroup[laneIndex][self._roleIndex].value
        filePathComponents = PathComponents( datasetInfo.filePath )

        ## Input meta-data fields

        # Name
        if index.column() == DatasetDetailedInfoColumn.Nickname:
            return datasetInfo.nickname

        # Location
        if index.column() == DatasetDetailedInfoColumn.Location:
            if datasetInfo.location == DatasetInfo.Location.FileSystem:
                if os.path.isabs(datasetInfo.filePath):
                    return "Absolute Link: {}".format( filePathComponents.externalPath )
                else:
                    return "Relative Link: {}".format( filePathComponents.externalPath )
            else:
                return "Project File"

        # Internal ID        
        if index.column() == DatasetDetailedInfoColumn.InternalID:
            if datasetInfo.location == DatasetInfo.Location.FileSystem:
                return filePathComponents.internalPath
            return ""

        ## Output meta-data fields
        
        # Defaults        
        imageSlot = self._op.ImageGroup[laneIndex][self._roleIndex]
        if not imageSlot.ready():
            return UninitializedDisplayData[index.column()]

        # Axis order            
        if index.column() == DatasetDetailedInfoColumn.AxisOrder:
            original_axistags = imageSlot.meta.original_axistags
            axistags = imageSlot.meta.axistags
            if original_axistags is not None:
                return "".join( tag.key for tag in original_axistags )            
            if axistags is not None:
                return "".join( imageSlot.meta.getAxisKeys() )
            return ""

        # Shape
        if index.column() == DatasetDetailedInfoColumn.Shape:
            original_shape = imageSlot.meta.original_shape
            shape = imageSlot.meta.shape
            if original_shape is not None:
                return str(original_shape)
            if shape is None:
                return ""
            return str(shape)

        # Range
        if index.column() == DatasetDetailedInfoColumn.Range:
            drange = imageSlot.meta.drange
            if drange is None:
                return ""
            return str(drange)

        assert False, "Unknown column: row={}, column={}".format( index.row(), index.column() )






























