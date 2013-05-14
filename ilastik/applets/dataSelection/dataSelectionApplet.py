from ilastik.applets.base.applet import Applet
from opDataSelection import OpMultiLaneDataSelectionGroup
from dataSelectionSerializer import DataSelectionSerializer, Ilastik05DataSelectionDeserializer

class DataSelectionApplet( Applet ):
    """
    This applet allows the user to select sets of input data, 
    which are provided as outputs in the corresponding top-level applet operator.
    """
    def __init__(self, workflow, title, projectFileGroupName, supportIlastik05Import=False, batchDataGui=False, force5d=False):
        self.__topLevelOperator = OpMultiLaneDataSelectionGroup(parent=workflow, force5d=force5d)
        super(DataSelectionApplet, self).__init__( title, syncWithImageIndex=False )

        self._serializableItems = [ DataSelectionSerializer(self.topLevelOperator, projectFileGroupName) ]
        if supportIlastik05Import:
            self._serializableItems.append(Ilastik05DataSelectionDeserializer(self.topLevelOperator))

        self._gui = None
        self._batchDataGui = batchDataGui
        self._title = title

    #
    # GUI
    #
    def getMultiLaneGui( self ):
        if self._gui is None:
            from dataSelectionGui import DataSelectionGui, GuiMode
            guiMode = { True: GuiMode.Batch, False: GuiMode.Normal }[self._batchDataGui]
            self._gui = DataSelectionGui( self.topLevelOperator, self._serializableItems[0], self.guiControlSignal, guiMode, self._title )
        return self._gui

    #
    # Top-level operator
    #
    @property
    def topLevelOperator(self):
        return self.__topLevelOperator 

    #
    # Project serialization
    #
    @property
    def dataSerializers(self):
        return self._serializableItems

