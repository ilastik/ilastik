from ilastik.applets.base.applet import Applet

from opDataSelection import OpDataSelection

from dataSelectionSerializer import DataSelectionSerializer, Ilastik05DataSelectionDeserializer

from lazyflow.graph import OperatorWrapper

from ilastik.applets.base.applet import SingleToMultiAppletAdapter
class DataSelectionApplet( SingleToMultiAppletAdapter ): # Uses base class for most methods, but provides a custom self.gui override.
    """
    This applet allows the user to select sets of input data, 
    which are provided as outputs in the corresponding top-level applet operator.
    """
    def __init__( self, workflow, title, projectFileGroupName, supportIlastik05Import=False, batchDataGui=False):
        super(DataSelectionApplet, self).__init__(title, workflow)

        # Our top-level operator is wrapped to enable multi-image support.
        # All inputs are common to all inputs except for the 'Dataset' input, which is unique for each image.
        # Hence, 'Dataset' is the only 'promoted' slot.
        #self._topLevelOperator = OperatorWrapper( OpDataSelection, parent=workflow, promotedSlotNames=set(['Dataset']) )
        self.topLevelOperator.name = "DataSelection Top-level Operator"

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
    def operatorClass(self):
        return OpDataSelection
    
    @property
    def broadcastingSlotNames(self):
        # Everything except Dataset
        return ['ProjectFile', 'ProjectDataGroup', 'WorkingDirectory']

    def addLane(self, laneIndex):
        """
        Add an image lane to the top-level operator.
        Since the top-level operator is just an OperatorWrapper, this is simple.
        """
        numLanes = len(self.topLevelOperator.innerOperators)
        if laneIndex == numLanes:
            self.topLevelOperator._insertInnerOperator(numLanes, numLanes+1)
        
    def removeLane(self, laneIndex, finalLength):
        """
        Remove an image lane from the top-level operator.
        Since the top-level operator is just an OperatorWrapper, this is simple.
        """
        numLanes = len(self.topLevelOperator.innerOperators)
        if finalLength < numLanes:
            self.topLevelOperator._removeInnerOperator(laneIndex, numLanes-1)
