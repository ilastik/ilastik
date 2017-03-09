from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui

from volumina.pixelpipeline.datasources import LazyflowSource

from volumina.api import ColortableLayer, generateRandomColors


class SlicGui(LayerViewerGui):
    def setupLayers(self):
        layers = [self.createStandardLayerFromSlot(self.topLevelOperatorView.Input)]
        layers[0].opacity = 0.5
        superVoxelSlot = self.topLevelOperatorView.Output
        if superVoxelSlot.ready():
            colortable = generateRandomColors(100, clamp={"v":1.0, "s": 1.0})
            layer = ColortableLayer(LazyflowSource(superVoxelSlot), colortable, direct=True)
            layer.name = "SLIC"
            layer.visible = True
            layer.opacity = 1.0
            layers.append(layer)

        return layers
