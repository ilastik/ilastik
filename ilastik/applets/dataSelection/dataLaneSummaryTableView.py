from PyQt4.QtCore import pyqtSignal, Qt
from PyQt4.QtGui import QTableView, QHeaderView, QItemSelection, QItemSelectionModel, QMenu

from dataLaneSummaryTableModel import DataLaneSummaryTableModel, LaneColumn, DatasetInfoColumn

class DataLaneSummaryTableView(QTableView):
    dataLaneSelected = pyqtSignal(int) # Signature: (laneIndex)

    def __init__(self, parent):
        super( DataLaneSummaryTableView, self ).__init__(parent)

        self.resizeRowsToContents()
        self.resizeColumnsToContents()
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)


#        self.horizontalHeader().setResizeMode(DatasetInfoColumn.Name, QHeaderView.Interactive)
#        self.horizontalHeader().setResizeMode(DatasetInfoColumn.Location, QHeaderView.Interactive)
#        self.horizontalHeader().setResizeMode(DatasetInfoColumn.InternalID, QHeaderView.Interactive)
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
        super( DataLaneSummaryTableView, self ).selectionChanged(selected, deselected)
        # Get the selected row and corresponding slot value
        selectedIndexes = selected.indexes()
        if len(selectedIndexes) == 0:
            self.update()
            self._selectedLane = -1
            self.dataLaneSelected.emit(-1)
            return

        rowFirstIndex = self.model().index( selectedIndexes[0].row(), 0, selectedIndexes[0].parent() )
        rowLastIndex = self.model().index( selectedIndexes[0].row(), self.model().columnCount(), selectedIndexes[0].parent() )
        selection = QItemSelection( rowFirstIndex, rowLastIndex )
        self.selectionModel().select( selection, QItemSelectionModel.Select )

        self._selectedLane = selectedIndexes[0].row()
        self.dataLaneSelected.emit(self._selectedLane)

        # For some reason, changing the selection doesn't automatically trigger a paint event
        self.update()
        
    def selectedLane(self):
        return self._selectedLane








