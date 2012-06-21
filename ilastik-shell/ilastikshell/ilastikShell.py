from PyQt4 import uic
from PyQt4 import Qt
from PyQt4.QtGui import QMainWindow, QWidget, QHBoxLayout, QMenu, \
                        QMenuBar, QFrame, QLabel, QStackedLayout, \
                        QStackedWidget, qApp, QFileDialog, QKeySequence, QMessageBox, \
                        QStandardItemModel, QTreeWidgetItem, QTreeWidget, QFont, \
                        QBrush, QColor, QAbstractItemView
from PyQt4 import QtCore

import h5py
import traceback
import os
from functools import partial

from versionManager import VersionManager
from utility import bind
from lazyflow.graph import MultiOutputSlot

import sys
import logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))

import applet

class ShellActions(object):
    """
    The shell provides the applet constructors with access to his GUI actions.
    They are provided in this class.
    """
    def __init__(self):
        self.openProjectAction = None
        self.saveProjectAction = None
        self.QuitAction = None

class SideSplitterSizePolicy(object):
    Manual = 0
    AutoCurrentDrawer = 1
    AutoLargestDrawer = 2

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
    def __init__( self, workflow = [], parent = None, flags = QtCore.Qt.WindowFlags(0), sideSplitterSizePolicy=SideSplitterSizePolicy.Manual ):
        QMainWindow.__init__(self, parent = parent, flags = flags )

        self._sideSplitterSizePolicy = sideSplitterSizePolicy
        
        import inspect, os
        ilastikShellFilePath = os.path.dirname(inspect.getfile(inspect.currentframe()))
        uic.loadUi( ilastikShellFilePath + "/ui/ilastikShell.ui", self )
        self._applets = []
        self.appletBarMapping = {}

        self._menuBar = _ShellMenuBar( self )
        self.setMenuWidget( self._menuBar  )

        for applet in workflow:
            self.addApplet(applet)

        self.appletBar.expanded.connect(self.handleAppleBarItemExpanded)
        self.appletBar.clicked.connect(self.handleAppletBarClick)
        self.appletBar.setVerticalScrollMode( QAbstractItemView.ScrollPerPixel )
        
        # By default, make the splitter control expose a reasonable width of the applet bar
        self.mainSplitter.setSizes([300,1])
        
        self.currentAppletIndex = 0
        self.currentProjectFile = None
        
        self.currentImageIndex = -1
        self.populatingImageSelectionCombo = False
        self.imageSelectionCombo.currentIndexChanged.connect( self.changeCurrentInputImageIndex )
        
        self.enableWorkflow = False # Global mask applied to all applets
        self._controlCmds = []      # Track the control commands that have been issued by each applet so they can be popped.
        self._disableCounts = []    # Controls for each applet can be disabled by his peers.
                                    # No applet can be enabled unless his disableCount == 0
        
    def show(self):
        """
        Show the window, and enable/disable controls depending on whether or not a project file present.
        """
        super(IlastikShell, self).show()
        self.enableWorkflow = (self.currentProjectFile != None)
        self.updateAppletControlStates()
        if self._sideSplitterSizePolicy == SideSplitterSizePolicy.Manual:
            self.autoSizeSideSplitter( SideSplitterSizePolicy.AutoLargestDrawer )
        else:
            self.autoSizeSideSplitter( SideSplitterSizePolicy.AutoCurrentDrawer )

    def setImageNameListSlot(self, multiSlot):
        assert type(multiSlot) == MultiOutputSlot
        self.imageNamesSlot = multiSlot
        
        def insertImageName( index, slot ):
            self.imageSelectionCombo.setItemText( index, slot.value )
            if self.currentImageIndex == -1:
                self.changeCurrentInputImageIndex(index)

        def handleImageNameSlotInsertion(multislot, index):
            assert multislot == self.imageNamesSlot
            self.populatingImageSelectionCombo = True
            self.imageSelectionCombo.insertItem(index, "uninitialized")
            self.populatingImageSelectionCombo = False
            multislot[index].notifyDirty( bind( insertImageName, index) )

        multiSlot.notifyInserted( bind(handleImageNameSlotInsertion) )

        def handleImageNameSlotRemoval(multislot, index):
            # Simply remove the combo entry, which causes the currentIndexChanged signal to fire if necessary.
            self.imageSelectionCombo.removeItem(index)
            if len(multislot) == 0:
                self.changeCurrentInputImageIndex(-1)
        multiSlot.notifyRemove( bind(handleImageNameSlotRemoval) )

    def changeCurrentInputImageIndex(self, newImageIndex):
        if newImageIndex != self.currentImageIndex \
        and self.populatingImageSelectionCombo == False:
            if newImageIndex != -1:
                try:
                    # Accessing the image name value will throw if it isn't properly initialized
                    self.imageNamesSlot[newImageIndex].value
                except:
                    # Revert to the original image index.
                    if self.currentImageIndex != -1:
                        self.imageSelectionCombo.setCurrentIndex(self.currentImageIndex)
                    return

            # Alert each central widget and viewer control widget that the image selection changed
            for i in range( len(self._applets) ):
                self._applets[i].gui.setImageIndex(newImageIndex)
                
            self.currentImageIndex = newImageIndex


    def handleAppleBarItemExpanded(self, modelIndex):
        """
        The user wants to view a different applet bar item.
        """
        drawerIndex = modelIndex.row()
        self.setSelectedAppletDrawer(drawerIndex)
    
    def setSelectedAppletDrawer(self, drawerIndex):
        """
        Show the correct applet central widget, viewer control widget, and applet drawer widget for this drawer index.
        """
        if self.currentAppletIndex != drawerIndex:
            self.currentAppletIndex = drawerIndex
            # Collapse all drawers in the applet bar...
            self.appletBar.collapseAll()
            # ...except for the newly selected item.
            self.appletBar.expand( self.getModelIndexFromDrawerIndex(drawerIndex) )
            
            if len(self.appletBarMapping) != 0:
                # Determine which applet this drawer belongs to
                applet_index = self.appletBarMapping[drawerIndex]

                # Select the appropriate central widget, menu widget, and viewer control widget for this applet
                self.appletStack.setCurrentIndex(applet_index)
                self._menuBar.setCurrentIndex(applet_index)
                self.viewerControlStack.setCurrentIndex(applet_index)
                
                self.autoSizeSideSplitter( self._sideSplitterSizePolicy )

    def getModelIndexFromDrawerIndex(self, drawerIndex):
        drawerTitleItem = self.appletBar.invisibleRootItem().child(drawerIndex)
        return self.appletBar.indexFromItem(drawerTitleItem)
                
    def autoSizeSideSplitter(self, sizePolicy):
        if sizePolicy == SideSplitterSizePolicy.Manual:
            # In manual mode, don't resize the splitter at all.
            return
        
        if sizePolicy == SideSplitterSizePolicy.AutoCurrentDrawer:
            # Get the height of the current applet drawer
            rootItem = self.appletBar.invisibleRootItem()
            appletDrawerItem = rootItem.child(self.currentAppletIndex).child(0)
            appletDrawerWidget = self.appletBar.itemWidget(appletDrawerItem, 0)
            appletDrawerHeight = appletDrawerWidget.frameSize().height()

        if sizePolicy == SideSplitterSizePolicy.AutoLargestDrawer:
            appletDrawerHeight = 0
            # Get the height of the largest drawer in the bar
            for drawerIndex in range( len(self.appletBarMapping) ):
                rootItem = self.appletBar.invisibleRootItem()
                appletDrawerItem = rootItem.child(drawerIndex).child(0)
                appletDrawerWidget = self.appletBar.itemWidget(appletDrawerItem, 0)
                appletDrawerHeight = max( appletDrawerHeight, appletDrawerWidget.frameSize().height() )
        
        # Get total height of the titles in the applet bar (not the widgets)
        firstItem = self.appletBar.invisibleRootItem().child(0)
        titleHeight = self.appletBar.visualItemRect(firstItem).size().height()
        numDrawers = len(self.appletBarMapping)
        totalTitleHeight = numDrawers * titleHeight    
    
        # Auto-size the splitter height based on the height of the applet bar.
        totalSplitterHeight = sum(self.sideSplitter.sizes())
        appletBarHeight = totalTitleHeight + appletDrawerHeight + 10 # Add a small margin so the scroll bar doesn't appear
        self.sideSplitter.setSizes([appletBarHeight, totalSplitterHeight-appletBarHeight])

    def handleAppletBarClick(self, modelIndex):
        # If the user clicks on a top-level item, automatically expand it.
        if modelIndex.parent() == self.appletBar.rootIndex():
            self.appletBar.expand(modelIndex)
        else:
            self.appletBar.setCurrentIndex( modelIndex.parent() )

    def addApplet( self, app ):
        assert isinstance( app, applet.Applet ), "Applets must inherit from Applet base class."
        assert app.base_initialized, "Applets must call Applet.__init__ upon construction."
        
        self._applets.append(app)
        applet_index = len(self._applets) - 1
        self.appletStack.addWidget( app.gui.centralWidget() )
        self._menuBar.addAppletMenuWidget( app.gui.menuWidget() )
        
        # Viewer controls are optional. If the applet didn't provide one, create an empty widget for him.
        if app.gui.viewerControlWidget() is None:
            self.viewerControlStack.addWidget( QWidget(parent=self) )
        else:
            self.viewerControlStack.addWidget( app.gui.viewerControlWidget() )

        # Add rows to the applet bar model
        rootItem = self.appletBar.invisibleRootItem()

        # Add all of the applet bar's items to the toolbox widget
        for controlName, controlGuiItem in app.gui.appletDrawers():
            appletNameItem = QTreeWidgetItem( self.appletBar, QtCore.QStringList( controlName ) )
            appletNameItem.setFont( 0, QFont("Ubuntu", 14) )
            drawerItem = QTreeWidgetItem(appletNameItem)
            drawerItem.setSizeHint( 0, controlGuiItem.frameSize() )
#            drawerItem.setBackground( 0, QBrush( QColor(224, 224, 224) ) )
#            drawerItem.setForeground( 0, QBrush( QColor(0,0,0) ) )
            self.appletBar.setItemWidget( drawerItem, 0, controlGuiItem )

            # Since each applet can contribute more than one applet bar item,
            #  we need to keep track of which applet this item is associated with
            self.appletBarMapping[rootItem.childCount()-1] = applet_index

        app.guiControlSignal.connect( bind(self.handleAppletGuiControlSignal, applet_index) )
        self._disableCounts.append(0)
        self._controlCmds.append( [] )
        
        return applet_index

    def handleAppletGuiControlSignal(self, applet_index, command=applet.ControlCommand.DisableAll):
        """
        Applets fire a signal when they want other applet GUIs to be disabled.
        This function handles the signal.
        Each signal is treated as a command to disable other applets.
        A special command, Pop, undoes the applet's most recent command (i.e. re-enables the applets that were disabled).
        If an applet is disabled twice (e.g. by two different applets), then it won't become enabled again until both commands have been popped.
        """
        if command == applet.ControlCommand.Pop:
            command = self._controlCmds[applet_index].pop()
            step = -1 # Since we're popping this command, we'll subtract from the disable counts
        else:
            step = 1
            self._controlCmds[applet_index].append( command ) # Push command onto the stack so we can pop it off when the applet isn't busy any more

        # Increase the disable count for each applet that is affected by this command.
        for index, count in enumerate(self._disableCounts):
            if (command == applet.ControlCommand.DisableAll) \
            or (command == applet.ControlCommand.DisableDownstream and index > applet_index) \
            or (command == applet.ControlCommand.DisableUpstream and index < applet_index) \
            or (command == applet.ControlCommand.DisableSelf and index == applet_index):
                self._disableCounts[index] += step

        self.updateAppletControlStates()

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
                self.enableWorkflow = False
                self.updateAppletControlStates()
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
                if os.path.exists(projectFilePath):
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
            # Applet serializable items are given the whole file (root group)
            for applet in self._applets:
                for item in applet.dataSerializers:
                    assert item.base_initialized, "AppletSerializer subclasses must call AppletSerializer.__init__ upon construction."
                    item.deserializeFromHdf5(self.currentProjectFile, projectFilePath)

            # Now that a project is loaded, the user is allowed to save
            self._menuBar.actions.saveProjectAction.setEnabled(True)
    
            # Enable all the applet controls
            self.enableWorkflow = True
            self.updateAppletControlStates()

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
                    assert item.base_initialized, "AppletSerializer subclasses must call AppletSerializer.__init__ upon construction."
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
    
    def updateAppletControlStates(self):
        """
        Enable or disable all controls of all applets according to their disable count.
        """
        for index, applet in enumerate(self._applets):
            enabled = self._disableCounts[index] == 0

            # Apply to the applet central widget
            applet.gui.centralWidget().enableControls( enabled and self.enableWorkflow )
            
            # Apply to the applet bar drawers
            for appletName, appletGui in applet.gui.appletDrawers():
                appletGui.enableControls( enabled and self.enableWorkflow )

#    def scrollToTop(self):
#        #self.appletBar.verticalScrollBar().setValue( 0 )
#
#        self.appletBar.setVerticalScrollMode( QAbstractItemView.ScrollPerPixel )
#        
#        from PyQt4.QtCore import QPropertyAnimation, QVariant
#        animation = QPropertyAnimation( self.appletBar.verticalScrollBar(), "value", self )
#        animation.setDuration(2000)
#        #animation.setStartValue( QVariant( self.appletBar.verticalScrollBar().minimum() ) )
#        animation.setEndValue( QVariant( self.appletBar.verticalScrollBar().maximum() ) )
#        animation.start()
#
#        #self.appletBar.setVerticalScrollMode( QAbstractItemView.ScrollPerItem )

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

