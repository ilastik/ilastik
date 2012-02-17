from PyQt4 import uic
from PyQt4 import Qt
from PyQt4.QtGui import QMainWindow, QWidget, QHBoxLayout, QMenuBar, QFrame, QLabel, QStackedLayout
from PyQt4 import QtCore

class _ShellMenuBar( QWidget ):
    def __init__( self, parent=None ):
        QWidget.__init__(self, parent=parent)
        #self._layout = QHBoxLayout( self )
        self._layout = QStackedLayout( self )
        #self.setLayout = self._layout

        
        self.appletMenuBar = QMenuBar(self)
        self.appletMenuBar.addMenu( "AppletMenu" )
        self.appletMenuBar.addMenu( "    " )
        self.appletMenuBar.addMenu( "AppletMenu2" )
        #self._layout.addWidget(self.appletMenuBar)

        #self.shellMenuBar = QMenuBar(self)
        #self.shellMenuBar.addMenu("File")
        #self._layout.addWidget(self.shellMenuBar)
        #separator = QFrame()
        #separator.setFrameStyle(QFrame.VLine)
        #separator.setLineWidth( 2 )
        #self.label = QLabel("dsafsaf")
        #self._layout.addWidget(separator)
        #self._layout.addWidget(QLabel("badfbfb"))
        



class IlastikShell( QMainWindow ):
    def __init__( self, workflow = [], parent = None, flags = QtCore.Qt.WindowFlags(0) ):
        QMainWindow.__init__(self, parent = parent, flags = flags )
        uic.loadUi( "ui/ilastikShell.ui", self )
        self._applets = []

        self._menuBar = _ShellMenuBar( self )
        self.setMenuWidget( self._menuBar  )

        for applet in workflow:
            self.addApplet(applet)

        self.appletBar.currentChanged.connect(self.appletStack.setCurrentIndex)

    def addApplet( self, applet ):
        self._applets.append(applet)
        self.appletBar.addItem( applet.controlWidget , applet.name )
        self.appletStack.addWidget( applet.centralWidget )
        return len(self._applets) - 1

    def currentIndex( self ):
        return self.appletBar.currentIndex()

    def indexOf( self, applet ):
        return self.appletBar.indexOf(applet.controlWidget)

    def setCurrentIndex( self, index ):
        self.appletBar.setCurrentIndex( index )

    def __len__( self ):
        return self.appletBar.count()

    def __getitem__( self, index ):
        return self._applets[index]

    


if __name__ == "__main__":
    #make the program quit on Ctrl+C
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    from PyQt4.QtGui import QApplication
    import sys
    from applet import Applet

    qapp = QApplication(sys.argv)
    shell = IlastikShell( [Applet(), Applet("Tracking")])
    shell.show()
    qapp.exec_()

