from ilastik.applets.base.applet import Applet

from opVigraWatershedViewer import OpVigraWatershedViewer
#from vigraWatershedSerializer import VigraWatershedSerializer

from lazyflow.graph import OperatorWrapper

class VigraWatershedViewerApplet( Applet ):
    """
    Viewer for watershed results, with minimal configuration controls.
    """
    def __init__( self, graph, guiName, projectFileGroupName ):
        super(VigraWatershedViewerApplet, self).__init__(guiName)

        # Wrap the top-level operator, since the GUI supports multiple images
        self._topLevelOperator = OperatorWrapper( OpVigraWatershedViewer(graph=graph),
                                                  promotedSlotNames=['RawImage', 'InputImage', 'OverrideLabels'] )

        self._gui = None # Created on first access
        
        self._serializableItems = []
        #self._serializableItems = [ VigraWatershedSerializer(self._topLevelOperator, projectFileGroupName) ]
        
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
            from vigraWatershedViewerGui import VigraWatershedViewerGui
            self._gui = VigraWatershedViewerGui(self._topLevelOperator)
        return self._gui
