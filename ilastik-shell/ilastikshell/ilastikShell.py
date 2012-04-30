from PyQt4 import uic
from PyQt4 import Qt
from PyQt4.QtGui import QMainWindow, QWidget, QHBoxLayout, QMenu, \
                        QMenuBar, QFrame, QLabel, QStackedLayout, \
                        QStackedWidget, qApp, QFileDialog, QKeySequence
from PyQt4 import QtCore

import h5py
import traceback
import os

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

        # Menu item: Open Project 
        self.actions.openProjectAction = self._generalMenu.addAction("&Open Project...")
        self.actions.openProjectAction.triggered.connect(parent.onOpenProjectActionTriggered)

        # Menu item: Save Project
        self.actions.saveProjectAction = self._generalMenu.addAction("&Save Project...")
        self.actions.saveProjectAction.triggered.connect(parent.onSaveProjectActionTriggered)

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
        print("ilastikShell.py path: " + ilastikShellFilePath)
        uic.loadUi( ilastikShellFilePath + "/ui/ilastikShell.ui", self )
        self._applets = []
        self.appletBarMapping = {}

        self._menuBar = _ShellMenuBar( self )
        self.setMenuWidget( self._menuBar  )

        for applet in workflow:
            self.addApplet(applet)

        self.appletBar.currentChanged.connect(self.handleAppletBarIndexChange)
        
        # By default, make the splitter control expose a reasonable width of the applet bar
        self.splitter.setSizes([300,1])

    def handleAppletBarIndexChange(self, appletBarIndex):
        if len(self.appletBarMapping) != 0:
            applet_index = self.appletBarMapping[appletBarIndex]
            self.appletStack.setCurrentIndex(applet_index)
            self._menuBar.setCurrentIndex(applet_index)        

    def addApplet( self, applet ):
        self._applets.append(applet)
        applet_index = len(self._applets) - 1
        self.appletStack.addWidget( applet.centralWidget )
        self._menuBar.addAppletMenuWidget( applet.menuWidget )

        # Add all of the applet bar's items to the toolbox widget
        for controlName, controlGuiItem in applet.appletDrawers:
            self.appletBar.addItem(controlGuiItem, controlName)            
            
            # Since each applet can contribute more than one applet bar item, 
            #  we need to keep track of which applet this item is associated with
            self.appletBarMapping[self.appletBar.count()-1] = applet_index

        return applet_index

    def __len__( self ):
        return self.appletBar.count()

    def __getitem__( self, index ):
        return self._applets[index]

    def onOpenProjectActionTriggered(self):
        print "Open Project action triggered"
        projectFileName = QFileDialog.getOpenFileName(
           self, "Open Ilastik Project", os.path.abspath(__file__), "Ilastik project files (*ilp)")
        
        # If the user cancelled, stop now
        if projectFileName.isNull():
            return
        
        # Convert from QString to str
        projectFileName = str(projectFileName)
        print "Opening Project: " + projectFileName

        # Open the file as an HDF5 file
        h5File = h5py.File(projectFileName, "r") # Should be no need to write

        try:            
            # Applet serializable items are given the whole file (root group) for now
            for applet in self._applets:
                for item in applet.dataSerializers:
                    item.deserializeFromHdf5(h5File)
        except:
            print "Project Open Action failed due to the following exception:"
            traceback.print_exc()
            
            print "Aborting Project Open Action"
            for applet in self._applets:
                for item in applet.dataSerializers:
                    item.unload()
        
        h5File.close()
    
    def onSaveProjectActionTriggered(self):
        print "Save Project action triggered"
        projectFileName = QFileDialog.getSaveFileName(
           self, "Save Ilastik Project", os.path.abspath(__file__), "Ilastik project files (*ilp)")
        
        # If the user cancelled, stop now
        if projectFileName.isNull():
            return
        
        # Convert from QString to str
        projectFileName = str(projectFileName)
        print "Saving Project: " + projectFileName

        # Open the file as an HDF5 file
        # For now, always start from scratch ("w").
        # In the future, maybe check the file's existing data to see if it really needs to be overwritten
        h5File = h5py.File(projectFileName, "w") 

        try:        
            # Applet serializable items are given the whole file (root group) for now
            for applet in self._applets:
                for item in applet.dataSerializers:
                    item.serializeToHdf5(h5File)
        except:
            print "Project Save Action failed due to the following exception:"
            traceback.print_exc()            

        h5File.close()
        
    def onQuitActionTriggered(self):
        print "Quit Action Triggered"
        
        # Check each of the serializable items to see if the user might need to save first
        unSavedDataExists = False
        for applet in self._applets:
            for item in applet.dataSerializers:
                if unSavedDataExists:
                    break
                else:
                    unSavedDataExists = item.isDirty()

        if unSavedDataExists:
            print "TODO: Prompt user to save his data before exiting."
        
        qApp.quit()
    
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

