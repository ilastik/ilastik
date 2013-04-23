from PyQt4.QtCore import pyqtSignal, Qt
from PyQt4.QtGui import QTableView, QHeaderView, QMenu, QAction

from datasetDetailedInfoTableModel import DatasetDetailedInfoTableModel, DatasetDetailedInfoColumn

class DatasetDetailedInfoTableView(QTableView):
    dataLaneSelected = pyqtSignal(object) # Signature: (laneIndex)

    replaceWithFileRequested = pyqtSignal(int) # Signature: (laneIndex)
    replaceWithStackRequested = pyqtSignal(int) # Signature: (laneIndex)
    editRequested = pyqtSignal(object) # Signature: (lane_index_list)
    resetRequested = pyqtSignal(object) # Signature: (lane_index_list)

    def __init__(self, parent):
        super( DatasetDetailedInfoTableView, self ).__init__(parent)

        self._selectedLanes = []
        self.setContextMenuPolicy( Qt.CustomContextMenu )
        self.customContextMenuRequested.connect( self.handleCustomContextMenuRequested )

        self.resizeRowsToContents()
        self.resizeColumnsToContents()
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        self.horizontalHeader().setResizeMode(DatasetDetailedInfoColumn.Nickname, QHeaderView.Interactive)
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
        
        self.setSelectionBehavior( QTableView.SelectRows )
        
        self.setAcceptDrops(True)

    def selectionChanged(self, selected, deselected):
        super( DatasetDetailedInfoTableView, self ).selectionChanged(selected, deselected)
        # Get the selected row and corresponding slot value
        selectedIndexes = self.selectedIndexes()
        if len(selectedIndexes) == 0:
            self._selectedLanes = []
            self.dataLaneSelected.emit(self._selectedLanes)
            return
        rows = set()
        for index in selectedIndexes:
            rows.add(index.row())
        self._selectedLanes = sorted(rows)
        self.dataLaneSelected.emit(self._selectedLanes)
        
    def selectedLanes(self):
        return self._selectedLanes
    
    def handleCustomContextMenuRequested(self, pos):
        col = self.columnAt( pos.x() )
        row = self.rowAt( pos.y() )

        if col < self.model().columnCount() and row < self.model().rowCount():
            menu = QMenu(parent=self)
            editSharedPropertiesAction = QAction( "Edit shared properties...", menu )
            editPropertiesAction = QAction( "Edit properties...", menu )
            replaceWithFileAction = QAction( "Replace with file...", menu )
            replaceWithStackAction = QAction( "Replace with stack...", menu )
            resetSelectedAction = QAction( "Reset", menu )

            if row in self._selectedLanes and len(self._selectedLanes) > 1:
                editable = True
                for lane in self._selectedLanes:
                    editable &= self.model().isEditable(lane)

                # Show the multi-lane menu, which allows for editing but not replacing
                menu.addAction( editSharedPropertiesAction )
                editSharedPropertiesAction.setEnabled(editable)
                menu.addAction( resetSelectedAction )
            else:
                menu.addAction( editPropertiesAction )
                editPropertiesAction.setEnabled(self.model().isEditable(row))
                menu.addAction( replaceWithFileAction )
                menu.addAction( replaceWithStackAction )
                menu.addAction( resetSelectedAction )
    
            globalPos = self.mapToGlobal( pos )
            selection = menu.exec_( globalPos )
            if selection is None:
                return
            if selection is editSharedPropertiesAction:
                self.editRequested.emit( self._selectedLanes )
            if selection is editPropertiesAction:
                self.editRequested.emit( [row] )
            if selection is replaceWithFileAction:
                self.replaceWithFileRequested.emit( row )
            if selection is replaceWithStackAction:
                self.replaceWithStackRequested.emit( row )
            if selection is resetSelectedAction:
                self.resetRequested.emit( self._selectedLanes )

    def dragEnterEvent(self, event):
        print "Accepting drag event"
        # FIXME: This accepts everything, regardless of the event
        event.acceptProposedAction()
        #super( DatasetDetailedInfoTableView, self ).dragEnterEvent(event)
        
    def dragMoveEvent(self, event):
        pass

    def dropEvent(self, dropEvent):
        print "Got a drop event."
        print "hasText(): {}".format( dropEvent.mimeData().hasText() )
        print "text(): {}".format( dropEvent.mimeData().text() )
        print "hasUrls(): {}".format( dropEvent.mimeData().hasText() )
        print "urls(): {}".format( dropEvent.mimeData().text() )
        #super( DatasetDetailedInfoTableView, self ).dropEvent(dropEvent)
         