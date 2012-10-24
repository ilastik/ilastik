from ilastik.applets.base.applet import Applet

from opTracking import OpTracking

from trackingSerializer import TrackingSerializer

from lazyflow.graph import OperatorWrapper

class TrackingApplet( Applet ):
    """
    This is a simple thresholding applet
    """
    def __init__( self, graph, guiName="Tracking", projectFileGroupName="Tracking" ):
        super(TrackingApplet, self).__init__( guiName )

        # Wrap the top-level operator, since the GUI supports multiple images
        self._topLevelOperator = OperatorWrapper(OpTracking, graph=graph)

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
            from trackingGui import TrackingGui
            self._gui = TrackingGui(self._topLevelOperator)
        return self._gui
