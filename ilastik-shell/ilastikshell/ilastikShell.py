from PyQt4 import uic
from PyQt4 import Qt
from PyQt4.QtGui import QMainWindow, QWidget, QHBoxLayout, QMenu, \
                        QMenuBar, QFrame, QLabel, QStackedLayout, QStackedWidget, qApp
from PyQt4 import QtCore

class _ShellMenuBar( QWidget ):
    def __init__( self, parent=None ):
        QWidget.__init__(self, parent=parent)
        
        # Our menu will consist of two pieces:
        #  - A "general" menu that is always visible on the left
        #  - An "applet" menu-ish widget that is visible on the right
        # Our top-level layout is an HBox for holding the two sections        
        self._layout = QHBoxLayout( self )
        self._layout.setSpacing(0)
        self.setLayout( self._layout )
        
        # Create the general menu bar and add it to the layout
        self._generalMenuBar = QMenuBar(self)
        self._generalMenuBar.setNativeMenuBar( False ) # Native menus are broken on Ubuntu at the moment
        self._generalMenu = QMenu("General", self)
        self._quitAction = self._generalMenu.addAction("Quit")
        self._generalMenuBar.addMenu(self._generalMenu)
        self._layout.addWidget( self._generalMenuBar )

        # Each applet can specify whatever he wants in the menu (not necessarily a QMenuBar)
        # Create a stacked widget to contain the applet menu-ish widgets
        #  and add it to the top-level HBox layout
        self._appletMenuStack = QStackedWidget(self)
        self._layout.addWidget( self._appletMenuStack, 1 )
        
        # Set up behavior for the quit action (from the shell menu)
        self._quitAction.triggered.connect(qApp.quit)

    def addAppletMenuWidget( self, appletMenuWidget ):
        # Add this widget to the applet menu area stack
        self._appletMenuStack.addWidget(appletMenuWidget)

    def setCurrentIndex( self, index ):
        self._appletMenuStack.setCurrentIndex( index )
    
    def getCurrentIndex(self):
        return self._layout.currentWidget()

class IlastikShell( QMainWindow ):
    def __init__( self, workflow = [], parent = None, flags = QtCore.Qt.WindowFlags(0) ):
        QMainWindow.__init__(self, parent = parent, flags = flags )
        import inspect, os
        ilastikShellFilePath = os.path.dirname(inspect.getfile(inspect.currentframe()))
        print("ilastikShell.py path: " + ilastikShellFilePath)
        uic.loadUi( ilastikShellFilePath + "/ui/ilastikShell.ui", self )
        self._applets = []

        self._menuBar = _ShellMenuBar( self )
        self.setMenuWidget( self._menuBar  )

        for applet in workflow:
            self.addApplet(applet)

        self.appletBar.currentChanged.connect(self.appletStack.setCurrentIndex)
        self.appletBar.currentChanged.connect(self._menuBar.setCurrentIndex)

    def addApplet( self, applet ):
        self._applets.append(applet)
        self.appletBar.addItem( applet.controlWidget , applet.name )
        self.appletStack.addWidget( applet.centralWidget )
        self._menuBar.addAppletMenuWidget( applet.menuWidget )
        return len(self._applets) - 1

    def currentIndex( self ):
        return self.appletBar.currentIndex()

    def indexOf( self, applet ):
        return self.appletBar.indexOf(applet.controlWidget)

    def setCurrentIndex( self, index ):
        self.appletBar.setCurrentIndex( index )
        self._menuBar.setCurrentIndex( index )

    def __len__( self ):
        return self.appletBar.count()

    def __getitem__( self, index ):
        return self._applets[index]

    
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

