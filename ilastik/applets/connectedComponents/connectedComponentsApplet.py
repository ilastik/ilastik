from ilastik.ilastikshell.applet import Applet
from opConnectedComponents import OpConnectedComponents
from connectedComponentsGui import ConnectedComponentsGui

class ConnectedComponentsApplet( Applet ):
    def __init__( self, graph, projectFileGroupName ):
        Applet.__init__( self, "Connected Components" )

        self._topLevelOperator = OpPixelClassification( graph )
        self._gui = ConnectedComponentsGui()
    
    @property
    def topLevelOperator(self):
        return self._topLevelOperator

    @property
    def gui(self):
        return self._gui
