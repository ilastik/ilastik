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
from functools import partial
from PyQt4.QtCore import pyqtSignal, Qt
from PyQt4.QtGui import QTableView, QHeaderView, QItemSelection, QItemSelectionModel, QMenu, QPushButton, QAction

from dataLaneSummaryTableModel import DataLaneSummaryTableModel, LaneColumn, DatasetInfoColumn
from addFileButton import AddFileButton

class DataLaneSummaryTableView(QTableView):
    dataLaneSelected = pyqtSignal(int) # Signature: (laneIndex)
    
    addFilesRequested = pyqtSignal(int) # Signature: (roleIndex)
    addStackRequested = pyqtSignal(int) # Signature: (roleIndex)
    
    removeLanesRequested = pyqtSignal(object) # Signature: (laneIndexes)

    def __init__(self, parent):
        super( DataLaneSummaryTableView, self ).__init__(parent)

        self._selectedLanes = []
        self.resizeRowsToContents()
        self.resizeColumnsToContents()
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)

        self.setSelectionBehavior( QTableView.SelectRows )
        self.setContextMenuPolicy( Qt.CustomContextMenu )
        self.customContextMenuRequested.connect( self.handleCustomContextMenuRequested )

        self.addFilesButtons = {}

    def setModel(self, model):
        super( DataLaneSummaryTableView, self ).setModel(model)

        roleIndex = 0
        for column in range( LaneColumn.NumColumns, model.columnCount(), DatasetInfoColumn.NumColumns ):
            button = AddFileButton(self, new=True)
            button.addFilesRequested.connect(
                    partial(self.addFilesRequested.emit, roleIndex))
            button.addStackRequested.connect(
                    partial(self.addStackRequested.emit, roleIndex))
            self.addFilesButtons[roleIndex] = button

            lastRow = self.model().rowCount()-1
            modelIndex = self.model().index( lastRow, column )
            self.setIndexWidget( modelIndex, button )
            
            roleIndex += 1

        # TODO: Implement support for the labelable flag again...
        self.setColumnHidden(LaneColumn.LabelsAllowed, True)
        self.resizeColumnsToContents()
    
    def selectionChanged(self, selected, deselected):
        super( DataLaneSummaryTableView, self ).selectionChanged(selected, deselected)
        # Get the selected row and corresponding slot value
        selectedIndexes = self.selectedIndexes()
        rows = set()
        for index in selectedIndexes:
            rows.add(index.row())
        rows.discard( self.model().rowCount()-1 )
        self._selectedLanes = sorted(rows)
        if len(self._selectedLanes) > 0:
            self.dataLaneSelected.emit( self._selectedLanes[0] )
        
    def selectedLane(self):
        return self._selectedLane

    def handleCustomContextMenuRequested(self, pos):
        col = self.columnAt( pos.x() )
        row = self.rowAt( pos.y() )

        if col < self.model().columnCount() and \
                row < self.model().rowCount() - 1: # last row has buttons
            menu = QMenu(parent=self)
            removeLanesAction = QAction( "Remove", menu )
            menu.addAction( removeLanesAction )
    
            globalPos = self.viewport().mapToGlobal( pos )
            selection = menu.exec_( globalPos )
            if selection is removeLanesAction:
                self.removeLanesRequested.emit( self._selectedLanes )


