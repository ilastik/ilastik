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

        self._supports_images=True
        self._supports_stack=True


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
        go.db
        super( DataLaneSummaryTableView, self ).setModel(model)

        roleIndex = 0
        for column in range( LaneColumn.NumColumns, model.columnCount(), DatasetInfoColumn.NumColumns ):
            button = AddFileButton(self, new=True, supports_images=self._supports_images,
                                   supports_stack=self._supports_stack)
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

    def setCapabilities(self, supports_images, supports_stack):

        self._supports_images=supports_images
        self._supports_stack=supports_stack

