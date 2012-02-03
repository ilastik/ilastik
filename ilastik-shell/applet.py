from PyQt4.QtGui import QLabel

class Applet( object ):
    def __init__( self, name = "Example Applet" ):
        self.name = name
        
        self.__centralWidget = QLabel(name + " Central Widget")
        self.__controlWidget = QLabel(name + " Control Widget")
        
    def centralWidget( self ):
        return self.__centralWidget

    def controlWidget( self ):
        return self.__controlWidget



