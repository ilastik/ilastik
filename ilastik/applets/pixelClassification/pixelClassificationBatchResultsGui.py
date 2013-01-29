from ilastik.applets.batchIo.batchIoGui import BatchIoGui
from ilastik.applets.layerViewer import LayerViewerGui

class PixelClassificationBatchResultsGui( BatchIoGui ):
    """
    A subclass of the generic Batch gui that creates custom layer viewers.
    """
    def createLayerViewer(self, opLane):
        return PixelClassificationResultsViewer(opLane)
        
class PixelClassificationResultsViewer(LayerViewerGui):
    def setupLayers(self):
        layers = []

        # Show the exported data on disk
        opLane = self.topLevelOperatorView
        exportedDataSlot = opLane.ExportedImage
        if exportedDataSlot.ready():
            exportLayer = self.createStandardLayerFromSlot( exportedDataSlot )
            exportLayer.name = "Probabilities - Exported"
            exportLayer.visible = True
            exportLayer.opacity = 1.0
            layers.append(exportLayer)
        
        # Show the (live-updated) data we're exporting
        previewSlot = opLane.ImageToExport
        if previewSlot.ready():
            previewLayer = self.createStandardLayerFromSlot( previewSlot )
            previewLayer.name = "Probabilities - Live Preview"
            previewLayer.visible = False # off by default
            previewLayer.opacity = 1.0
            layers.append(previewLayer)

        return layers

