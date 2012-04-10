from PyQt4.QtGui import QLabel, QApplication

from test.serializationTestItems import ExampleSerializableItem

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
    def __init__( self, name = "Example Applet" ):
        """ Example constructor for testing purposes only.
            No need to be called from subclasses."""
        self.name = name
        
        self._centralWidget = QLabel(name + " Central Widget")
        self._controlWidget = QLabel(name + " Control Widget")
        self._menuWidget = QLabel(name + " Menu Widget")
        
        # Only a single serializable item for this example applet
        self._serializableItems = [ExampleSerializableItem(self.name)]

    @property
    def centralWidget( self ):
        return self._centralWidget

    @property
    def controlWidgets( self ):
        """ A list of the control widgets to be displayed in the left-hand side bar for this applet"""
        return self._controlWidgets

    @property
    def menuWidget( self ):
        return self._menuWidget

    @property
    def serializableItems(self):
        """ Return a list of serialization.SerializableItem objects for loading/saving """ 
        return self._serializableItems

if __name__ == '__main__':
    run_applet(Applet)
