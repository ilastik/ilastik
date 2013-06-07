import os
import json
from functools import partial

import numpy

from PyQt4 import uic
from PyQt4.QtCore import Qt, pyqtSignal
from PyQt4.QtGui import QWidget, QFileDialog, QMessageBox, QTreeWidgetItem, QTableWidgetItem, QPushButton, QTableView, QHeaderView, QIcon, QProgressBar

from lazyflow.roi import TinyVector

from ilastik.shell.gui.iconMgr import ilastikIcons

# Example json file:
"""
{
    "coordinates" : [
        [100,200,300],
        [101,201,301],
        [102,202,302]
    ]
}
"""

class BodyProgressBar(QProgressBar):
    
    def __init__(self, *args, **kwargs):
        super( BodyProgressBar, self ).__init__(*args, **kwargs)
        self._text = ""
    
    def setText(self, text):
        self._text = text
    
    def text(self):
        return self._text

class BodyTreeColumns():
    ID = 0
    Button1 = 1
    Button2 = 2

class AnnotationTableColumns():
    Body = 0
    Coordinates = 1

class BodySplitInfoWidget( QWidget ):
    
    navigationRequested = pyqtSignal(object) # (3d coordinate tuple)
    
    def __init__(self, parent, opSplitBodyCarving):
        # We don't pass parent to the QWidget because we want the window to be top-level
        super( BodySplitInfoWidget, self ).__init__() 
        self.opSplitBodyCarving = opSplitBodyCarving
        
        self._annotationFilepath = None
        if self.opSplitBodyCarving.AnnotationFilepath.ready():
            self._annotationFilepath = self.opSplitBodyCarving.AnnotationFilepath.value
        self._annotationCoordinates = {} # label : 3d coordinates
        self._ravelerLabels = set()
        
        self._initUi()
        
        if self._annotationFilepath is not None:
            self._loadAnnotationFile()
        self.refreshButton.setEnabled(self._annotationFilepath is not None)

    def _initUi(self):
        # Load the ui file into this class (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        uiFilePath = os.path.join( localDir, 'bodySplitInfoWidget.ui' )
        uic.loadUi(uiFilePath, self)
        
        self.setWindowTitle("Body Split Info")
        
        self.bodyTreeWidget.setHeaderLabels( ['Body ID', 'Progress', ''] )
        
        self.annotationTableWidget.setColumnCount(2)
        self._initAnnotationTableHeader()
        self.annotationTableWidget.itemDoubleClicked.connect( self._handleAnnotationDoubleClick )
        self.annotationTableWidget.setSelectionBehavior( QTableView.SelectRows )
        self.annotationTableWidget.horizontalHeader().setResizeMode( QHeaderView.Stretch )
        
        self.loadSplitAnnoationFileButton.pressed.connect( self._loadNewAnnotationFile )
        self.loadSplitAnnoationFileButton.setIcon( QIcon(ilastikIcons.Open) )

        self.refreshButton.pressed.connect( self._loadAnnotationFile )
        self.refreshButton.setIcon( QIcon(ilastikIcons.Refresh) )

    def _loadNewAnnotationFile(self):
        """
        Ask the user for a new annotation filepath, and then load it.
        """
        navDir = ""
        if self._annotationFilepath is not None:
            navDir = os.path.split( self._annotationFilepath )[0]

        selected_file = QFileDialog.getOpenFileName(self,
                                    "Load Split Annotation File",
                                    navDir,
                                    "JSON files (*.json)",
                                     options=QFileDialog.DontUseNativeDialog)
        if selected_file.isNull():
            return

        self._annotationFilepath = str( selected_file )
        self.refreshButton.setEnabled(self._annotationFilepath is not None)
        self._loadAnnotationFile()
    
    def _loadAnnotationFile(self):
        """
        Load the annotation file using the path stored in our member variable.
        """        
        self.annotationFilepathEdit.setText( self._annotationFilepath )

        try:
            with open(self._annotationFilepath) as annotationFile:
                jsonDict = json.load( annotationFile )
        except Exception as ex:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self,
                                 "Failed to parse",
                                 "Wasn't able to parse your annotation file.  See console output for details." )
            self._annotationFilepath = None
            self.annotationFilepathEdit.setText("")

        if 'coordinates' not in jsonDict:
            QMessageBox.critical(self,
                                 "Invalid format",
                                 "Couldn't find the 'coordinates' list in your annotation file.  Giving up." )
            self._annotationFilepath = None
            self.annotationFilepathEdit.setText("")
            
        coordinates = jsonDict['coordinates']
        assert isinstance(coordinates, list)
        coordinates = map( tuple, coordinates )
        
        # Determine the Raveler label of each coordinate
        for coord3d in coordinates:
            coord5d = (0,) + coord3d + (0,)
            pos = TinyVector(coord5d)
            sample_roi = (pos, pos+1)
            ravelerLabelSample = self.opSplitBodyCarving.RavelerLabels(*sample_roi).wait()
            ravelerLabel = ravelerLabelSample[0,0,0,0,0]
            
            self._annotationCoordinates[coord3d] = ravelerLabel
            self._ravelerLabels.add( ravelerLabel )
        
        self._reloadInfoWidgets()
        
        self.opSplitBodyCarving.AnnotationFilepath.setValue( self._annotationFilepath )


    def _handleAnnotationDoubleClick(self, item):
        coord3d, ravelerLabel = item.data(Qt.UserRole).toPyObject()
        self.navigationRequested.emit( coord3d )
        
    def _reloadInfoWidgets(self):
        self._reloadBodyTree()
        self._reloadAnnotationTable()
    
    def _reloadBodyTree(self):
        self.bodyTreeWidget.clear()
        
        currentEditingFragmentName = self.opSplitBodyCarving.currentObjectName()
        
        for ravelerLabel in sorted( self._ravelerLabels ):
            fragmentNames = self.opSplitBodyCarving.getSavedObjectNamesForRavelerLabel(ravelerLabel)
            
            # For this raveler label, how many fragments do we have and how many do we expect?
            num_splits = reduce( lambda count, v: count + (v == ravelerLabel),
                                 self._annotationCoordinates.values(),
                                 0 )
            num_expected = num_splits + 1
            num_fragments = len(fragmentNames)
            
            # Parent row for the raveler body            
            progressText = "({}/{})".format( num_fragments, num_expected )
            bodyItem = QTreeWidgetItem( ["{}".format(ravelerLabel),
                                         progressText,
                                         ""] )
            self.bodyTreeWidget.invisibleRootItem().addChild(bodyItem)

            progressBar = BodyProgressBar(self)
            progressBar.setMaximum( num_expected )
            progressBar.setValue( min( num_fragments, num_expected ) )
            progressBar.setText( progressText )
            self.bodyTreeWidget.setItemWidget( bodyItem, BodyTreeColumns.Button1, progressBar )

            selectButton = QPushButton( "New Fragment" )
            selectButton.pressed.connect( partial( self._startNewFragment, ravelerLabel ) )
            selectButton.setEnabled( currentEditingFragmentName == "" )
            selectButton.setIcon( QIcon(ilastikIcons.AddSel) )
            self.bodyTreeWidget.setItemWidget( bodyItem, BodyTreeColumns.Button2, selectButton )
            bodyItem.setExpanded(True)
            
            # Child rows for each fragment
            fragmentItem = None
            for fragmentName in sorted(fragmentNames):
                fragmentItem = QTreeWidgetItem( [fragmentName, "", ""] )
                bodyItem.addChild( fragmentItem )

            # Add 'edit' and 'delete' buttons to the LAST fragment item
            if fragmentItem is not None:
                assert fragmentName is not None
                if fragmentName == currentEditingFragmentName:
                    saveButton = QPushButton( "Save" )
                    saveButton.pressed.connect( partial( self._saveFragment, fragmentName ) )
                    saveButton.setIcon( QIcon(ilastikIcons.Save) )
                    self.bodyTreeWidget.setItemWidget( fragmentItem, BodyTreeColumns.Button1, saveButton )
                else:
                    editButton = QPushButton( "Edit" )
                    editButton.pressed.connect( partial( self._editFragment, fragmentName ) )
                    editButton.setEnabled( currentEditingFragmentName == "" )
                    editButton.setIcon( QIcon(ilastikIcons.Edit) )
                    self.bodyTreeWidget.setItemWidget( fragmentItem, BodyTreeColumns.Button1, editButton )
    
                deleteButton = QPushButton( "Delete" )
                deleteButton.pressed.connect( partial( self._deleteFragment, fragmentName ) )
                deleteButton.setEnabled( currentEditingFragmentName == "" or currentEditingFragmentName == fragmentName )
                deleteButton.setIcon( QIcon(ilastikIcons.RemSel) )
                self.bodyTreeWidget.setItemWidget( fragmentItem, BodyTreeColumns.Button2, deleteButton )

    def _initAnnotationTableHeader(self):
        self.annotationTableWidget.setHorizontalHeaderLabels( ['Original Body', 'Coordinates'] )
            
    def _reloadAnnotationTable(self):
        self.annotationTableWidget.clear()
        self.annotationTableWidget.setRowCount( len(self._annotationCoordinates) )
        self._initAnnotationTableHeader()
        
        # Flip the key/value of the annotation list so we can sort them by label
        annotations = self._annotationCoordinates.items()
        annotations = map( lambda x: (x[1], x[0]), annotations )
        
        for row, (ravelerLabel, coord3d) in enumerate( sorted( annotations ) ):
            coordItem = QTableWidgetItem( "{}".format( coord3d ) )
            labelItem = QTableWidgetItem( "{}".format( ravelerLabel ) )
            
            coordItem.setData( Qt.UserRole, ( coord3d, ravelerLabel ) )
            labelItem.setData( Qt.UserRole, ( coord3d, ravelerLabel ) )
            
            self.annotationTableWidget.setItem( row, AnnotationTableColumns.Coordinates, coordItem )
            self.annotationTableWidget.setItem( row, AnnotationTableColumns.Body, labelItem )
        
    def _startNewFragment(self, ravelerLabel):
        # TODO: This save/load sequence involves two recomputes in a row.  It could be only 1. 
        self.opSplitBodyCarving.CurrentRavelerLabel.setValue( ravelerLabel )

        # Clear all seeds
        self.opSplitBodyCarving.clearCurrentLabeling( trigger_recompute=False )

        # "Save As" (with no seeds) with the appropriate name
        fragmentName = self._getNextAvailableFragmentName( ravelerLabel )
        self.opSplitBodyCarving.saveObjectAs( fragmentName )
        
        # "Load" the saved (empty) object
        self.opSplitBodyCarving.loadObject( fragmentName )
        
        # Refresh the entire table.
        self._reloadBodyTree()


    def _getNextAvailableFragmentName(self, ravelerLabel):
        fragmentNames = self.opSplitBodyCarving.getSavedObjectNamesForRavelerLabel(ravelerLabel)
        if len(fragmentNames) == 0:
            return "{}.A".format( ravelerLabel )

        # Find the last name and increment the fragment letter
        # e.g. 4321.B --> 4321.C
        fragmentNames = sorted(fragmentNames)
        assert len(fragmentNames) < 25, "Need to refine fragment naming scheme.  The current scheme only supports up to 26 fragments."
        letter = fragmentNames[-1][-1]
        nextLetter = chr( ord(letter)+1 )
        return "{}.{}".format( ravelerLabel, nextLetter )

    def _editFragment(self, fragmentName):
        self.opSplitBodyCarving.loadObject( fragmentName )
        self._reloadBodyTree()
    
    def _deleteFragment(self, fragmentName):
        # This might be the "current object" that we're deleting.
        # That's okay.
        self.opSplitBodyCarving.deleteObject( fragmentName )
        self._reloadBodyTree()

    def _saveFragment(self, fragmentName):
        self.opSplitBodyCarving.saveObjectAs( fragmentName )

        # After save, there is no longer a "current object"
        self._reloadBodyTree()
        








