from PyQt4.QtCore import pyqtSignal, Qt
from PyQt4.QtGui import QTableView, QHeaderView, QMenu

from datasetDetailedInfoTableModel import DatasetDetailedInfoTableModel, DatasetDetailedInfoColumn

class DatasetDetailedInfoTableView(QTableView):
    dataLaneSelected = pyqtSignal(int) # Signature: (laneIndex)
    editRequested = pyqtSignal(int) # Signature: (laneIndex)

    def __init__(self, parent):
        super( DatasetDetailedInfoTableView, self ).__init__(parent)

        self.setContextMenuPolicy( Qt.CustomContextMenu )
        self.customContextMenuRequested.connect( self.handleCustomContextMenuRequested )

        self.resizeRowsToContents()
        self.resizeColumnsToContents()
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        self.horizontalHeader().setResizeMode(DatasetDetailedInfoColumn.Name, QHeaderView.Interactive)
        self.horizontalHeader().setResizeMode(DatasetDetailedInfoColumn.Location, QHeaderView.Interactive)
        self.horizontalHeader().setResizeMode(DatasetDetailedInfoColumn.InternalID, QHeaderView.Interactive)
        self.horizontalHeader().setResizeMode(DatasetDetailedInfoColumn.AxisOrder, QHeaderView.Interactive)
#
#        self.horizontalHeader().resizeSection(Column.Name, 200)
#        self.horizontalHeader().resizeSection(Column.Location, 300)
#        self.horizontalHeader().resizeSection(Column.InternalID, 200)
#
#        if self.guiMode == GuiMode.Batch:
#            # It doesn't make sense to provide a labeling option in batch mode
#            self.removeColumn( Column.LabelsAllowed )
#            self.horizontalHeader().resizeSection(Column.LabelsAllowed, 150)
#            self.horizontalHeader().setResizeMode(Column.LabelsAllowed, QHeaderView.Fixed)

        self.verticalHeader().hide()

    def selectionChanged(self, selected, deselected):
        super( DatasetDetailedInfoTableView, self ).selectionChanged(selected, deselected)
        # Get the selected row and corresponding slot value
        selectedIndexes = selected.indexes()
        if len(selectedIndexes) == 0:
            #self.update()
            self._selectedLane = -1
            self.dataLaneSelected.emit(-1)
            return
        self._selectedLane = selectedIndexes[0].row()
        self.dataLaneSelected.emit(self._selectedLane)
        
    def selectedLane(self):
        return self._selectedLane
    
    def handleCustomContextMenuRequested(self, pos):
        col = self.columnAt( pos.x() )
        row = self.rowAt( pos.y() )

        if col < self.model().columnCount() and row < self.model().rowCount():
            menu = QMenu(parent=self)
            menu.addAction( "Replace with file..." )
            menu.addAction( "Replace with stack import..." )
            menu.addAction( "Edit properties..." )
    
            globalPos = self.mapToGlobal( pos )
            selection = menu.exec_( globalPos )
            if selection is not None:
                print "Selection was: ", selection.text()
    


