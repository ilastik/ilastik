from ilastik.applets.base.applet import StandardApplet
from opDeviationFromMean import OpDeviationFromMean
#from deviationFromMeanSerializer import DeviationFromMeanSerializer

class DeviationFromMeanApplet( StandardApplet ):
    """
    This applet serves as an example multi-image-lane applet.
    The GUI is not aware of multiple image lanes (it is written as if the applet were single-image only).
    The top-level operator is multi-image.
    """
    def __init__( self, workflow, projectFileGroupName ):

        # Multi-image operator
        self._topLevelOperator = OpDeviationFromMean(parent=workflow)
        
        # Base class
        super(DeviationFromMeanApplet, self).__init__( "Deviation From Mean", workflow )
        #self._serializableItems = [ DeviationFromMeanSerializer( self._topLevelOperator, projectFileGroupName ) ]
        self._serializableItems = []
            
    @property
    def topLevelOperator(self):
        # Override from base class.
        return self._topLevelOperator

    @property
    def singleLaneGuiClass(self):
        from deviationFromMeanGui import DeviationFromMeanGui
        return DeviationFromMeanGui

    @property
    def dataSerializers(self):
        return self._serializableItems


