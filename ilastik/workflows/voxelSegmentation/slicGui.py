import os

import numpy as np

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui

from volumina.pixelpipeline.datasources import LazyflowSource
from volumina.api import AlphaModulatedLayer

from .slicViewerControls import SlicViewerControls


SLIC_PARAMS = ("NumSegments", "Compactness", "MaxIter")#, "SlicZero")


class SlicGui(LayerViewerGui):

    def __init__(self, parentApplet, topLevelOperatorView, additionalMonitoredSlots=[], centralWidgetOnly=False, crosshair=True):
        super().__init__(parentApplet, topLevelOperatorView, additionalMonitoredSlots=[], centralWidgetOnly=False, crosshair=True)

        self._drawer = SlicViewerControls()

        def runSlic():
            for param in SLIC_PARAMS:
                print("{} {}".format(param, getattr(self._drawer, param).value()))
                getattr(self.topLevelOperatorView, param).setValue(getattr(self._drawer, param).value())

            self.topLevelOperatorView.Input.setDirty()

        self._drawer.RunSLICButton.clicked.connect(runSlic)

        # Import default params from opSlic
        for param in SLIC_PARAMS:
            getattr(self._drawer, param).setValue(getattr(self.topLevelOperatorView, param).value)

        if self.topLevelOperatorView.Output.ready():
            self._drawer.NumSegments.setValue(np.max(self.topLevelOperatorView.Output.value))


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

    def appletDrawer(self):
        """
        Load the viewer controls GUI, which appears below the applet bar.
        In our case, the viewer control GUI consists mainly of a layer list.
        Subclasses should override this if they provide their own viewer control widget.
        """
        return self._drawer
