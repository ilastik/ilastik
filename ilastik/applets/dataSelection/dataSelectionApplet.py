from ilastik.applets.base.applet import Applet

from opDataSelection import OpDataSelection

from dataSelectionSerializer import DataSelectionSerializer, Ilastik05DataSelectionDeserializer

from lazyflow.graph import OperatorWrapper

class DataSelectionApplet( Applet ):
    """
    This applet allows the user to select sets of input data, 
    which are provided as outputs in the corresponding top-level applet operator.
    """
    def __init__( self, workflow, title, projectFileGroupName, supportIlastik05Import=False, batchDataGui=False):
        super(DataSelectionApplet, self).__init__(title)

        # Our top-level operator is wrapped to enable multi-image support.
        # All inputs are common to all inputs except for the 'Dataset' input, which is unique for each image.
        # Hence, 'Dataset' is the only 'promoted' slot.
        self._topLevelOperator = OperatorWrapper( OpDataSelection, parent=workflow, promotedSlotNames=set(['Dataset']) )
        self._topLevelOperator.name = "DataSelection Top-level Operator"

        self._serializableItems = [ DataSelectionSerializer(self._topLevelOperator, projectFileGroupName) ]
        if supportIlastik05Import:
            self._serializableItems.append(Ilastik05DataSelectionDeserializer(self._topLevelOperator))

        self._gui = None
        self.batchDataGui = batchDataGui
        self.title = title
        
    @property
    def gui( self ):
        if self._gui is None:
            from dataSelectionGui import DataSelectionGui, GuiMode
            guiMode = { True: GuiMode.Batch, False: GuiMode.Normal }[self.batchDataGui]
            self._gui = DataSelectionGui( self._topLevelOperator, self._serializableItems[0], self.guiControlSignal, guiMode, self.title )
        return self._gui

    @property
    def dataSerializers(self):
        return self._serializableItems

    @property
    def topLevelOperator(self):
        return self._topLevelOperator
