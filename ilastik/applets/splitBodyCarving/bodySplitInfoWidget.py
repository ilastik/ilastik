import sys
import os
import json
from functools import partial
import collections

import numpy

from PyQt4 import uic
from PyQt4.QtCore import Qt, pyqtSignal
from PyQt4.QtGui import QWidget, QFileDialog, QMessageBox, QTreeWidgetItem, QTableWidgetItem, \
                        QPushButton, QTableView, QHeaderView, QIcon, QProgressBar

from lazyflow.roi import TinyVector

from ilastik.shell.gui.iconMgr import ilastikIcons

from opSplitBodyCarving import OpParseAnnotations

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
    Comment = 2

class BodySplitInfoWidget( QWidget ):
    
    navigationRequested = pyqtSignal(object) # (3d coordinate tuple)
    
    def __init__(self, parent, opSplitBodyCarving):
        # We don't pass parent to the QWidget because we want the window to be top-level
        super( BodySplitInfoWidget, self ).__init__() 
        self.opSplitBodyCarving = opSplitBodyCarving
        self._bodyTreeParentItems = {} # This is easier to maintain than using setData/find
        
        annotation_filepath = None
        if self.opSplitBodyCarving.AnnotationFilepath.ready():
            annotation_filepath = self.opSplitBodyCarving.AnnotationFilepath.value
        self._annotations = {} # coordinate : Annotation
        self._ravelerLabels = set()
        
        self._initUi()
        
        if annotation_filepath is not None:
            self._loadAnnotationFile( annotation_filepath )
        self.refreshButton.setEnabled( annotation_filepath is not None )

    def _initUi(self):
        # Load the ui file into this class (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        uiFilePath = os.path.join( localDir, 'bodySplitInfoWidget.ui' )
        uic.loadUi(uiFilePath, self)
        
        self.setWindowTitle("Body Split Info")
        
        self.bodyTreeWidget.setHeaderLabels( ['Body ID', 'Progress', ''] )
        self.bodyTreeWidget.header().setResizeMode( QHeaderView.ResizeToContents )
        self.bodyTreeWidget.header().setStretchLastSection(False)
        self.bodyTreeWidget.itemDoubleClicked.connect( self._handleBodyTreeDoubleClick )
        self.bodyTreeWidget.setExpandsOnDoubleClick(False) # We want to use double-click for auto-navigation
        
        
        self.annotationTableWidget.setColumnCount(3)
        self._initAnnotationTableHeader()
        self.annotationTableWidget.itemDoubleClicked.connect( self._handleAnnotationDoubleClick )
        self.annotationTableWidget.setSelectionBehavior( QTableView.SelectRows )
        self.annotationTableWidget.horizontalHeader().setResizeMode( QHeaderView.ResizeToContents )
        
        self.loadSplitAnnoationFileButton.pressed.connect( self._loadNewAnnotationFile )
        self.loadSplitAnnoationFileButton.setIcon( QIcon(ilastikIcons.Open) )

        self.refreshButton.pressed.connect( self._refreshAnnotations )
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

        self.refreshButton.setEnabled( not selected_file.isNull() )
        if selected_file.isNull():
            return

        self._loadAnnotationFile( str( selected_file ) )
    
    def _loadAnnotationFile(self, annotation_filepath):
        """
        Load the annotation file using the path stored in our member variable.
        """        
        try:
            # Configure operator
            self.opSplitBodyCarving.AnnotationFilepath.setValue( annotation_filepath )

            # Requesting annotations triggers parse.
            self._annotations = self.opSplitBodyCarving.Annotations.value
            self._ravelerLabels = self.opSplitBodyCarving.AnnotationBodyIds.value

            # Update gui
            self._reloadInfoWidgets()
            self.annotationFilepathEdit.setText( annotation_filepath )
            
        except OpParseAnnotations.AnnotationParsingException as ex :
            import traceback
            if ex.original_exc is not None:
                traceback.print_exception( type(ex.original_exc), ex.original_exc, sys.exc_info()[2] )
                sys.stderr.write( ex.msg )
            else:
                traceback.print_exc()
            QMessageBox.critical(self,
                                 "Failed to parse",
                                 ex.msg + "\n\nSee console output for details." )
            
            self._annotations = None
            self._ravelerLabels = None
            self.annotationFilepathEdit.setText("")
        except:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self,
                                 "Failed to parse",
                                 "Wasn't able to parse your bookmark file.  See console output for details." )
            self._annotations = None
            self._ravelerLabels = None
            self.annotationFilepathEdit.setText("")

    def _refreshAnnotations(self):
        if self.opSplitBodyCarving.AnnotationFilepath.ready():
            # Disconnect, then refresh.
            annotation_filepath = self.opSplitBodyCarving.AnnotationFilepath.value
            self.opSplitBodyCarving.AnnotationFilepath.disconnect()
            self._loadAnnotationFile( annotation_filepath )

    def _handleAnnotationDoubleClick(self, item):
        coord3d, ravelerLabel = item.data(Qt.UserRole).toPyObject()
        self._selectAnnotation(coord3d, ravelerLabel)

        # Highlight the appropriate row in the body list as a convenience
        bodyItem = self._bodyTreeParentItems[ravelerLabel]
        self.bodyTreeWidget.setCurrentItem( bodyItem )

    def _handleBodyTreeDoubleClick(self, item, column):
        if item in self._bodyTreeParentItems.values():
            
            selectedLabel = item.data(0, Qt.UserRole).toPyObject()
            
            # Find the first split point for this body
            for coord3d, annotation in self._annotations.items():
                if selectedLabel == annotation.ravelerLabel:
                    # Find a row to auto-select in the annotation table
                    for row in range( self.annotationTableWidget.rowCount() ):
                        if selectedLabel == self.annotationTableWidget.itemAt(row, 0).data(Qt.UserRole).toPyObject()[1]:
                            self.annotationTableWidget.selectRow( row )
                            break
                    self._selectAnnotation(coord3d, selectedLabel)
                    break
        
    def _selectAnnotation(self, coord3d, ravelerLabel):
        # Switch raveler labels if necessary.
        if self.opSplitBodyCarving.CurrentRavelerLabel.value != ravelerLabel:
            # Don't switch bodies if the user hasn't saved the current fragment
            currentFragmentName = self.opSplitBodyCarving.CurrentEditingFragment.value
            if currentFragmentName != "":
                QMessageBox.warning(self,
                                    "Unsaved Fragment",
                                    "Please save or delete the fragment you are editing ({}) "\
                                    "before moving on to a different raveler body.".format( currentFragmentName ) )
                return
            else:
                self.opSplitBodyCarving.CurrentRavelerLabel.setValue( ravelerLabel )
        self.navigationRequested.emit( coord3d )
        self._reloadBodyTree()
            
    def _reloadInfoWidgets(self):
        self._reloadBodyTree()
        self._reloadAnnotationTable()
    
    def _reloadBodyTree(self):
        self.bodyTreeWidget.clear()
        self._bodyTreeParentItems = {}
        
        currentEditingRavelerLabel = self.opSplitBodyCarving.CurrentRavelerLabel.value
        currentEditingFragmentName = self.opSplitBodyCarving.CurrentEditingFragment.value
        
        for ravelerLabel in sorted( self._ravelerLabels ):
            fragmentNames = self.opSplitBodyCarving.getFragmentNames(ravelerLabel)

            # For this raveler label, how many fragments do we have and how many do we expect?
            # Count the number of annotations with this label.
            num_splits = reduce( lambda count, ann: count + (ann.ravelerLabel == ravelerLabel),
                                 self._annotations.values(),
                                 0 )
            num_expected = num_splits + 1
            num_fragments = len(fragmentNames)
            
            # Parent row for the raveler body            
            progressText = "({}/{})".format( num_fragments, num_expected )
            bodyItem = QTreeWidgetItem( ["{}".format(ravelerLabel),
                                         progressText,
                                         ""] )
            bodyItem.setData( 0, Qt.UserRole, ravelerLabel )
            self._bodyTreeParentItems[ravelerLabel] = bodyItem
            self.bodyTreeWidget.invisibleRootItem().addChild(bodyItem)

            progressBar = BodyProgressBar(self)
            progressBar.setMaximum( num_expected )
            progressBar.setValue( min( num_fragments, num_expected ) )
            progressBar.setText( progressText )
            self.bodyTreeWidget.setItemWidget( bodyItem, BodyTreeColumns.Button1, progressBar )

            if currentEditingFragmentName == "" and currentEditingRavelerLabel == ravelerLabel:
                selectButton = QPushButton( "New Fragment" )
                selectButton.pressed.connect( partial( self._startNewFragment, ravelerLabel ) )
                selectButton.setIcon( QIcon(ilastikIcons.AddSel) )
                self.bodyTreeWidget.setItemWidget( bodyItem, BodyTreeColumns.Button2, selectButton )
            bodyItem.setExpanded(True)
            
            # Child rows for each fragment
            fragmentItem = None
            for fragmentName in fragmentNames:
                fragmentItem = QTreeWidgetItem( [fragmentName, "", ""] )
                bodyItem.addChild( fragmentItem )

            # Add 'edit' and 'delete' buttons to the LAST fragment item
            if fragmentItem is not None and ravelerLabel == currentEditingRavelerLabel:
                assert fragmentName is not None
                if currentEditingFragmentName == fragmentName:
                    saveButton = QPushButton( "Save" )
                    saveButton.pressed.connect( partial( self._saveFragment, fragmentName ) )
                    saveButton.setIcon( QIcon(ilastikIcons.Save) )
                    self.bodyTreeWidget.setItemWidget( fragmentItem, BodyTreeColumns.Button1, saveButton )
                elif currentEditingFragmentName == "":
                    editButton = QPushButton( "Edit" )
                    editButton.pressed.connect( partial( self._editFragment, fragmentName ) )
                    editButton.setIcon( QIcon(ilastikIcons.Edit) )
                    self.bodyTreeWidget.setItemWidget( fragmentItem, BodyTreeColumns.Button1, editButton )

                if currentEditingFragmentName == "" or currentEditingFragmentName == fragmentName:
                    deleteButton = QPushButton( "Delete" )
                    deleteButton.pressed.connect( partial( self._deleteFragment, fragmentName ) )
                    deleteButton.setIcon( QIcon(ilastikIcons.RemSel) )
                    self.bodyTreeWidget.setItemWidget( fragmentItem, BodyTreeColumns.Button2, deleteButton )

    def _initAnnotationTableHeader(self):
        self.annotationTableWidget.setHorizontalHeaderLabels( ['Original Body', 'Coordinates', 'Comment'] )
        self.annotationTableWidget.horizontalHeaderItem(AnnotationTableColumns.Comment).setTextAlignment(Qt.AlignLeft)
            
    def _reloadAnnotationTable(self):
        self.annotationTableWidget.clear()
        self.annotationTableWidget.setRowCount( len(self._annotations) )
        self._initAnnotationTableHeader()
        
        # Flip the key/value of the annotation list so we can sort them by label
        annotations = self._annotations.items()
        annotations = map( lambda (coord3d, (label,comment)): (label, coord3d, comment), annotations )
        annotations = sorted( annotations )
        
        for row, (ravelerLabel, coord3d, comment) in enumerate( annotations ):
            coordItem = QTableWidgetItem( "{}".format( coord3d ) )
            labelItem = QTableWidgetItem( "{}".format( ravelerLabel ) )
            commentItem = QTableWidgetItem( comment )
            
            coordItem.setData( Qt.UserRole, ( coord3d, ravelerLabel ) )
            labelItem.setData( Qt.UserRole, ( coord3d, ravelerLabel ) )
            commentItem.setData( Qt.UserRole, ( coord3d, ravelerLabel ) )
            
            self.annotationTableWidget.setItem( row, AnnotationTableColumns.Coordinates, coordItem )
            self.annotationTableWidget.setItem( row, AnnotationTableColumns.Body, labelItem )
            self.annotationTableWidget.setItem( row, AnnotationTableColumns.Comment, commentItem )
        
    def _startNewFragment(self, ravelerLabel):
        self.opSplitBodyCarving.CurrentRavelerLabel.setValue( ravelerLabel )

        fragmentName = self._getNextAvailableFragmentName( ravelerLabel )
        self.opSplitBodyCarving.CurrentEditingFragment.setValue( fragmentName )

        # Refresh the entire table.
        self._reloadBodyTree()


    def _getNextAvailableFragmentName(self, ravelerLabel):
        fragmentNames = self.opSplitBodyCarving.getFragmentNames(ravelerLabel)
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
        self.opSplitBodyCarving.CurrentEditingFragment.setValue( fragmentName )
        self.opSplitBodyCarving.loadObject( fragmentName )
        self._reloadBodyTree()
    
    def _deleteFragment(self, fragmentName):
        # This might be the "current object" that we're deleting.
        # That's okay.
        if self.opSplitBodyCarving.CurrentEditingFragment.value == fragmentName:
            self.opSplitBodyCarving.CurrentEditingFragment.setValue( "" )

        # Attempt to delete the object.
        if not self.opSplitBodyCarving.deleteObject( fragmentName ):
            # If it wasn't there, then we still need to delete the seeds
            self.opSplitBodyCarving.clearCurrentLabeling()

        self._reloadBodyTree()

    def _saveFragment(self, fragmentName):
        self.opSplitBodyCarving.CurrentEditingFragment.setValue( "" )
        self.opSplitBodyCarving.saveObjectAs( fragmentName )

        # After save, there is no longer a "current object"
        self._reloadBodyTree()
        








