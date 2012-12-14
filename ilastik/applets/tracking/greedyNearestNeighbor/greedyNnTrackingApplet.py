from ilastik.applets.base.applet import Applet
from lazyflow.graph import OperatorWrapper
from ilastik.applets.tracking.base.trackingSerializer import TrackingSerializer
from ilastik.applets.tracking.greedyNearestNeighbor.opGreedyNnTracking import OpGreedyNnTracking

class GreedyNnTrackingApplet( Applet ):
    """
    This is a simple thresholding applet
    """
    def __init__( self, graph, guiName="Tracking", projectFileGroupName="Tracking" ):
        super(GreedyNnTrackingApplet, self).__init__( guiName )

        # Wrap the top-level operator, since the GUI supports multiple images
        self._topLevelOperator = OperatorWrapper(OpGreedyNnTracking, graph=graph)

#        self._gui = TrackingTabsGui(self._topLevelOperator)
        self._gui = None
        
        self._serializableItems = [ TrackingSerializer(self._topLevelOperator, projectFileGroupName) ]

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
        if self._gui is None:
            from ilastik.applets.tracking.greedyNearestNeighbor.greedyNnTrackingGui import GreedyNnTrackingGui
            self._gui = GreedyNnTrackingGui(self._topLevelOperator)        
        return self._gui
