from ilastik.applets.base.applet import Applet
from trackingSerializerNN import TrackingSerializerNN
from lazyflow.graph import OperatorWrapper
from ilastik.applets.tracking.opTrackingCons import OpTrackingCons

class TrackingAppletCons( Applet ):
    """
    This is a simple thresholding applet
    """
    def __init__( self, graph, guiName="Tracking", projectFileGroupName="Tracking" ):
        super(TrackingAppletCons, self).__init__( guiName )

        # Wrap the top-level operator, since the GUI supports multiple images
        self._topLevelOperator = OperatorWrapper(OpTrackingCons, graph=graph)

        self._gui = None
        
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
        if self._gui is None:
            from ilastik.applets.tracking.trackingGuiCons import TrackingGuiCons
            self._gui = TrackingGuiCons(self._topLevelOperator)        
        return self._gui
