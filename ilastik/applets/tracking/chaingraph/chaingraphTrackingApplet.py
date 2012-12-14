from ilastik.applets.base.applet import Applet

from lazyflow.graph import OperatorWrapper
from ilastik.applets.tracking.chaingraph.opChaingraphTracking import OpChaingraphTracking
from ilastik.applets.tracking.base.trackingSerializer import TrackingSerializer

class ChaingraphTrackingApplet( Applet ):
    def __init__( self, graph, guiName="Tracking", projectFileGroupName="Tracking" ):
        super(ChaingraphTrackingApplet, self).__init__( guiName )

        # Wrap the top-level operator, since the GUI supports multiple images
        self._topLevelOperator = OperatorWrapper(OpChaingraphTracking, graph=graph)

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
            from ilastik.applets.tracking.chaingraph.chaingraphTrackingGui import ChaingraphTrackingGui
            self._gui = ChaingraphTrackingGui(self._topLevelOperator)
        return self._gui
