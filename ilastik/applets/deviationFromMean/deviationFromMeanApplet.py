from ilastik.applets.base.applet import Applet
from opDeviationFromMean import OpDeviationFromMean
#from deviationFromMeanSerializer import DeviationFromMeanSerializer


from ilastik.applets.base.applet import SingleToMultiAppletAdapter
class DeviationFromMeanApplet( SingleToMultiAppletAdapter ):
    """
    This applet demonstrates how to use the LabelingGui base class, which serves as a reusable base class for other applet GUIs that need a labeling UI.  
    """
    def __init__( self, workflow, projectFileGroupName ):
        self._topLevelOperator = OpDeviationFromMean(parent=workflow)
        super(DeviationFromMeanApplet, self).__init__( "Deviation From Mean", workflow )
        #self._serializableItems = [ DeviationFromMeanSerializer( self._topLevelOperator, projectFileGroupName ) ]
        self._serializableItems = []
            
    @property
    def topLevelOperator(self):
        return self._topLevelOperator

    @property
    def operatorClass(self):
        # This should never be called because we provided a custom top-level operator
        assert False

    @property
    def broadcastingSlotNames(self):
        # This should never be called because we provided a custom top-level operator
        raise NotImplementedError
        
    @property
    def singleImageGuiClass(self):
        from deviationFromMeanGui import DeviationFromMeanGui
        return DeviationFromMeanGui

    @property
    def dataSerializers(self):
        return self._serializableItems

    def addLane(self, laneIndex):
        """
        Add an image lane to the top-level operator.
        """
        numLanes = len(self.topLevelOperator.Input)
        assert numLanes == laneIndex, "Image lanes must be appended."        
        self.topLevelOperator.Input.resize(numLanes+1)
        self.topLevelOperator.Output.resize(numLanes+1)
        
    def removeLane(self, laneIndex, finalLength):
        """
        Remove the specified image lane from the top-level operator.
        """
        self.topLevelOperator.Input.removeSlot(laneIndex, finalLength)
        self.topLevelOperator.Output.removeSlot(laneIndex, finalLength)

