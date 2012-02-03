from PyQt4 import uic
from PyQt4 import Qt
from PyQt4.QtGui import QMainWindow
from PyQt4 import QtCore

class IlastikShell( QMainWindow ):
    def __init__( self, workflow = [], parent = None, flags = QtCore.Qt.WindowFlags(0) ):
        QMainWindow.__init__(self, parent = parent, flags = flags )
        uic.loadUi( "ui/ilastikShell.ui", self )
        self._applets = []

        for applet in workflow:
            self.addApplet(applet)

        self.appletBar.currentChanged.connect(self.appletStack.setCurrentIndex)

    def addApplet( self, applet ):
        self._applets.append(applet)
        self.appletBar.addItem( applet.controlWidget() , applet.name )
        self.appletStack.addWidget( applet.centralWidget() )
        return len(self._applets) - 1

    def currentIndex( self ):
        return self.appletBar.currentIndex()

    def indexOf( self, applet ):
        return self.appletBar.indexOf(applet.controlWidget())

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

