from __future__ import absolute_import
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
#		   http://ilastik.org/license.html
###############################################################################
import os

from PyQt5.QtCore import Qt, QAbstractItemModel, QModelIndex

from lazyflow.utility import PathComponents, isUrl
from ilastik.utility import bind
from ilastik.utility.gui import ThreadRouter, threadRouted
from .opDataSelection import DatasetInfo

from .dataLaneSummaryTableModel import rowOfButtonsProxy

class DatasetDetailedInfoColumn(object):
    Nickname = 0
    Location = 1
    InternalID = 2
    AxisOrder = 3
    Shape = 4
    Range = 5
    NumColumns = 6

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

        self._op.DatasetGroup.notifyInsert( self.prepareForNewLane )  # pre
        self._op.DatasetGroup.notifyInserted( self.handleNewLane )    # post

        self._op.DatasetGroup.notifyRemove( self.handleLaneRemove )   # pre
        self._op.DatasetGroup.notifyRemoved( self.handleLaneRemoved ) # post

        # Any lanes that already exist must be added now.        
        for laneIndex, slot in enumerate(self._op.DatasetGroup):
            self.prepareForNewLane( self._op.DatasetGroup, laneIndex )
            self.handleNewLane( self._op.DatasetGroup, laneIndex )

    @threadRouted
    def prepareForNewLane(self, multislot, laneIndex, *args):
        assert multislot is self._op.DatasetGroup
        self.beginInsertRows( QModelIndex(), laneIndex, laneIndex )
        self._currently_inserting = True            

    @threadRouted
    def handleNewLane(self, multislot, laneIndex, *args):
        assert multislot is self._op.DatasetGroup
        self.endInsertRows()
        self._currently_inserting = False

        for laneIndex, datasetMultiSlot in enumerate( self._op.DatasetGroup ):
            datasetMultiSlot.notifyInserted( bind(self.handleNewDatasetInserted) )
            if self._roleIndex < len(datasetMultiSlot):
                self.handleNewDatasetInserted(datasetMultiSlot, self._roleIndex)
    
    @threadRouted
    def handleLaneRemove( self, multislot, laneIndex, *args ):
        assert multislot is self._op.DatasetGroup
        self.beginRemoveRows( QModelIndex(), laneIndex, laneIndex )
        self._currently_removing = True

    @threadRouted
    def handleLaneRemoved( self, multislot, laneIndex, *args ):
        assert multislot is self._op.DatasetGroup
        self.endRemoveRows()
        self._currently_removing = False

    @threadRouted
    def handleDatasetInfoChanged(self, slot):
        # Get the row of this slot
        laneSlot = slot.operator
        if laneSlot is None or laneSlot.operator is None: # This can happen during disconnect
            return
        try:
            laneIndex = laneSlot.operator.index( laneSlot )
        except ValueError:
            # If the slot doesn't exist in the lane, 
            #  then this dataset is in the process of being removed.
            return
        firstIndex = self.createIndex(laneIndex, 0)
        lastIndex = self.createIndex(laneIndex, self.columnCount()-1)
        self.dataChanged.emit(firstIndex, lastIndex)
    
    @threadRouted
    def handleNewDatasetInserted(self, slot, index):
        if index == self._roleIndex:
            slot[self._roleIndex].notifyDirty( bind(self.handleDatasetInfoChanged) )
            slot[self._roleIndex].notifyDisconnect( bind(self.handleDatasetInfoChanged) )

    def isEditable(self, row):
        return self._op.DatasetGroup[row][self._roleIndex].ready()

    def getNumRoles(self):
        # Return the number of possible roles in the workflow
        if self._op.DatasetRoles.ready():
            return len(self._op.DatasetRoles.value)
        return 0

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
        return len( self._op.DatasetGroup )
    
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

    def isEmptyRow(self, index):
        return not self._op.DatasetGroup[index][self._roleIndex].ready()
            
    def _getDisplayRoleData(self, index):
        laneIndex = index.row()

        UninitializedDisplayData = { DatasetDetailedInfoColumn.Nickname : "<empty>",
                                     DatasetDetailedInfoColumn.Location : "",
                                     DatasetDetailedInfoColumn.InternalID : "",
                                     DatasetDetailedInfoColumn.AxisOrder : "",
                                     DatasetDetailedInfoColumn.Shape : "",
                                     DatasetDetailedInfoColumn.Range : "" }

        if len( self._op.DatasetGroup ) <= laneIndex \
        or len( self._op.DatasetGroup[laneIndex] ) <= self._roleIndex:
            return UninitializedDisplayData[ index.column() ]

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
                if isUrl(datasetInfo.filePath) or os.path.isabs(datasetInfo.filePath):
                    text = "Absolute Link: {}".format( filePathComponents.externalPath )
                    return text
                else:
                    text = "Relative Link: {}".format( filePathComponents.externalPath )
                    return text
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
            if imageSlot.meta.original_axistags is not None:
                return "".join( imageSlot.meta.getOriginalAxisKeys() )
                assert imageSlot.meta.original_shape is not None, \
                    'if original axistags are available, original shape has to exist as well'

            if imageSlot.meta.axistags is not None:
                return "".join( imageSlot.meta.getAxisKeys() )
            return ""

        # Shape
        if index.column() == DatasetDetailedInfoColumn.Shape:
            original_shape = imageSlot.meta.original_shape
            if original_shape is not None:
                assert imageSlot.meta.original_axistags is not None, \
                    'if original shape is available, original axistags have to exist as well'
                return str(original_shape)
            shape = imageSlot.meta.shape
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






























