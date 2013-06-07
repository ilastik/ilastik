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

# Example Raveler bookmark json file:
"""
{
  "data": [
    {
      "text": "split <username=ogundeyio> <time=1370275410> <status=review>", 
      "body ID": 4199, 
      "location": [
        361, 
        478, 
        1531
      ]
    }, 
    {
      "text": "split <username=ogundeyio> <time=1370275416> <status=review>", 
      "body ID": 4199, 
      "location": [
        301, 
        352, 
        1531
      ]
    }, 
    {
      "text": "Separate from bottom merge", 
      "body ID": 4182, 
      "location": [
        176, 
        419, 
        1556
      ]
    }, 
    {
      "text": "Needs to be separate", 
      "body ID": 4199, 
      "location": [
        163, 
        244, 
        1564
      ]
    }
  ],
  "metadata": {
    "username": "ogundeyio", 
    "software version": "1.7.15", 
    "description": "bookmarks", 
    "file version": 1, 
    "software revision": "4406", 
    "computer": "emrecon11.janelia.priv", 
    "date": "03-June-2013 14:49", 
    "session path": "/groups/flyem/data/medulla-FIB-Z1211-25-production/align2/substacks/00051_3508-4007_3759-4258_1500-1999/focused-910-sessions/ogundeyio.910", 
    "software": "Raveler"
  }
}
"""

# Example Raveler substack.json file.
# Note that raveler substacks are viewed as 500**3 volumes with a 10 pixel border on all sides,
#  which means that the volume ilastik actually loads is 520**3
# The bookmark Z-coordinates are GLOBAL to the entire stack, but the XY coordinates are relative 
#  to the 520**3 volume we have loaded.
# Therefore, we need to offset the Z-coordinates in any bookmarks we load using the idz1 and border fields below.
# In this example, idz1 = 1500, and border=10, which means the first Z-slice in the volume we loaded is slice 1490.
"""
{
    "idz1": 1500, 
    "gray_view": true, 
    "idz2": 1999, 
    "substack_id": 51, 
    "stack_path": "/groups/flyem/data/medulla-FIB-Z1211-25-production/align2", 
    "ry2": 4268, 
    "basename": "iso.%05d.png", 
    "substack_path": "/groups/flyem/data/medulla-FIB-Z1211-25-production/align2/substacks/00051_3508-4007_3759-4258_1500-1999", 
    "idx2": 4007, 
    "rz2": 2009, 
    "rz1": 1490, 
    "raveler_view": true, 
    "rx1": 3498, 
    "idy1": 3759, 
    "idx1": 3508, 
    "rx2": 4017, 
    "border": 10, 
    "idy2": 4258, 
    "ry1": 3749
}
"""


Annotation = collections.namedtuple( 'Annotation', ['ravelerLabel', 'comment'] )

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
        
        self._annotationFilepath = None
        if self.opSplitBodyCarving.AnnotationFilepath.ready():
            self._annotationFilepath = self.opSplitBodyCarving.AnnotationFilepath.value
        self._annotations = {} # coordinate : Annotation
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
        self.bodyTreeWidget.header().setResizeMode( QHeaderView.ResizeToContents )
        self.bodyTreeWidget.header().setStretchLastSection(False)
        
        self.annotationTableWidget.setColumnCount(3)
        self._initAnnotationTableHeader()
        self.annotationTableWidget.itemDoubleClicked.connect( self._handleAnnotationDoubleClick )
        self.annotationTableWidget.setSelectionBehavior( QTableView.SelectRows )
        self.annotationTableWidget.horizontalHeader().setResizeMode( QHeaderView.ResizeToContents )
        
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
                annotation_json_dict = json.load( annotationFile )
        except Exception as ex:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self,
                                 "Failed to parse",
                                 "Wasn't able to parse your bookmark file.  See console output for details." )
            self._annotationFilepath = None
            self.annotationFilepathEdit.setText("")
            return

        if 'data' not in annotation_json_dict:
            QMessageBox.critical(self,
                                 "Invalid format",
                                 "Couldn't find the 'data' list in your bookmark file.  Giving up." )
            self._annotationFilepath = None
            self.annotationFilepathEdit.setText("")
            return

        # Before we parse the bookmarks data, locate the substack description
        #  to calculate the z-coordinate offset (see comment about substack coordinates, above)
        bookmark_dir = os.path.split(self._annotationFilepath)[0]
        substack_dir = os.path.split(bookmark_dir)[0]
        substack_description_path = os.path.join( substack_dir, 'substack.json' )
        try:
            with open(substack_description_path) as substack_description_file:
                 substack_description_json_dict = json.load( substack_description_file )
        except Exception as ex:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self,
                                 "Failed to parse SUBSTACK",
                                 "Attempted to open substack description file:\n {}"
                                 "\n but something went wrong.  See console output for details.  Giving up."
                                 .format(substack_description_path) )
            self._annotationFilepath = None
            self.annotationFilepathEdit.setText("")
            return

        z_offset = substack_description_json_dict['idz1'] - substack_description_json_dict['border']

        bookmarks = annotation_json_dict['data']
        # Each bookmark is a dict (see example above)
        for bookmark in bookmarks:
            if 'text' in bookmark and str(bookmark['text']).lower().find( 'split' ) != -1:
                coord3d = bookmark['location']
                coord3d[2] -= z_offset # See comments above re: substack coordinates
                coord3d = tuple(coord3d)
                coord5d = (0,) + coord3d + (0,)
                pos = TinyVector(coord5d)
                sample_roi = (pos, pos+1)
                # For debug purposes, we sometimes load a smaller volume than the original.
                # Don't import bookmarks that fall outside our volume
                if (pos < self.opSplitBodyCarving.RavelerLabels.meta.shape).all():
                    ravelerLabelSample = self.opSplitBodyCarving.RavelerLabels(*sample_roi).wait()
                    ravelerLabel = ravelerLabelSample[0,0,0,0,0]
                    
                    self._annotations[coord3d] = Annotation(ravelerLabel=ravelerLabel, comment=str(bookmark['text']))
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
        








