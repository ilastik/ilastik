from PyQt4 import uic
from PyQt4 import Qt
from PyQt4.QtGui import QMainWindow, QLabel
from PyQt4 import QtCore


class Applet( object ):
    def __init__( self, name = "Example Applet" ):
        self.name = name
        
        self.__centralWidget = QLabel(name + " Central Widget")
        self.__controlWidget = QLabel(name + " Control Widget")
        
    def centralWidget( self ):
        return self.__centralWidget

    def controlWidget( self ):
        return self.__controlWidget



class IlastikShell( QMainWindow ):
    def __init__( self, workflow = [], parent = None, flags = QtCore.Qt.WindowFlags(0) ):
        QMainWindow.__init__(self, parent = parent, flags = flags )
        uic.loadUi( "ui/ilastikShell.ui", self )
        self._applets = []

        for applet in workflow:
            self.addApplet(applet)

    def addApplet( self, applet ):
        self._applets.append(applet)
        self.appletBar.addItem( applet.controlWidget() , applet.name )
        return len(self._applets) - 1

    def currentIndex( self ):
        raise NotImplementedError

    def indexOf( self, applet ):
        raise NotImplementedError

    def insertApplet( self, index, applet ):
        raise NotImplementedError

    def setCurrentIndex( self, index ):
        raise NotImplementedError

    def __len__( self ):
        raise NotImplementedError

    def __getitem__( self, index ):
        raise NotImplementedError

    def __delitem__( self, index ):
        raise NotImplementedError

    


if __name__ == "__main__":
    #make the program quit on Ctrl+C
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    from PyQt4.QtGui import QApplication
    import sys

    qapp = QApplication(sys.argv)
    shell = IlastikShell( [Applet(), Applet("Tracking")])
    shell.show()
    qapp.exec_()
