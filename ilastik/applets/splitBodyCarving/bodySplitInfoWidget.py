import os
import json
from functools import partial

import numpy

from PyQt4 import uic
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QWidget, QFileDialog, QMessageBox, QTreeWidgetItem, QTableWidgetItem, QPushButton

from lazyflow.roi import TinyVector

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

class BodyTreeColumns():
    ID = 0
    Button1 = 1
    Button2 = 2

class BodySplitInfoWidget( QWidget ):
    
    def __init__(self, parent, opSplitBodyCarving):
        # We don't pass parent to the QWidget because we want the window to be top-level
        super( BodySplitInfoWidget, self ).__init__() 
        self.opSplitBodyCarving = opSplitBodyCarving
        
        self._annotationFilepath = None
        self._annotationCoordinates = {} # label : 3d coordinates
        self._ravelerLabels = set()
        
        self._initUi()

    def _initUi(self):
        # Load the ui file into this class (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        uiFilePath = os.path.join( localDir, 'bodySplitInfoWidget.ui' )
        uic.loadUi(uiFilePath, self)
        
        self.bodyTreeWidget.setHeaderLabels( ['Body ID', '', ''] )
        self.annotationTableWidget.setColumnCount(2)
        self.annotationTableWidget.setHorizontalHeaderLabels( ['Coordinates', 'Original Body'] )
        
        self.loadSplitAnnoationFileButton.pressed.connect( self._loadAnnotationFile )
        self.refreshButton.pressed.connect( self._reloadInfoWidgets )

    def _loadAnnotationFile(self):
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
        
    def _reloadInfoWidgets(self):
        self._reloadBodyTree()
        self._reloadAnnotationTable()
    
    def _reloadBodyTree(self):
        self.bodyTreeWidget.clear()
        for ravelerLabel in sorted( self._ravelerLabels ):
            # Parent row for the raveler body
            bodyItem = QTreeWidgetItem( ["{}".format(ravelerLabel), "", ""] )
            self.bodyTreeWidget.invisibleRootItem().addChild(bodyItem)

            selectButton = QPushButton( "New Fragment" )
            selectButton.pressed.connect( partial( self._selectRavelerLabel, ravelerLabel ) )
            self.bodyTreeWidget.setItemWidget( bodyItem, BodyTreeColumns.Button1, selectButton )
            
            # Child rows for each fragment
            fragmentNames = self.opSplitBodyCarving._getSavedObjectNamesForRavelerLabel(ravelerLabel)
            fragmentItem = None
            for fragmentName in fragmentNames:
                fragmentItem = QTreeWidgetItem(fragmentName, "", "")
                bodyItem.addChild( fragmentItem )

            # Add 'edit' and 'delete' buttons to the LAST fragment item
            if fragmentItem is not None:
                editButton = QPushButton( "Edit" )
                editButton.pressed.connect( partial( self._editFragment, fragmentName ) )
                self.bodyTreeWidget.setItemWidget( fragmentItem, BodyTreeColumns.Button1, editButton )

                deleteButton = QPushButton( "Delete" )
                deleteButton.pressed.connect( partial( self._deleteFragment, fragmentName ) )
                self.bodyTreeWidget.setItemWidget( fragmentItem, BodyTreeColumns.Button2, deleteButton )
            
    def _reloadAnnotationTable(self):
        self.annotationTableWidget.clear()
        self.annotationTableWidget.setRowCount( len(self._annotationCoordinates) )
        
        for row, (coord3d, ravelerLabel) in enumerate(self._annotationCoordinates.items()):
            coordItem = QTableWidgetItem( "{}".format( coord3d ) )
            labelItem = QTableWidgetItem( "{}".format( ravelerLabel ) )
            
            self.annotationTableWidget.setItem( row, 0, coordItem )
            self.annotationTableWidget.setItem( row, 1, labelItem )            
        
    def _selectRavelerLabel(self, ravelerLabel):
        pass

    def _editFragment(self, fragmentName):
        pass
    
    def _deleteFragment(self, fragmentName):
        pass
        








