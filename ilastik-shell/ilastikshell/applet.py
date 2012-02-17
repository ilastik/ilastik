from PyQt4.QtGui import QLabel, QApplication

def run_applet( applet_type, *args, **kwargs):
    '''Run applet standalone.'''
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    qapp = QApplication([])
    applet = applet_type(*args, **kwargs)
    applet.centralWidget.show()
    applet.controlWidget.show()
    qapp.exec_()



class Applet( object ):
    @property
    def centralWidget( self ):
        return self._centralWidget

    @property
    def controlWidget( self ):
        return self._controlWidget

    @property
    def menuWidget( self ):
        return self._menuWidget

    def __init__( self, name = "Example Applet" ):
        self.name = name
        
        self._centralWidget = QLabel(name + " Central Widget")
        self._controlWidget = QLabel(name + " Control Widget")
        self._menuWidget = QLabel(name + " Menu Widget")

if __name__ == '__main__':
    run_applet(Applet)
