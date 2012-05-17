from PyQt4 import uic
from PyQt4 import Qt
from PyQt4.QtGui import QMainWindow, QWidget, QHBoxLayout, QMenu, \
                        QMenuBar, QFrame, QLabel, QStackedLayout, \
                        QStackedWidget, qApp, QFileDialog, QKeySequence, QMessageBox, \
                        QStandardItemModel, QTreeWidgetItem, QTreeWidget, QFont, \
                        QBrush, QColor
from PyQt4 import QtCore

import h5py
import traceback
import os
from functools import partial

from utility import VersionManager
from lazyflow.graph import MultiOutputSlot

import logging
logger = logging.getLogger(__name__)

class ShellActions(object):
    """
    The shell provides the applet constructors with access to his GUI actions.
    They are provided in this class.
    """
    def __init__(self):
        self.openProjectAction = None
        self.saveProjectAction = None
        self.QuitAction = None

class _ShellMenuBar( QWidget ):
    """
    The main window menu bar.
    Only the "General" menu is provided by the shell.
    Applets can add their own custom menus, which appear next to the General menu.
    """
    def __init__( self, parent ):
        QWidget.__init__(self, parent=parent)

        # Any actions we add to the shell GUI will be stored in this member
        self.actions = ShellActions()
        
        # Our menu will consist of two pieces:
        #  - A "general" menu that is always visible on the left
        #  - An "applet" menu-ish widget that is visible on the right
        # Our top-level layout is an HBox for holding the two sections
        self._layout = QHBoxLayout( self )
        self._layout.setSpacing(0)
        self.setLayout( self._layout )

        self.initGeneralMenu(parent)

        # Each applet can specify whatever he wants in the menu (not necessarily a QMenuBar)
        # Create a stacked widget to contain the applet menu-ish widgets
        #  and add it to the top-level HBox layout
        self._appletMenuStack = QStackedWidget(self)
        self._layout.addWidget( self._appletMenuStack, 1 )
        
    def initGeneralMenu(self, parent):
        # Create a menu for "General" (non-applet) actions
        self._generalMenu = QMenu("General", self)

        # Menu item: New Project 
        self.actions.newProjectAction = self._generalMenu.addAction("&New Project...")
        self.actions.newProjectAction.triggered.connect(parent.onNewProjectActionTriggered)

        # Menu item: Open Project 
        self.actions.openProjectAction = self._generalMenu.addAction("&Open Project...")
        self.actions.openProjectAction.triggered.connect(parent.onOpenProjectActionTriggered)

        # Menu item: Save Project
        self.actions.saveProjectAction = self._generalMenu.addAction("&Save Project...")
        self.actions.saveProjectAction.triggered.connect(parent.onSaveProjectActionTriggered)
        # Can't save until a project is loaded for the first time
        self.actions.saveProjectAction.setEnabled(False)

        # Menu item: Quit
        self.actions.quitAction = self._generalMenu.addAction("&Quit")
        self.actions.quitAction.triggered.connect(parent.onQuitActionTriggered)
        self.actions.quitAction.setShortcut( QKeySequence.Quit )

        # Create a menu bar widget and populate it with the general menu
        self._generalMenuBar = QMenuBar(self)
        self._generalMenuBar.setNativeMenuBar( False ) # Native menus are broken on Ubuntu at the moment
        self._generalMenuBar.addMenu(self._generalMenu)
        self._layout.addWidget( self._generalMenuBar )
        
    def addAppletMenuWidget( self, appletMenuWidget ):
        # Add this widget to the applet menu area stack
        self._appletMenuStack.addWidget(appletMenuWidget)

    def setCurrentIndex( self, index ):
        self._appletMenuStack.setCurrentIndex( index )
    
    def getCurrentIndex(self):
        return self._layout.currentWidget()

class IlastikShell( QMainWindow ):    
    """
    The GUI's main window.  Simply a standard 'container' GUI for one or more applets.
    """
    def __init__( self, workflow = [], parent = None, flags = QtCore.Qt.WindowFlags(0) ):
        QMainWindow.__init__(self, parent = parent, flags = flags )
        import inspect, os
        ilastikShellFilePath = os.path.dirname(inspect.getfile(inspect.currentframe()))
        uic.loadUi( ilastikShellFilePath + "/ui/ilastikShell.ui", self )
        self._applets = []
        self.appletBarMapping = {}

        self._menuBar = _ShellMenuBar( self )
        self.setMenuWidget( self._menuBar  )

        for applet in workflow:
            self.addApplet(applet)

        self.appletBar.expanded.connect(self.handleAppletBarIndexChange)
        self.appletBar.clicked.connect(self.handleAppletBarClick)
        
        # By default, make the splitter control expose a reasonable width of the applet bar
        self.mainSplitter.setSizes([300,1])
        
        self.currentAppletIndex = 0
        self.currentProjectFile = None
        
        self.currentImageIndex = None
        self.imageSelectionCombo.currentIndexChanged.connect( self.changeCurrentInputImageIndex )
        
    def show(self):
        """
        Show the window, and enable/disable controls depending on whether or not a project file present.
        """
        super(IlastikShell, self).show()
        self.enableControls(self.currentProjectFile != None)
        self.autoSizeSideSplitter()

    def setImageNameListSlot(self, multiSlot):
        assert type(multiSlot) == MultiOutputSlot
        #multiSlot.operator.notifyConfigured( self.handleImageListModified )
        multiSlot.notifyInserted( self.handleImageListModified )
        multiSlot.notifyRemove( self.handleImageListModified )
        multiSlot.notifyResized( self.handleImageListModified )
        self.imageNamesSlot = multiSlot
        
    def handleImageListModified(self,  multiSlot, ignored, newListSize):
        # assert multiSlot == self.imageNamesSlot
        # Regenerate the image selection combo.
        self.imageSelectionCombo.clear()
        
        # Set the combo text for every slot we know so far
        for i, subSlot in enumerate(self.imageNamesSlot):
            try:
                self.imageSelectionCombo.addItem(subSlot.value)
            except AssertionError:
                # Currently graph.py asserts if the item has no value.
                # In the future this may be changed to some other exception.
                self.imageSelectionCombo.addItem('uninitialized')
            except:
                # If we got here, modify the except statement above to catch the appropriate exception type.
                assert False

            # Update the combo text for any subslots that get updated in the future           
            def handleNewImageName(index, slot):
                text = slot.value
                if text is not None:
                    self.imageSelectionCombo.setItemText( index, slot.value )            
            subSlot.notifyConnect( partial(handleNewImageName, i) )
        
        # Change the image index if it's too high for the new list
        self.changeCurrentInputImageIndex( min( len(self.imageNamesSlot), self.currentImageIndex ) )

    def changeCurrentInputImageIndex(self, newImageIndex):
        if newImageIndex != self.currentImageIndex:
            try:
                # Accessing the image name value will throw if it isn't properly initialized
                self.imageNamesSlot[newImageIndex].value

                # Alert each central widget and viewer control widget that the image selection changed
                for i in range( len(self._applets) ):
                    self._applets[i].setImageIndex(newImageIndex)
            except:
                pass

    def handleAppletBarIndexChange(self, modelIndex):
        """
        The user wants to view a different applet bar item.
        """
        appletBarIndex = modelIndex.row()

        if self.currentAppletIndex != appletBarIndex:
            self.currentAppletIndex = appletBarIndex
            # Collapse all drawers in the applet bar...
            self.appletBar.collapseAll()
            # ...except for the newly selected item.
            self.appletBar.expand(modelIndex)
            
            if len(self.appletBarMapping) != 0:
                # Determine which applet this drawer belongs to
                applet_index = self.appletBarMapping[appletBarIndex]

                # Select the appropriate central widget, menu widget, and viewer control widget for this applet
                self.appletStack.setCurrentIndex(applet_index)
                self._menuBar.setCurrentIndex(applet_index)
                self.viewerControlStack.setCurrentIndex(applet_index)
                
                self.autoSizeSideSplitter()
                
    def autoSizeSideSplitter(self):
        # Get total height of the titles in the applet bar (not the widgets)
        firstItem = self.appletBar.invisibleRootItem().child(0)
        titleHeight = self.appletBar.visualItemRect(firstItem).size().height()
        numDrawers = len(self.appletBarMapping)
        totalTitleHeight = numDrawers * titleHeight
    
        # Get the height of the current applet drawer               
        rootItem = self.appletBar.invisibleRootItem()
        appletDrawerItem = rootItem.child(self.currentAppletIndex).child(0)
        appletDrawerWidget = self.appletBar.itemWidget(appletDrawerItem, 0)
        appletDrawerHeight = appletDrawerWidget.frameSize().height()
    
        # Auto-size the splitter height based on the height of the applet bar.
        totalSplitterHeight = sum(self.sideSplitter.sizes())
        appletBarHeight = totalTitleHeight + appletDrawerHeight + 10 # Add a small margin so the scroll bar doesn't appear
        self.sideSplitter.setSizes([appletBarHeight, totalSplitterHeight-appletBarHeight])

    def handleAppletBarClick(self, modelIndex):
        # If the user clicks on a top-level item, automatically expand it.
        if modelIndex.parent() == self.appletBar.rootIndex():
            self.appletBar.expand(modelIndex)

    def addApplet( self, applet ):
        self._applets.append(applet)
        applet_index = len(self._applets) - 1
        self.appletStack.addWidget( applet.centralWidget )
        self._menuBar.addAppletMenuWidget( applet.menuWidget )
        
        # Viewer controls are optional.
        if applet.viewerControlWidget is None:
            self.viewerControlStack.addWidget( QWidget(parent=self) )
        else:
            self.viewerControlStack.addWidget( applet.viewerControlWidget )

        # Add rows to the applet bar model
        rootItem = self.appletBar.invisibleRootItem()

        # Add all of the applet bar's items to the toolbox widget
        for controlName, controlGuiItem in applet.appletDrawers:
            appletNameItem = QTreeWidgetItem( QtCore.QStringList( controlName ) )
            appletNameItem.setFont( 0, QFont("Ubuntu", 16) )
            appletNameItem.setBackground( 0, QBrush( QColor( 0, 0, 128 ) ) ) # Dark blue
            appletNameItem.setForeground( 0, QBrush( QColor( 255, 255, 255) ) ) # White
            drawerItem = QTreeWidgetItem()
            drawerItem.setSizeHint( 0, controlGuiItem.frameSize() )
            appletNameItem.addChild( drawerItem )
            rootItem.addChild( appletNameItem )
            self.appletBar.setItemWidget( drawerItem, 0, controlGuiItem )

            # Since each applet can contribute more than one applet bar item,
            #  we need to keep track of which applet this item is associated with
            self.appletBarMapping[rootItem.childCount()-1] = applet_index

        return applet_index

    def __len__( self ):
        return self.appletBar.count()

    def __getitem__( self, index ):
        return self._applets[index]
    
    def ensureNoCurrentProject(self):
        projectClosed = True
        if self.currentProjectFile is not None:
            if self.isProjectDataDirty():
                message = "Your current project is about to be closed, but it has unsaved changes which will be lost.\n"
                message += "Are you sure you want to proceed?"
                buttons = QMessageBox.Yes | QMessageBox.Cancel
                response = QMessageBox.warning(self, "Discard unsaved changes?", message, buttons, defaultButton=QMessageBox.Cancel)
                projectClosed = (response == QMessageBox.Yes)

            if projectClosed:                
                self.unloadAllApplets()
                self.currentProjectFile.close()
                self.currentProjectFile = None
                self.enableControls(False)
        return projectClosed
    
    def onNewProjectActionTriggered(self):
        logger.debug("New Project action triggered")
        
        # Make sure the user is finished with the currently open project
        if not self.ensureNoCurrentProject():
            return
        
        fileSelected = False
        while not fileSelected:
            projectFilePath = QFileDialog.getSaveFileName(
               self, "Create Ilastik Project", os.path.abspath(__file__), "Ilastik project files (*.ilp)")
            
            # If the user cancelled, stop now
            if projectFilePath.isNull():
                return
    
            projectFilePath = str(projectFilePath)
            fileSelected = True
            
            # Add extension if necessary
            fileExtension = os.path.splitext(projectFilePath)[1].lower()
            if fileExtension != '.ilp':
                projectFilePath += ".ilp"
                # Since we changed the file path, we need to re-check if we're overwriting an existing file.
                message = "A file named '" + projectFilePath + "' already exists in this location.\n"
                message += "Are you sure you want to overwrite it with a blank project?"
                buttons = QMessageBox.Yes | QMessageBox.Cancel
                response = QMessageBox.warning(self, "Overwrite existing project?", message, buttons, defaultButton=QMessageBox.Cancel)
                if response == QMessageBox.Cancel:
                    # Try again...
                    fileSelected = False

        # Create the blank project file
        h5File = h5py.File(projectFilePath, "w")
        h5File.create_dataset("ilastikVersion", data=VersionManager.CurrentIlastikVersion)
        
        self.loadProject(h5File, projectFilePath)

    def onOpenProjectActionTriggered(self):
        logger.debug("Open Project action triggered")

        # Make sure the user is finished with the currently open project
        if not self.ensureNoCurrentProject():
            return

        projectFilePath = QFileDialog.getOpenFileName(
           self, "Open Ilastik Project", os.path.abspath(__file__), "Ilastik project files (*.ilp)")

        # If the user canceled, stop now        
        if projectFilePath.isNull():
            return

        projectFilePath = str(projectFilePath)
        
        self.openProjectFile(projectFilePath)
    
    def openProjectFile(self, projectFilePath):
        logger.info("Opening Project: " + projectFilePath)

        # Open the file as an HDF5 file
        hdf5File = h5py.File(projectFilePath)
        self.loadProject(hdf5File, projectFilePath)
    
    def loadProject(self, hdf5File, projectFilePath):
        """
        Load the data from the given hdf5File (which should already be open).
        """
        assert self.currentProjectFile is None
        
        # Save this as the current project
        self.currentProjectFile = hdf5File
        self.currentProjectPath = projectFilePath
        try:            
            # Applet serializable items are given the whole file (root group) for now
            for applet in self._applets:
                for item in applet.dataSerializers:
                    item.deserializeFromHdf5(self.currentProjectFile, projectFilePath)

            # Now that a project is loaded, the user is allowed to save
            self._menuBar.actions.saveProjectAction.setEnabled(True)
    
            # Enable all the applet controls        
            self.enableControls(True)

        except:
            logger.error("Project Open Action failed due to the following exception:")
            traceback.print_exc()
            
            logger.error("Aborting Project Open Action")
            self.unloadAllApplets()

    def unloadAllApplets(self):
        """
        Unload all applets into a blank state.
        """
        for applet in self._applets:
            for item in applet.dataSerializers:
                item.unload()
    
    def onSaveProjectActionTriggered(self):
        logger.debug("Save Project action triggered")
        
        assert self.currentProjectFile != None
        assert self.currentProjectPath != None

        try:        
            # Applet serializable items are given the whole file (root group) for now
            for applet in self._applets:
                for item in applet.dataSerializers:
                    item.serializeToHdf5(self.currentProjectFile, self.currentProjectPath)
        except:
            logger.error("Project Save Action failed due to the following exception:")
            traceback.print_exc()            

        # Flush any changes we made to disk, but don't close the file.
        self.currentProjectFile.flush()
        
    def onQuitActionTriggered(self):
        """
        The user wants to quit the application.
        Check his project for unsaved data and ask if he really means it.
        """
        logger.info("Quit Action Triggered")
        
        if self.isProjectDataDirty():
            message = "Your project has unsaved data.  Are you sure you want to discard your changes and quit?"
            buttons = QMessageBox.Discard | QMessageBox.Cancel
            response = QMessageBox.warning(self, "Discard unsaved changes?", message, buttons, defaultButton=QMessageBox.Cancel)
            if response == QMessageBox.Cancel:
                return

        if self.currentProjectFile is not None:
            self.currentProjectFile.close()
        self.currentProjectFile = None

        qApp.quit()

    def isProjectDataDirty(self):
        """
        Check all serializable items in our workflow if they have any unsaved data.
        """
        if self.currentProjectFile is None:
            return False

        unSavedDataExists = False
        for applet in self._applets:
            for item in applet.dataSerializers:
                if unSavedDataExists:
                    break
                else:
                    unSavedDataExists = item.isDirty()
        return unSavedDataExists
    
    def enableControls(self, enabled):
        """
        Enable or disable all controls of all applets.
        """
        for applet in self._applets:
            # Apply to the applet central widget
            applet.centralWidget.enableControls(enabled)
            # Apply to the applet bar drawers
            for appletName, appletGui in applet.appletDrawers:
                appletGui.enableControls(enabled)
#
# Simple standalone test for the IlastikShell
#
if __name__ == "__main__":
    #make the program quit on Ctrl+C
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    from PyQt4.QtGui import QApplication
    import sys
    from applet import Applet

    qapp = QApplication(sys.argv)
    
    # Create some simple applets to load
    defaultApplet = Applet()
    trackingApplet = Applet("Tracking")

    # Normally applets would provide their own menu items,
    # but for this test we'll add them here (i.e. from the outside).
    defaultApplet._menuWidget = QMenuBar()
    defaultApplet._menuWidget.setNativeMenuBar( False ) # Native menus are broken on Ubuntu at the moment
    defaultMenu = QMenu("Default Applet", defaultApplet._menuWidget)
    defaultMenu.addAction("Default Action 1")
    defaultMenu.addAction("Default Action 2")
    defaultApplet._menuWidget.addMenu(defaultMenu)
    
    trackingApplet._menuWidget = QMenuBar()
    trackingApplet._menuWidget.setNativeMenuBar( False ) # Native menus are broken on Ubuntu at the moment
    trackingMenu = QMenu("Tracking Applet", trackingApplet._menuWidget)
    trackingMenu.addAction("Tracking Options...")
    trackingMenu.addAction("Track...")
    trackingApplet._menuWidget.addMenu(trackingMenu)

    # Create a shell with our test applets    
    shell = IlastikShell( [defaultApplet, trackingApplet] )

    shell.show()
    qapp.exec_()

