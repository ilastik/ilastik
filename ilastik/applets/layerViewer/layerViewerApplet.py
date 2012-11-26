from lazyflow.graph import OperatorWrapper
from ilastik.applets.base.applet import Applet
from opLayerViewer import OpLayerViewer


from ilastik.applets.base.applet import SingleToMultiAppletAdapter
class LayerViewerApplet( SingleToMultiAppletAdapter ):
    """
    This applet can be used as a simple viewer of raw image data.  
    Its main purpose is to provide a simple example of how to use the LayerViewerGui, 
    which is intended to be used as a base class for most other applet GUIs.
    """
    def __init__( self, workflow ):
        super(LayerViewerApplet, self).__init__("layer Viewer", workflow)

#        self._topLevelOperator = OperatorWrapper( OpLayerViewer, parent=workflow, promotedSlotNames=set(['RawInput']) )
#        self._topLevelOperator.name = "LayerViewer Top-Level Operator"
        self._serializableItems = []

    @property
    def operatorClass(self):
        return OpLayerViewer
    
    @property
    def guiClass(self):
        from layerViewerGui import LayerViewerGui
        return LayerViewerGui

    @property
    def dataSerializers(self):
        return self._serializableItems

#    @property
#    def topLevelOperator(self):
#        return self._topLevelOperator
#    