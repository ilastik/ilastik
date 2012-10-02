from ilastik.ilastikshell.applet import Applet
from opConnectedComponents import OpConnectedComponents
from connectedComponentsGui import ConnectedComponentsGui

class ConnectedComponentsApplet( Applet ):
    def __init__( self, graph ):
        super(ConnectedComponentsApplet, self).__init__( None)

        self._topLevelOperator = OpConnectedComponents( graph )
        self._gui = ConnectedComponentsGui( [] )
    
    @property
    def topLevelOperator(self):
        return self._topLevelOperator

    @property
    def gui(self):
        return self._gui

if __name__=='__main__':
    #make the program quit on Ctrl+C
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    import sys
    from PyQt4.QtGui import QApplication
    
    qapp = QApplication(sys.argv)
    cca = ConnectedComponentsApplet( None )
    cca.gui.show()

    qapp.exec_()
