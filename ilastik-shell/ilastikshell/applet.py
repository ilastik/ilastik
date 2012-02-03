from PyQt4.QtGui import QLabel

class Applet( object ):
    @property
    def centralWidget( self ):
        return self._centralWidget

    @property
    def controlWidget( self ):
        return self._controlWidget

    def __init__( self, name = "Example Applet" ):
        self.name = name
        
        self._centralWidget = QLabel(name + " Central Widget")
        self._controlWidget = QLabel(name + " Control Widget")
