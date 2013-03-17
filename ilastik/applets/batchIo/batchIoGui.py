from PyQt4.QtGui import *
from PyQt4 import uic

import threading

from functools import partial
import os
import sys
import copy
import ilastik.utility # This is the ilastik shell utility module
from ilastik.utility import bind
from ilastik.utility import PathComponents

from ilastik.shell.gui.iconMgr import ilastikIcons
import ilastik.applets.base.applet

from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui

import logging
logger = logging.getLogger(__name__)
traceLogger = logging.getLogger('TRACE.' + __name__)
from lazyflow.utility import Tracer

from opBatchIo import SupportedFormats

class Column():
    """ Enum for table column positions """
    Dataset = 0
    ExportLocation = 1
    Action = 2

class BatchIoGui(QWidget):
    """
    Manages all GUI elements in the data selection applet.
    This class itself is the central widget and also owns/manages the applet drawer widgets.
    """
    ###########################################
    ### AppletGuiInterface Concrete Methods ###
    ###########################################
    
    def centralWidget( self ):
        return self

    def appletDrawer(self):
        return self.drawer

    def menus( self ):
        return []

    def viewerControlWidget(self):
        return self._viewerControlWidgetStack

    def setImageIndex(self, index):
        pass

    def stopAndCleanUp(self):
        pass

    def imageLaneAdded(self, laneIndex):
        pass

    def imageLaneRemoved(self, laneIndex, finalLength):
        pass

    ###########################################
    ###########################################
    
    def __init__(self, topLevelOperator, guiControlSignal, progressSignal, title):
        with Tracer(traceLogger):
            super(BatchIoGui, self).__init__()
    
            self.title = title
            self.drawer = None
            self.topLevelOperator = topLevelOperator
            
            self.initAppletDrawerUic()
            self.initCentralUic()
            self.chosenExportDirectory = '/'
            self.initViewerControls()
            
            self.guiControlSignal = guiControlSignal
            self.progressSignal = progressSignal
            
            def handleNewDataset( multislot, index ):
                # Make room in the GUI table
                self.batchOutputTableWidget.insertRow( index )
                
                # Update the table row data when this slot has new data
                # We can't bind in the row here because the row may change in the meantime.
                multislot[index].notifyDirty( bind( self.updateTableForSlot ) )
                if multislot[index].ready():
                    self.updateTableForSlot( multislot[index] )
    
            self.topLevelOperator.OutputDataPath.notifyInserted( bind( handleNewDataset ) )
            
            # For each dataset that already exists, update the GUI
            for i, subslot in enumerate(self.topLevelOperator.OutputDataPath):
                handleNewDataset( self.topLevelOperator.OutputDataPath, i )
                if subslot.ready():
                    self.updateTableForSlot(subslot)
        
            def handleImageRemoved( multislot, index, finalLength ):
                if self.batchOutputTableWidget.rowCount() <= finalLength:
                    return

                # Remove the row we don't need any more
                self.batchOutputTableWidget.removeRow( index )

                # Remove the viewer for this dataset
                imageSlot = self.topLevelOperator.ImageToExport[index]
                if imageSlot in self.layerViewerGuis.keys():
                    layerViewerGui = self.layerViewerGuis[imageSlot]
                    self.viewerStack.removeWidget( layerViewerGui )
                    self._viewerControlWidgetStack.removeWidget( layerViewerGui.viewerControlWidget() )
                    layerViewerGui.stopAndCleanUp()

            self.topLevelOperator.ImageToExport.notifyRemove( bind( handleImageRemoved ) )
            
            self.topLevelOperator.Suffix.notifyDirty( self.updateDrawerGuiFromOperatorSettings )
            self.topLevelOperator.ExportDirectory.notifyDirty( self.updateDrawerGuiFromOperatorSettings )
            self.topLevelOperator.Format.notifyDirty( self.updateDrawerGuiFromOperatorSettings )
            self.updateDrawerGuiFromOperatorSettings()
        
    def initAppletDrawerUic(self):
        """
        Load the ui file for the applet drawer, which we own.
        """
        with Tracer(traceLogger):
            # Load the ui file (find it in our own directory)
            localDir = os.path.split(__file__)[0]+'/'
            # (We don't pass self here because we keep the drawer ui in a separate object.)
            self.drawer = uic.loadUi(localDir+"/batchIoDrawer.ui")
    
            # Set up our handlers
            self.drawer.saveWithInputButton.toggled.connect( self.handleExportLocationOptionChanged )
            self.drawer.saveToDirButton.toggled.connect( self.handleExportLocationOptionChanged )
            
            self.drawer.outputDirChooseButton.clicked.connect( self.chooseNewExportDirectory )        
            self.drawer.outputSuffixEdit.textEdited.connect( self.handleNewOutputSuffix )
            
            self.drawer.exportAllButton.clicked.connect( self.exportAllResults )
            self.drawer.exportAllButton.setIcon( QIcon(ilastikIcons.Save) )
            self.drawer.deleteAllButton.clicked.connect( self.deleteAllResults )
            self.drawer.deleteAllButton.setIcon( QIcon(ilastikIcons.Clear) )

            
            for i, formatInfo in sorted(SupportedFormats.items()):
                self.drawer.exportFormatCombo.addItem( formatInfo.name + ' (' + formatInfo.extension + ')' )
            self.drawer.exportFormatCombo.currentIndexChanged.connect( partial(self.handleExportFormatChanged) )

    def initCentralUic(self):
        """
        Load the GUI from the ui file into this class and connect it with event handlers.
        """
        # Load the ui file into this class (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        uic.loadUi(localDir+"/batchIo.ui", self)

        self.batchOutputTableWidget.resizeRowsToContents()
        self.batchOutputTableWidget.resizeColumnsToContents()
        self.batchOutputTableWidget.setAlternatingRowColors(True)
        self.batchOutputTableWidget.setShowGrid(False)
        self.batchOutputTableWidget.horizontalHeader().setResizeMode(0, QHeaderView.Interactive)
        
        self.batchOutputTableWidget.horizontalHeader().resizeSection(Column.Dataset, 200)
        self.batchOutputTableWidget.horizontalHeader().resizeSection(Column.ExportLocation, 250)
        self.batchOutputTableWidget.horizontalHeader().resizeSection(Column.Action, 100)

        self.batchOutputTableWidget.verticalHeader().hide()

        # Set up handlers
        self.batchOutputTableWidget.itemSelectionChanged.connect(self.handleTableSelectionChange)

        # Set up the viewer area
        self.initViewerStack()
        self.splitter.setSizes([150, 850])
    
    def initViewerStack(self):
        self.layerViewerGuis = {}
        self.viewerStack.addWidget( QWidget() )
        
    def initViewerControls(self):
        self._viewerControlWidgetStack = QStackedWidget(parent=self)

    def handleExportLocationOptionChanged(self):
        """
        The user has changed the export directory option (radio buttons).
        """
        saveWithInput = self.drawer.saveWithInputButton.isChecked()
        if saveWithInput:
            # Set to '', which means export data is stored in the input data directory
            self.topLevelOperator.ExportDirectory.setValue('')
        else:
            self.topLevelOperator.ExportDirectory.setValue(self.chosenExportDirectory)

        for index, slot in enumerate(self.topLevelOperator.OutputDataPath):
            self.updateTableForSlot(slot)
    
    def handleExportFormatChanged(self, index):
        with Tracer(traceLogger):
            self.topLevelOperator.Format.setValue( index )
    
    def chooseNewExportDirectory(self):
        """
        The user wants to choose a new export directory.
        """
        with Tracer(traceLogger):
            # Launch the "Open File" dialog
            directoryName = QFileDialog.getExistingDirectory(self, "Export Directory", os.path.abspath(__file__))
    
            # Stop now if the user canceled
            if directoryName.isNull():
                return
            
            self.chosenExportDirectory = str( directoryName )
            self.drawer.outputDirEdit.setText( directoryName )
    
            # Auto-check the radio button for this option if necessary
            if not self.drawer.saveToDirButton.isChecked():
                self.drawer.saveToDirButton.setChecked(True)
            else:
                self.handleExportLocationOptionChanged()
    
    def handleNewOutputSuffix(self):
        with Tracer(traceLogger):
            suffix = str( self.drawer.outputSuffixEdit.text() )
            
            self.topLevelOperator.Suffix.setValue( suffix )
    
            # Update every row of the GUI        
            for index, slot in enumerate(self.topLevelOperator.OutputDataPath):
                self.updateTableForSlot(slot)

    def getSlotIndex(self, multislot, subslot ):
        with Tracer(traceLogger):
            # Which index is this slot?
            for index, slot in enumerate(multislot):
                if slot == subslot:
                    return index
            return -1

    def updateTableForSlot(self, slot):
        """
        Update the table row that corresponds to the given slot of the top-level operator (could be either input slot)
        """
        row = self.getSlotIndex( self.topLevelOperator.OutputDataPath, slot )
        assert row != -1, "Unknown input slot!"

        if not self.topLevelOperator.OutputDataPath[row].ready():
            return
        
        datasetPath = self.topLevelOperator.DatasetPath[row].value
        outputDataPath = self.topLevelOperator.OutputDataPath[row].value
                
        self.batchOutputTableWidget.setItem( row, Column.Dataset, QTableWidgetItem(datasetPath) )
        self.batchOutputTableWidget.setItem( row, Column.ExportLocation, QTableWidgetItem( outputDataPath ) )

        exportNowButton = QPushButton("Export")
        exportNowButton.setToolTip("Generate individual batch output dataset.")
        exportNowButton.clicked.connect( bind(self.exportResultsForSlot, self.topLevelOperator.ExportResult[row], self.topLevelOperator.ProgressSignal[row] ) )
        self.batchOutputTableWidget.setCellWidget( row, Column.Action, exportNowButton )

        # Select a row if there isn't one already selected.
        selectedRanges = self.batchOutputTableWidget.selectedRanges()
        if len(selectedRanges) == 0:
            self.batchOutputTableWidget.selectRow(0)


    def updateDrawerGuiFromOperatorSettings(self, *args):
        with Tracer(traceLogger):
            if self.topLevelOperator.Suffix.ready():
                self.drawer.outputSuffixEdit.setText( self.topLevelOperator.Suffix.value )
            
            if self.topLevelOperator.ExportDirectory.ready():
                self.drawer.outputDirEdit.setText( self.topLevelOperator.ExportDirectory.value )
                self.drawer.saveToDirButton.setChecked( self.topLevelOperator.ExportDirectory.value != '' )
                self.drawer.saveWithInputButton.setChecked( self.topLevelOperator.ExportDirectory.value == '' )
                self.drawer.outputDirChooseButton.setEnabled( self.drawer.saveToDirButton.isChecked() )
                self.drawer.outputDirEdit.setEnabled( self.drawer.saveToDirButton.isChecked() )
            
            if self.topLevelOperator.Format.ready():
                formatId = self.topLevelOperator.Format.value
                self.drawer.exportFormatCombo.setCurrentIndex( formatId )

    def handleTableSelectionChange(self):
        """
        Any time the user selects a new item, select the whole row.
        """
        self.selectEntireRow()
        self.showSelectedDataset()
    
    def selectEntireRow(self):
        # Figure out which row is selected
        selectedItemRows = set()
        selectedRanges = self.batchOutputTableWidget.selectedRanges()
        for rng in selectedRanges:
            for row in range(rng.topRow(), rng.bottomRow()+1):
                selectedItemRows.add(row)
        
        # Disconnect from selection change notifications while we do this
        self.batchOutputTableWidget.itemSelectionChanged.disconnect(self.handleTableSelectionChange)
        for row in selectedItemRows:
            self.batchOutputTableWidget.selectRow(row)

        # Reconnect now that we're finished
        self.batchOutputTableWidget.itemSelectionChanged.connect(self.handleTableSelectionChange)
        
    def exportSlots(self, slotList, progressSignalSlotList ):
        with Tracer(traceLogger):
            try:
                # Don't let anyone change the classifier while we're exporting...
                self.guiControlSignal.emit( ilastik.applets.base.applet.ControlCommand.DisableUpstream )
                
                # Also disable this applet's controls
                self.guiControlSignal.emit( ilastik.applets.base.applet.ControlCommand.DisableSelf )

                # Start with 1% so the progress bar shows up
                self.progressSignal.emit(0)
                self.progressSignal.emit(1)

                def signalFileProgress(slotIndex, percent):
                    self.progressSignal.emit( (100*slotIndex + percent) / len(slotList) ) 

                for i, slot in enumerate(slotList):
                    logger.debug("Exporting result {}".format(i))

                    # If the operator provides a progress signal, use it.
                    slotProgressSignal = progressSignalSlotList[i].value
                    slotProgressSignal.subscribe( partial(signalFileProgress, i) )
                    
                    result = slot.value
                    if not result:
                        logger.error("Failed to export an image.")
    
                    # We're finished with this file. 
                    self.progressSignal.emit( 100*(i+1)/float(len(slotList)) )
                    
                # Ensure the shell knows we're really done.
                self.progressSignal.emit(100)
            except:
                # Cancel our progress.
                self.progressSignal.emit(0, True)
                raise
            finally:            
                # Now that we're finished, it's okay to use the other applets again.
                self.guiControlSignal.emit( ilastik.applets.base.applet.ControlCommand.Pop ) # Enable ourselves
                self.guiControlSignal.emit( ilastik.applets.base.applet.ControlCommand.Pop ) # Enable the others we disabled

    def exportResultsForSlot(self, slot, progressSlot):
        with Tracer(traceLogger):
            # Do this in a separate thread so the UI remains responsive
            exportThread = threading.Thread(target=bind(self.exportSlots, [slot], [progressSlot]), name="BatchIOExportThread")
            exportThread.start()
    
    def exportAllResults(self):
        with Tracer(traceLogger):
            # Do this in a separate thread so the UI remains responsive
            exportThread = threading.Thread(target=bind(self.exportSlots, self.topLevelOperator.ExportResult, self.topLevelOperator.ProgressSignal), name="BatchIOExportThread")
            exportThread.start()

    def deleteAllResults(self):
        with Tracer(traceLogger):
            for slot in self.topLevelOperator.OutputDataPath:
                os.remove(slot.value)
    
    def showSelectedDataset(self):
        """
        Show the exported file in the viewer
        """
        # Get the selected row and corresponding slot value
        selectedRanges = self.batchOutputTableWidget.selectedRanges()
        if len(selectedRanges) == 0:
            return
        row = selectedRanges[0].topRow()
        imageSlot = self.topLevelOperator.ImageToExport[row]
        
        # Create if necessary
        if imageSlot not in self.layerViewerGuis.keys():
            opLane = self.topLevelOperator.getLane(row)
            layerViewer = self.createLayerViewer(opLane)

            # Maximize the x-y view by default.
            layerViewer.volumeEditorWidget.quadview.ensureMaximized(2)
            
            self.layerViewerGuis[imageSlot] = layerViewer
            self.viewerStack.addWidget( layerViewer )
            self._viewerControlWidgetStack.addWidget( layerViewer.viewerControlWidget() )

        # Show the right one
        self.viewerStack.setCurrentWidget( self.layerViewerGuis[imageSlot] )


    def createLayerViewer(self, opLane):
        return BatchIoLayerViewerGui(opLane)

class BatchIoLayerViewerGui(LayerViewerGui):
    """
    Subclass the default LayerViewerGui implementation so we can provide a custom layer order.
    """

    def setupLayers(self):
        layers = []

        # Show the exported data on disk
        opLane = self.topLevelOperatorView
        exportedDataSlot = opLane.ExportedImage
        if exportedDataSlot.ready():
            exportLayer = self.createStandardLayerFromSlot( exportedDataSlot )
            exportLayer.name = "Exported Image"
            exportLayer.visible = True
            exportLayer.opacity = 1.0
            layers.append(exportLayer)
        
        # Show the (live-updated) data we're exporting
        previewSlot = opLane.ImageToExport
        if previewSlot.ready():
            previewLayer = self.createStandardLayerFromSlot( previewSlot )
            previewLayer.name = "Live Preview"
            previewLayer.visible = False # off by default
            previewLayer.opacity = 1.0
            layers.append(previewLayer)

        rawSlot = opLane.RawImage
        if rawSlot.ready():
            rawLayer = self.createStandardLayerFromSlot( rawSlot )
            rawLayer.name = "Raw Data"
            rawLayer.visible = True
            rawLayer.opacity = 1.0
            layers.append(rawLayer)

        return layers









