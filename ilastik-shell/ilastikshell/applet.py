from PyQt4.QtGui import QLabel

class Applet( object ):
    def __init__( self, name = "Example Applet" ):
        self.name = name
        
        self.centralWidget = QLabel(name + " Central Widget")
        self.controlWidget = QLabel(name + " Control Widget")
