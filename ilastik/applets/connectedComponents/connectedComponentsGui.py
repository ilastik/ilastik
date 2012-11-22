from PyQt4.QtGui import QWidget

from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui

class ConnectedComponentsGui( LayerViewerGui ):
    def appletDrawers( self ):
        return [('Identify Objects', QWidget())]

    def setupLayers( self, imageIndex ):
        return []
