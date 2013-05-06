#Python
from functools import partial
import os
import threading
import h5py
import logging
logger = logging.getLogger(__name__)
traceLogger = logging.getLogger('TRACE.' + __name__)

#PyQt
from PyQt4 import uic
from PyQt4.QtGui import QWidget, QStackedWidget, QMenu, QMessageBox, QFileDialog, QDialog

#lazyflow
from lazyflow.utility import Tracer
from lazyflow.request import Request

#volumina
from volumina.utility import PreferencesManager

#ilastik
from ilastik.config import cfg as ilastik_config
from ilastik.utility import bind
from ilastik.utility.gui import ThreadRouter, threadRouted
from ilastik.utility.pathHelpers import getPathVariants, areOnSameDrive, PathComponents
from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui
from ilastik.applets.base.applet import ControlCommand, DatasetConstraintError
from ilastik.widgets.massFileLoader import MassFileLoader

from opDataSelection import OpDataSelection, DatasetInfo
from dataLaneSummaryTableModel import DataLaneSummaryTableModel 
from dataDetailViewerWidget import DataDetailViewerWidget
from datasetInfoEditorWidget import DatasetInfoEditorWidget
from ilastik.widgets.stackFileSelectionWidget import StackFileSelectionWidget

#===----------------------------------------------------------------------------------------------------------------===

class LocationOptions():
    """ Enum for location menu options """
    Project = 0
    AbsolutePath = 1
    RelativePath = 2

class GuiMode():
    Normal = 0
    Batch = 1


class DataSelectionGui(QWidget):
    """
    Manages all GUI elements in the data selection applet.
    This class itself is the central widget and also owns/manages the applet drawer widgets.
    """

    ###########################################
    ### AppletGuiInterface Concrete Methods ###
    ###########################################

    def centralWidget( self ):
        return self

    def appletDrawer( self ):
        return self._drawer

    def menus( self ):
        return []

    def viewerControlWidget(self):
        return self._viewerControlWidgetStack

    def setImageIndex(self, imageIndex):
        if imageIndex is not None:
            self.laneSummaryTableView.selectRow(imageIndex)
            for detailWidget in self._detailViewerWidgets:
                detailWidget.datasetDetailTableView.selectRow(imageIndex)

    def stopAndCleanUp(self):
        for editor in self.volumeEditors.values():
            self.viewerStack.removeWidget( editor )
            editor.stopAndCleanUp()
        self.volumeEditors.clear()

    def imageLaneAdded(self, laneIndex):
        if len(self.laneSummaryTableView.selectedIndexes()) == 0:
            self.laneSummaryTableView.selectRow(laneIndex)
        
        # We don't have any real work to do because this gui initiated the lane addition in the first place
        if self.guiMode != GuiMode.Batch:
            if(len(self.topLevelOperator.DatasetGroup) != laneIndex+1):
                import warnings
                warnings.warn("DataSelectionGui.imageLaneAdded(): length of dataset multislot out of sync with laneindex [%s != %s + 1]" % (len(self.topLevelOperator.Dataset), laneIndex))

    def imageLaneRemoved(self, laneIndex, finalLength):
        # We assume that there's nothing to do here because THIS GUI initiated the lane removal
        if self.guiMode != GuiMode.Batch:
            assert len(self.topLevelOperator.DatasetGroup) == finalLength

    ###########################################
    ###########################################

    def __init__(self, dataSelectionOperator, serializer, guiControlSignal, guiMode=GuiMode.Normal, title="Input Selection"):
        with Tracer(traceLogger):
            super(DataSelectionGui, self).__init__()

            self.title = title

            self._viewerControls = QWidget()
            self.topLevelOperator = dataSelectionOperator
            self.guiMode = guiMode
            self.serializer = serializer
            self.guiControlSignal = guiControlSignal
            self.threadRouter = ThreadRouter(self)

            self._initCentralUic()
            self._initAppletDrawerUic()
            
            self._viewerControlWidgetStack = QStackedWidget(self)

            def handleImageRemoved(multislot, index, finalLength):
                # Remove the viewer for this dataset
                imageSlot = self.topLevelOperator.Image[index]
                if imageSlot in self.volumeEditors.keys():
                    editor = self.volumeEditors[imageSlot]
                    self.viewerStack.removeWidget( editor )
                    editor.stopAndCleanUp()

            self.topLevelOperator.Image.notifyRemove( bind( handleImageRemoved ) )

    def _initCentralUic(self):
        """
        Load the GUI from the ui file into this class and connect it with event handlers.
        """
        # Load the ui file into this class (find it in our own directory)
        localDir = os.path.split(__file__)[0]+'/'
        uic.loadUi(localDir+"/dataSelection.ui", self)

        self._initTableViews()
        self._initViewerStack()
        self.splitter.setSizes( [150, 850] )

    def _initAppletDrawerUic(self):
        """
        Load the ui file for the applet drawer, which we own.
        """
        localDir = os.path.split(__file__)[0]+'/'
        self._drawer = uic.loadUi(localDir+"/dataSelectionDrawer.ui")

    def _initTableViews(self):
        self.fileInfoTabWidget.setTabText( 0, "Summary" )
        self.laneSummaryTableView.setModel( DataLaneSummaryTableModel(self, self.topLevelOperator) )
        self.laneSummaryTableView.dataLaneSelected.connect( self.showDataset )
        self.laneSummaryTableView.addFilesRequested.connect( self.handleAddFiles )
        self.laneSummaryTableView.addStackRequested.connect( self.handleAddStack )
        self.laneSummaryTableView.addByPatternRequested.connect( self.handleAddByPattern )
        self.removeLaneButton.clicked.connect( self.handleRemoveLaneButtonClicked )
        self.laneSummaryTableView.removeLanesRequested.connect( self.handleRemoveLaneButtonClicked )

        self._retained = [] # Retain menus so they don't get deleted
        self._detailViewerWidgets = []
        for roleIndex, role in enumerate(self.topLevelOperator.DatasetRoles.value):
            detailViewer = DataDetailViewerWidget( self, self.topLevelOperator, roleIndex )
            self._detailViewerWidgets.append( detailViewer )

            # Button
            menu = QMenu(parent=self)
            menu.setObjectName("addFileButton_role_{}".format( roleIndex ))
            menu.addAction( "Add File(s)..." ).triggered.connect( partial(self.handleAddFiles, roleIndex) )
            menu.addAction( "Add Volume from Stack..." ).triggered.connect( partial(self.handleAddStack, roleIndex) )
            menu.addAction( "Add Many by Pattern..." ).triggered.connect( partial(self.handleAddByPattern, roleIndex) )
            detailViewer.appendButton.setMenu( menu )
            self._retained.append(menu)
            
            # Context menu            
            detailViewer.datasetDetailTableView.replaceWithFileRequested.connect( partial(self.handleReplaceFile, roleIndex) )
            detailViewer.datasetDetailTableView.replaceWithStackRequested.connect( partial(self.replaceWithStack, roleIndex) )
            detailViewer.datasetDetailTableView.editRequested.connect( partial(self.editDatasetInfo, roleIndex) )
            detailViewer.datasetDetailTableView.resetRequested.connect( partial(self.handleClearDatasets, roleIndex) )

            # Drag-and-drop
            detailViewer.datasetDetailTableView.addFilesRequested.connect( partial( self.addFileNames, roleIndex=roleIndex ) )

            # Selection handling
            def showFirstSelectedDataset( _roleIndex, lanes ):
                if lanes:
                    self.showDataset( lanes[0], _roleIndex )
            detailViewer.datasetDetailTableView.dataLaneSelected.connect( partial(showFirstSelectedDataset, roleIndex) )

            self.fileInfoTabWidget.insertTab(roleIndex, detailViewer, role)
                
        self.fileInfoTabWidget.currentChanged.connect( self.handleSwitchTabs )
        self.fileInfoTabWidget.setCurrentIndex(0)

    def handleSwitchTabs(self, tabIndex ):
        if tabIndex < len(self._detailViewerWidgets):
            roleIndex = tabIndex # If summary tab is moved to the front, change this line.
            detailViewer = self._detailViewerWidgets[roleIndex]
            selectedLanes = detailViewer.datasetDetailTableView.selectedLanes
            if selectedLanes:
                self.showDataset( selectedLanes[0], roleIndex )

    def _initViewerStack(self):
        self.volumeEditors = {}
        self.viewerStack.addWidget( QWidget() )

    def handleRemoveLaneButtonClicked(self):
        """
        The user clicked the "Remove" button.
        Remove the currently selected row(s) from both the GUI and the top-level operator.
        """
        # Figure out which lanes to remove
        selectedIndexes = self.laneSummaryTableView.selectedIndexes()
        rows = set()
        for modelIndex in selectedIndexes:
            rows.add( modelIndex.row() )
        rows.discard( self.laneSummaryTableView.model().rowCount() )

        # Remove in reverse order so row numbers remain consistent
        for row in reversed(sorted(rows)):
            # Remove from the GUI
            self.laneSummaryTableView.model().removeRow(row)
            # Remove from the operator
            finalSize = len(self.topLevelOperator.DatasetGroup) - 1
            self.topLevelOperator.DatasetGroup.removeSlot(row, finalSize)
    
            # The gui and the operator should be in sync
            assert self.laneSummaryTableView.model().rowCount() == len(self.topLevelOperator.DatasetGroup)+1

    def showDataset(self, laneIndex, roleIndex=None):
        if laneIndex == -1:
            self.viewerStack.setCurrentIndex(0)
            return
        
        assert threading.current_thread().name == "MainThread"
        imageSlot = self.topLevelOperator.Image[laneIndex]

        # Create if necessary
        if imageSlot not in self.volumeEditors.keys():
            
            class DatasetViewer(LayerViewerGui):
                def moveToTop(self, roleIndex):
                    opLaneView = self.topLevelOperatorView
                    if not opLaneView.DatasetRoles.ready():
                        return
                    datasetRoles = opLaneView.DatasetRoles.value
                    roleName = datasetRoles[roleIndex]
                    try:
                        layerIndex = [l.name for l in self.layerstack].index(roleName)
                    except ValueError:
                        return
                    else:
                        self.layerstack.selectRow(layerIndex)
                        self.layerstack.moveSelectedToTop()

                def setupLayers(self):
                    opLaneView = self.topLevelOperatorView
                    if not opLaneView.DatasetRoles.ready():
                        return []
                    layers = []
                    datasetRoles = opLaneView.DatasetRoles.value
                    for roleIndex, slot in enumerate(opLaneView.ImageGroup):
                        if slot.ready():
                            roleName = datasetRoles[roleIndex]
                            layer = self.createStandardLayerFromSlot(slot)
                            layer.name = roleName
                            layers.append(layer)
                    return layers

            opLaneView = self.topLevelOperator.getLane(laneIndex)
            layerViewer = DatasetViewer(opLaneView, crosshair=False)
            
            # Maximize the x-y view by default.
            layerViewer.volumeEditorWidget.quadview.ensureMaximized(2)

            self.volumeEditors[imageSlot] = layerViewer
            self.viewerStack.addWidget( layerViewer )
            self._viewerControlWidgetStack.addWidget( layerViewer.viewerControlWidget() )

        # Show the right one
        viewer = self.volumeEditors[imageSlot]
        if roleIndex is not None:
            viewer.moveToTop(roleIndex)
        self.viewerStack.setCurrentWidget( viewer )
        self._viewerControlWidgetStack.setCurrentWidget( viewer.viewerControlWidget() )

    def handleAddFiles(self, roleIndex):
        self.addFiles(roleIndex)

    def handleReplaceFile(self, roleIndex, startingLane):
        self.addFiles(roleIndex, startingLane)

    def addFiles(self, roleIndex, startingLane=None):
        """
        The user clicked the "Add File" button.
        Ask him to choose a file (or several) and add them to both
          the GUI table and the top-level operator inputs.
        """
        # Find the directory of the most recently opened image file
        mostRecentImageFile = PreferencesManager().get( 'DataSelection', 'recent image' )
        if mostRecentImageFile is not None:
            defaultDirectory = os.path.split(mostRecentImageFile)[0]
        else:
            defaultDirectory = os.path.expanduser('~')

        # Launch the "Open File" dialog
        fileNames = self.getImageFileNamesToOpen(defaultDirectory)

        # If the user didn't cancel
        if len(fileNames) > 0:
            PreferencesManager().set('DataSelection', 'recent image', fileNames[0])
            try:
                self.addFileNames(fileNames, roleIndex, startingLane)
            except RuntimeError as e:
                QMessageBox.critical(self, "Error loading file", str(e))

    def handleAddByPattern(self, roleIndex):
        # Find the most recent directory

        # TODO: remove code duplication
        mostRecentDirectory = PreferencesManager().get( 'DataSelection', 'recent mass directory' )
        if mostRecentDirectory is not None:
            defaultDirectory = os.path.split(mostRecentDirectory)[0]
        else:
            defaultDirectory = os.path.expanduser('~')

        fileNames = self.getMass(defaultDirectory)

        # If the user didn't cancel
        if len(fileNames) > 0:
            PreferencesManager().set('DataSelection', 'recent mass directory', os.path.split(fileNames[0])[0])
            try:
                self.addFileNames(fileNames, roleIndex)
            except RuntimeError as e:
                QMessageBox.critical(self, "Error loading file", str(e))


    def getImageFileNamesToOpen(self, defaultDirectory):
        """
        Launch an "Open File" dialog to ask the user for one or more image files.
        """
        extensions = OpDataSelection.SupportedExtensions
        filt = "Image files (" + ' '.join('*.' + x for x in extensions) + ')'
        options = QFileDialog.Options()
        if ilastik_config.getboolean("ilastik", "debug"):
            options |=  QFileDialog.DontUseNativeDialog
        fileNames = QFileDialog.getOpenFileNames( self, "Select Images", 
                                 defaultDirectory, filt, options=options )
        # Convert from QtString to python str
        fileNames = [str(s) for s in fileNames]
        return fileNames

    def _findFirstEmptyLane(self, roleIndex):
        opTop = self.topLevelOperator
        
        # Determine the number of files this role already has
        # Search for the last valid value.
        firstNewLane = 0
        for laneIndex, slot in reversed(zip(range(len(opTop.DatasetGroup)), opTop.DatasetGroup)):
            if slot[roleIndex].ready():
                firstNewLane = laneIndex+1
                break
        return firstNewLane

    def addFileNames(self, fileNames, roleIndex, startingLane=None):
        """
        Add the given filenames to both the GUI table and the top-level operator inputs.
        If startingLane is None, the filenames will be *appended* to the role's list of files.
        """
        infos = []

        if startingLane is None:        
            startingLane = self._findFirstEmptyLane(roleIndex)
            endingLane = startingLane+len(fileNames)-1
        else:
            assert startingLane < len(self.topLevelOperator.DatasetGroup)
            endingLane = startingLane+len(fileNames)-1

        # Assign values to the new inputs we just allocated.
        # The GUI will be updated by callbacks that are listening to slot changes
        for i, filePath in enumerate(fileNames):
            datasetInfo = DatasetInfo()
            cwd = self.topLevelOperator.WorkingDirectory.value
            
            if not areOnSameDrive(filePath,cwd):
                QMessageBox.critical(self, "Drive Error","Data must be on same drive as working directory.")
                return
                
            absPath, relPath = getPathVariants(filePath, cwd)
            
            # Relative by default, unless the file is in a totally different tree from the working directory.
            if len(os.path.commonprefix([cwd, absPath])) > 1:
                datasetInfo.filePath = relPath
            else:
                datasetInfo.filePath = absPath
                
            datasetInfo.nickname = PathComponents(absPath).filenameBase

            h5Exts = ['.ilp', '.h5', '.hdf5']
            if os.path.splitext(datasetInfo.filePath)[1] in h5Exts:
                datasetNames = self.getPossibleInternalPaths( absPath )
                if len(datasetNames) > 0:
                    datasetInfo.filePath += str(datasetNames[0])
                else:
                    raise RuntimeError("HDF5 file %s has no image datasets" % datasetInfo.filePath)

            # Allow labels by default if this gui isn't being used for batch data.
            datasetInfo.allowLabels = ( self.guiMode == GuiMode.Normal )
            infos.append(datasetInfo)

        # if no exception was thrown, set up the operator now
        opTop = self.topLevelOperator
        originalSize = len(opTop.DatasetGroup)
            
        try:
            if len( opTop.DatasetGroup ) < endingLane+1:
                opTop.DatasetGroup.resize( endingLane+1 )
    
            for laneIndex, info in zip(range(startingLane, endingLane+1), infos):
                self.topLevelOperator.DatasetGroup[laneIndex][roleIndex].setValue( info )
        except DatasetConstraintError as ex:
            self.handleDatasetConstraintError(info.filePath, ex)
            opTop.DatasetGroup.resize( originalSize )
        except:
            QMessageBox.critical( self, "Dataset Load Error", "Wasn't able to load your dataset into the workflow.  See console for details." )
            opTop.DatasetGroup.resize( originalSize )
            raise

    def handleDatasetConstraintError(self, filename, ex):
            msg = "Can't use dataset:\n" + \
                  filename + "\n" + \
                  "because it violates a constraint of the {} applet.\n\n".format( ex.appletName ) + \
                  ex.message
            QMessageBox.critical( self, "Unacceptable Dataset", msg )

    def getPossibleInternalPaths(self, absPath):
        datasetNames = []
        # Open the file as a read-only so we can get a list of the internal paths
        with h5py.File(absPath, 'r') as f:
            # Define a closure to collect all of the dataset names in the file.
            def accumulateDatasetPaths(name, val):
                if type(val) == h5py._hl.dataset.Dataset and 3 <= len(val.shape) <= 5:
                    datasetNames.append( '/' + name )
            # Visit every group/dataset in the file
            f.visititems(accumulateDatasetPaths)
        return datasetNames

    def handleAddStack(self, roleIndex):
        self.replaceWithStack(roleIndex, laneIndex=None)

    def replaceWithStack(self, roleIndex, laneIndex):
        """
        The user clicked the "Import Stack Files" button.
        """
        stackDlg = StackFileSelectionWidget(self)
        stackDlg.exec_()
        if stackDlg.result() != QDialog.Accepted :
            return
        files = stackDlg.selectedFiles
        if len(files) == 0:
            return

        info = DatasetInfo()
        info.filePath = "//".join( files )
        prefix = os.path.commonprefix(files)
        info.nickname = PathComponents(prefix).filenameBase + "..."

        # Allow labels by default if this gui isn't being used for batch data.
        info.allowLabels = ( self.guiMode == GuiMode.Normal )
        info.fromstack = True

        originalNumLanes = len(self.topLevelOperator.DatasetGroup)

        if laneIndex is None:
            laneIndex = self._findFirstEmptyLane(roleIndex)
        if len(self.topLevelOperator.DatasetGroup) < laneIndex+1:
            self.topLevelOperator.DatasetGroup.resize(laneIndex+1)

        def importStack():
            self.guiControlSignal.emit( ControlCommand.DisableAll )
            # Serializer will update the operator for us, which will propagate to the GUI.
            try:
                self.serializer.importStackAsLocalDataset( info )
                self.topLevelOperator.DatasetGroup[laneIndex][roleIndex].setValue(info)
            
            finally:
                self.guiControlSignal.emit( ControlCommand.Pop )

        req = Request( importStack )
        req.notify_failed( partial(self.handleFailedStackLoad, files, originalNumLanes ) )
        req.submit()

    @threadRouted
    def handleFailedStackLoad(self, files, originalNumLanes, exc, exc_info):
        if isinstance(exc, DatasetConstraintError):
            filename = files[0] + "\n...\n" + files[-1]
            self.handleDatasetConstraintError( filename, exc )
        else:
            import traceback
            traceback.print_tb(exc_info[2])
            msg = "Failed to load stack due to the following error:\n{}".format( exc )
            msg += "Attempted stack files were:"
            for f in files:
                msg += f + "\n"
            QMessageBox.critical(self, "Failed to load image stack", msg)
        
        self.topLevelOperator.DatasetGroup.resize(originalNumLanes)

    def getMass(self, defaultDirectory):
        # TODO: launch dialog and get files

        # Convert from QtString to python str
        loader = MassFileLoader(defaultDirectory=defaultDirectory)
        loader.exec_()
        if loader.result() == QDialog.Accepted:
            fileNames = [str(s) for s in loader.filenames]
        else:
            fileNames = []
        return fileNames

    def handleClearDatasets(self, roleIndex, selectedRows):
        for row in selectedRows:
            self.topLevelOperator.DatasetGroup[row][roleIndex].disconnect()
        
        # Search for the last lane that has any valid role
        # This would be cleaner in Python 3...
        last_valid = -1
        laneIndexes = range( len(self.topLevelOperator.DatasetGroup) )
        for laneIndex, multislot in reversed(zip(laneIndexes, self.topLevelOperator.DatasetGroup)):
            all_disconnected = True
            for slot in multislot:
                all_disconnected &= not slot.ready()
            if not all_disconnected:
                last_valid = laneIndex
                break
        self.topLevelOperator.DatasetGroup.resize( last_valid+1 )

    def editDatasetInfo(self, roleIndex, laneIndexes):
        editorDlg = DatasetInfoEditorWidget(self, self.topLevelOperator, roleIndex, laneIndexes)
        editorDlg.exec_()
