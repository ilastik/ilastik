from functools import partial
from PyQt4.QtCore import pyqtSignal, Qt
from PyQt4.QtGui import QTableView, QHeaderView, QItemSelection, QItemSelectionModel, QMenu, QPushButton, QAction

from dataLaneSummaryTableModel import DataLaneSummaryTableModel, LaneColumn, DatasetInfoColumn

class DataLaneSummaryTableView(QTableView):
    dataLaneSelected = pyqtSignal(int) # Signature: (laneIndex)
    
    addFilesRequested = pyqtSignal(int) # Signature: (roleIndex)
    addStackRequested = pyqtSignal(int) # Signature: (roleIndex)
    addByPatternRequested = pyqtSignal(int) # Signature: (roleIndex)
    
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
        

    def setModel(self, model):
        super( DataLaneSummaryTableView, self ).setModel(model)

        self._retained = []
        roleIndex = 0
        for column in range( LaneColumn.NumColumns, model.columnCount(), DatasetInfoColumn.NumColumns ):
            menu = QMenu()
            self._retained.append(menu)
            menu.addAction( "Add File(s)..." ).triggered.connect( partial(self.addFilesRequested.emit, roleIndex) )
            menu.addAction( "Add Volume from Stack..." ).triggered.connect( partial(self.addStackRequested.emit, roleIndex) )
            menu.addAction( "Add Many by Pattern..." ).triggered.connect( partial(self.addByPatternRequested.emit, roleIndex) )
            
            button = QPushButton("Add File(s)...", self)
            button.setMenu( menu )

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

        if col < self.model().columnCount() and row < self.model().rowCount():
            menu = QMenu(parent=self)
            removeLanesAction = QAction( "Remove", menu )
            menu.addAction( removeLanesAction )
    
            globalPos = self.mapToGlobal( pos )
            selection = menu.exec_( globalPos )
            if selection is removeLanesAction:
                self.removeLanesRequested.emit( self._selectedLanes )


