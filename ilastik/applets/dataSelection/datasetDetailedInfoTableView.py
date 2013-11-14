from PyQt4.QtCore import pyqtSignal, Qt, QUrl
from PyQt4.QtGui import QTableView, QHeaderView, QMenu, QAction, QWidget, \
        QHBoxLayout

from datasetDetailedInfoTableModel import DatasetDetailedInfoColumn
from addFileButton import AddFileButton

class DatasetDetailedInfoTableView(QTableView):
    dataLaneSelected = pyqtSignal(object) # Signature: (laneIndex)

    replaceWithFileRequested = pyqtSignal(int) # Signature: (laneIndex), or (-1) to indicate "append requested"
    replaceWithStackRequested = pyqtSignal(int) # Signature: (laneIndex)
    editRequested = pyqtSignal(object) # Signature: (lane_index_list)
    resetRequested = pyqtSignal(object) # Signature: (lane_index_list)

    addFilesRequested = pyqtSignal() # Signature: ()
    addStackRequested = pyqtSignal() # Signature: (x)
    addFilesRequestedDrop = pyqtSignal(object) # Signature: ( filepath_list )

    def __init__(self, parent):
        super( DatasetDetailedInfoTableView, self ).__init__(parent)

        self.selectedLanes = []
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
        
        self.setSelectionBehavior( QTableView.SelectRows )
        
        self.setAcceptDrops(True)

    def setModel(self, model):
        """
        Set model used to store the data. This method adds an extra row
        at the end, which is used to keep the "Add..." button.
        """
        super( DatasetDetailedInfoTableView, self ).setModel(model)

        widget = QWidget()
        layout = QHBoxLayout(widget)
        self._addButton = button = AddFileButton(widget)
        button.addFilesRequested.connect(self.addFilesRequested.emit)
        button.addStackRequested.connect(self.addStackRequested.emit)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(button)
        layout.addStretch()
        widget.setLayout(layout)

        lastRow = self.model().rowCount()-1
        modelIndex = self.model().index( lastRow, 0 )
        self.setIndexWidget( modelIndex, widget )
        # the "Add..." button spans last row
        self.setSpan(lastRow, 0, 1, model.columnCount())

    def setEnabled(self, status):
        """
        Set status of the add button shown on the last row.

        If this view is used for a secondary role, such as importing
        prediction maps, the button is only available if there are more
        raw data lanes than prediction maps.
        """
        self._addButton.setEnabled(status)

    def dataChanged(self, topLeft, bottomRight):
        self.dataLaneSelected.emit( self.selectedLanes )

    def selectionChanged(self, selected, deselected):
        super( DatasetDetailedInfoTableView, self ).selectionChanged(selected, deselected)
        # Get the selected row and corresponding slot value
        selectedIndexes = self.selectedIndexes()
        
        if len(selectedIndexes) == 0:
            self.selectedLanes = []
        else:
            rows = set()
            for index in selectedIndexes:
                rows.add(index.row())
            rows.discard(self.model().rowCount() - 1) # last row is a button
            self.selectedLanes = sorted(rows)

        self.dataLaneSelected.emit(self.selectedLanes)
        
    def handleCustomContextMenuRequested(self, pos):
        col = self.columnAt( pos.x() )
        row = self.rowAt( pos.y() )
        
        if 0 <= col < self.model().columnCount() and \
                0 <= row < self.model().rowCount() - 1: # last row is a button
            menu = QMenu(parent=self)
            editSharedPropertiesAction = QAction( "Edit shared properties...", menu )
            editPropertiesAction = QAction( "Edit properties...", menu )
            replaceWithFileAction = QAction( "Replace with file...", menu )
            replaceWithStackAction = QAction( "Replace with stack...", menu )
            
            if self.model().getNumRoles() > 1:
                resetSelectedAction = QAction( "Reset", menu )
            else:
                resetSelectedAction = QAction( "Remove", menu )

            if row in self.selectedLanes and len(self.selectedLanes) > 1:
                editable = True
                for lane in self.selectedLanes:
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
    
            globalPos = self.viewport().mapToGlobal( pos )
            selection = menu.exec_( globalPos )
            if selection is None:
                return
            if selection is editSharedPropertiesAction:
                self.editRequested.emit( self.selectedLanes )
            if selection is editPropertiesAction:
                self.editRequested.emit( [row] )
            if selection is replaceWithFileAction:
                self.replaceWithFileRequested.emit( row )
            if selection is replaceWithStackAction:
                self.replaceWithStackRequested.emit( row )
            if selection is resetSelectedAction:
                self.resetRequested.emit( self.selectedLanes )

    def mouseDoubleClickEvent(self, event):
        col = self.columnAt( event.pos().x() )
        row = self.rowAt( event.pos().y() )

        # If the user double-clicked an empty table,
        #  we behave as if she clicked the "add file" button.
        if self.model().rowCount() == 0:
            # In this case -1 means "append a row"
            self.replaceWithFileRequested.emit(-1)
            return

        if not ( 0 <= col < self.model().columnCount() and 0 <= row < self.model().rowCount() ):
            return

        if self.model().isEditable(row):
            self.editRequested.emit([row])
        else:
            self.replaceWithFileRequested.emit(row)

    def dragEnterEvent(self, event):
        # Only accept drag-and-drop events that consist of urls to local files.
        if not event.mimeData().hasUrls():
            return
        urls = event.mimeData().urls()
        if all( map( QUrl.isLocalFile, urls ) ):        
            event.acceptProposedAction()
        
    def dragMoveEvent(self, event):
        # Must override this or else the QTableView base class steals dropEvents from us.
        pass

    def dropEvent(self, dropEvent):
        urls = dropEvent.mimeData().urls()
        filepaths = map( QUrl.toLocalFile, urls )
        filepaths = map( str, filepaths )
        self.addFilesRequestedDrop.emit( filepaths )




























