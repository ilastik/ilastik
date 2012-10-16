from ilastik.applets.base.applet import Applet

from opTrackingNN import OpTrackingNN
from trackingGuiNN import TrackingGuiNN
from trackingSerializerNN import TrackingSerializerNN

from lazyflow.graph import OperatorWrapper
from ilastik.applets.tracking.opTrackingNN import OpTrackingNN
from ilastik.applets.tracking.trackingTabsGui import TrackingTabsGui

class TrackingAppletNN( Applet ):
    """
    This is a simple thresholding applet
    """
    def __init__( self, graph, guiName="Tracking", projectFileGroupName="Tracking" ):
        super(TrackingAppletNN, self).__init__( guiName )

        # Wrap the top-level operator, since the GUI supports multiple images
        self._topLevelOperator = OperatorWrapper(OpTrackingNN, graph=graph)

        self._gui = TrackingTabsGui(self._topLevelOperator)
        
        self._serializableItems = [ TrackingSerializerNN(self._topLevelOperator, projectFileGroupName) ]

    @property
    def topLevelOperator(self):
        return self._topLevelOperator

    @property
    def dataSerializers(self):
        return self._serializableItems

    @property
    def viewerControlWidget(self):
        return self._centralWidget.viewerControlWidget

    @property
    def gui(self):
        return self._gui
