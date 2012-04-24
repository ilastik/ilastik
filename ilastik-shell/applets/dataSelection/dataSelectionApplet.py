from lazyflow.operators import OpImageReader
from ilastikshell.applet import Applet

from opDataSelection import OpDataSelection

from dataSelectionSerializer import DataSelectionSerializer
from dataSelectionPreferencesManager import DataSelectionPreferencesManager
from dataSelectionGui import DataSelectionGui

class DataSelectionApplet( Applet ):
    """
    This applet allows the user to select sets of input data, 
    which are provided as outputs in the corresponding top-level applet operator.
    """
    def __init__( self, graph ):
        super(DataSelectionApplet, self).__init__( self, "Data Selection" )
        
        # Create a data selection top-level operator on the main graph
        # This operator object represents the "model" or master state of the applet which 
        #  the other components of the applet will manipulate and/or listen to for changes.
        self._topLevelOperator = OpDataSelection(graph)

        # Instantiate the main GUI, which creates the applet drawers (for now)
        self._centralWidget = DataSelectionGui( self._topLevelOperator )

        # To save some typing, the menu bar is defined in the .ui file 
        #  along with the rest of the central widget.
        # However, we must expose it here as an applet property since we 
        #  want it to show up properly in the shell
        self._menuWidget = self._centralWidget.menuBar
        
        # The central widget owns the applet drawer gui
        self._drawers = [ ("Datasets", self._centralWidget.datasetDrawer) ]

        # A separate object handles serializing the user's selections
        self._serializableItems = [ DataSelectionSerializer(self._topLevelOperator) ]
        
        # Preferences manager
        self._preferencesManager = DataSelectionPreferencesManager()
    
    @property
    def centralWidget( self ):
        return self._centralWidget

    @property
    def appletDrawers(self):
        return self._drawers
    
    @property
    def menuWidget( self ):
        return self._menuWidget

    @property
    def dataSerializers(self):
        return self._serializableItems

    @property
    def topLevelOperator(self):
        return self._topLevelOperator
    
    @property
    def appletPreferencesManager(self):
         return self._preferencesManager
     
    def setShellActions(self, shellActions):
        """
        TODO: Take appropriate action in response to a quit action.
        """
        pass
