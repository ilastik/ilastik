from ilastik.ilastikshell.applet import Applet

from opDataSelection import OpDataSelection

from dataSelectionSerializer import DataSelectionSerializer, Ilastik05DataSelectionDeserializer
from dataSelectionPreferencesManager import DataSelectionPreferencesManager

from lazyflow.graph import OperatorWrapper

class DataSelectionApplet( Applet ):
    """
    This applet allows the user to select sets of input data, 
    which are provided as outputs in the corresponding top-level applet operator.
    """
    def __init__( self, graph, title, projectFileGroupName, supportIlastik05Import=False, batchDataGui=False):
        super(DataSelectionApplet, self).__init__(title)

        # Our top-level operator is wrapped to enable multi-image support.
        # All inputs are common to all inputs except for the 'Dataset' input, which is unique for each image.
        # Hence, 'Dataset' is the only 'promoted' slot.
        self._topLevelOperator = OperatorWrapper( OpDataSelection(graph=graph), promotedSlotNames=set(['Dataset']) )

        self._serializableItems = [ DataSelectionSerializer(self._topLevelOperator, projectFileGroupName) ]
        if supportIlastik05Import:
            self._serializableItems.append(Ilastik05DataSelectionDeserializer(self._topLevelOperator))

        self._gui = None
        self.batchDataGui = batchDataGui
        
        self._preferencesManager = DataSelectionPreferencesManager()
    
    @property
    def gui( self ):
        if self._gui is None:
            from dataSelectionGui import DataSelectionGui, GuiMode
            guiMode = { True: GuiMode.Batch, False: GuiMode.Normal }[self.batchDataGui]
            self._gui = DataSelectionGui( self._topLevelOperator, self._serializableItems[0], guiMode )
        return self._gui

    @property
    def dataSerializers(self):
        return self._serializableItems

    @property
    def topLevelOperator(self):
        return self._topLevelOperator
    
    @property
    def appletPreferencesManager(self):
         return self._preferencesManager
