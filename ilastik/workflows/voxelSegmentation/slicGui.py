import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui

from volumina.pixelpipeline.datasources import LazyflowSource
from volumina.api import AlphaModulatedLayer

from .slicViewerControls import SlicViewerControls


class SlicGui(LayerViewerGui):
    def setupLayers(self):
        layers = [self.createStandardLayerFromSlot(self.topLevelOperatorView.Input)]
        layers[0].opacity = 1.0
        superVoxelSlot = self.topLevelOperatorView.BoundariesOutput
        if superVoxelSlot.ready():
            layer = AlphaModulatedLayer(LazyflowSource(superVoxelSlot),
                            tintColor=QColor(Qt.blue),
                            range=(0.0, 1.0),
                            normalize=(0.0, 1.0))
            layer.name = "Input Data"
            layer.visible = True
            layer.opacity = 1.0
            layers.insert(0, layer)

        return layers

    def initViewerControlUi(self):
        """
        Load the viewer controls GUI, which appears below the applet bar.
        In our case, the viewer control GUI consists mainly of a layer list.
        Subclasses should override this if they provide their own viewer control widget.
        """
        localDir = os.path.split(__file__)[0]
        self.__viewerControlWidget = SlicViewerControls()

        # The editor's layerstack is in charge of which layer movement buttons are enabled
        model = self.editor.layerStack

        if self.__viewerControlWidget is not None:
            self.__viewerControlWidget.setupConnections(model, self.topLevelOperatorView)

    def viewerControlWidget(self):
        return self.__viewerControlWidget
