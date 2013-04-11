from PyQt4.QtCore import Qt, QAbstractItemModel, QModelIndex

from ilastik.utility import bind

class LaneColumn():
    LabelsAllowed = 0
    NumColumns = 1

class ImageColumn():
    Name = 0
    Location = 1
    NumColumns = 2

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
        self._op.DatasetGroup.notifyInserted( handleNewLane )

        def handleLaneRemoved( multislot, laneIndex ):
            assert multislot is self._op.DatasetGroup
            self.beginRemoveRows( QModelIndex(), laneIndex, laneIndex )
            self.endEndRemoveRows()
        self._op.DatasetGroup.notifyRemoved( handleLaneRemoved )
        
        for 

    def columnCount(self, parent=QModelIndex()):
        roles = self._op.DatasetRoles.value
        return LaneColumn.NumColumns + ImageColumn.NumColumns * len(roles)
    
    def rowCount(self, parent=QModelIndex()):
        return len( self._op.ImageGroup )
    
    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return self._getDisplayRoleData(index)
    
    def index(self, row, column, parent=QModelIndex()):
        return self.createIndex( row, column, object=None )
    
    def parent(self, index):
        return QModelIndex()
    
    def handleDatasetInfoChanged(self, slot, *args):
        """                                                                                                                                           
        Handle a change in the operator slot by signaling that the model data has changed.                                                            
        """
        # Determine which index this slot corresponds to                                                                                              
        parentSlot = slot.operator
        row = parentSlot.index( slot )

        # Update the entire row                                                                                                                       
        firstIndex = self.createIndex(row, 0, object=slot)
        lastIndex = self.createIndex(row, Column.NumColumns, object=slot)
        self.dataChanged.emit(firstIndex, lastIndex)
    
    def _getDisplayRoleData(self, index):
        slot = index.internalPointer()
        if slot.level == 1:
            if index.column() == 0:
                laneIndex = self._op.DatasetGroup.index( slot )
                firstDatasetImageNameSlot = self._op.ImageName[laneIndex]
#                if firstDatasetImageNameSlot.ready():
#                    return firstDatasetImageNameSlot.value
                return "Data Lane {}".format( laneIndex )
            else:
                return ""
        elif slot.level == 0:
            parentSlot = slot.operator
            laneIndex = self._op.DatasetGroup.index( parentSlot )
            slotIndex = slot.operator.index( slot ) # The index of the dataset within the lane's group
            
            UninitializedDisplayData = { Column.Role : self._op.DatasetRoles.value[slotIndex],
                                         Column.Name : "<please select>",
                                         Column.Location : "",
                                         Column.InternalID : "",
                                         Column.LabelsAllowed : False }
            
            datasetSlot = self._op.DatasetGroup[laneIndex][slotIndex]
            if datasetSlot.ready():
                datasetInfo = self._op.DatasetGroup[laneIndex][slotIndex].value
            else:
                return UninitializedDisplayData[ index.column() ]
            
            filePathComponents = PathComponents( datasetInfo.filePath )
            if index.column() == Column.Action:
                return None
            if index.column() == Column.Role:
                return self._op.DatasetRoles.value[slotIndex]
            
            if index.column() == Column.Name:
                if slot.ready():
                    return filePathComponents.filename
                else:
                    return "<please select>"

            if not slot.ready():
                return ""
            
            if index.column() == Column.Location:
                LocationNames = { DatasetInfo.Location.FileSystem : "External File",
                                  DatasetInfo.Location.ProjectInternal : "Project File" }
                return LocationNames[ datasetInfo.location ]
            if index.column() == Column.InternalID:
                return filePathComponents.internalPath
            if index.column() == Column.LabelsAllowed:
                return datasetInfo.allowLabels
            assert False, "Unknown column"
        assert False, "Expected slot of level 0 or 1"
        
