from PyQt4.QtGui import QColor
from ilastik.applets.batchIo.batchIoGui import BatchIoGui
from ilastik.applets.layerViewer import LayerViewerGui

from ilastik.utility import bind

from lazyflow.operators import OpMultiArraySlicer2

from volumina.api import LazyflowSource, AlphaModulatedLayer

class PixelClassificationBatchResultsGui( BatchIoGui ):
    """
    A subclass of the generic Batch gui that creates custom layer viewers.
    """
    def createLayerViewer(self, opLane):
        return PixelClassificationResultsViewer(opLane)
        
class PixelClassificationResultsViewer(LayerViewerGui):
    
    def __init__(self, *args, **kwargs):
        super(PixelClassificationResultsViewer, self).__init__(*args, **kwargs)
        self.topLevelOperatorView.PmapColors.notifyDirty( bind( self.updateAllLayers ) )
        self.topLevelOperatorView.LabelNames.notifyDirty( bind( self.updateAllLayers ) )
    
    def setupLayers(self):
        layers = []
        opLane = self.topLevelOperatorView

        exportedLayers = self._initPredictionLayers(opLane.ExportedImage)
        for layer in exportedLayers:
            layer.visible = True
            layer.name = layer.name + "- Exported"
        layers += exportedLayers
        
        previewLayers = self._initPredictionLayers(opLane.ImageToExport)
        for layer in previewLayers:
            layer.visible = False
            layer.name = layer.name + "- Preview"
        layers += previewLayers
        
        # If available, also show the raw data layer
        rawSlot = opLane.RawImage
        if rawSlot.ready():
            rawLayer = self.createStandardLayerFromSlot( rawSlot )
            rawLayer.name = "Raw Data"
            rawLayer.visible = True
            rawLayer.opacity = 1.0
            layers.append( rawLayer )

        return layers 

    def _initPredictionLayers(self, predictionSlot):
        layers = []

        opLane = self.topLevelOperatorView
        colors = opLane.PmapColors.value
        names = opLane.LabelNames.value

        # Use a slicer to provide a separate slot for each channel layer
        opSlicer = OpMultiArraySlicer2( parent=opLane.viewed_operator() )
        opSlicer.Input.connect( predictionSlot )
        opSlicer.AxisFlag.setValue('c')

        for channel, channelSlot in enumerate(opSlicer.Slices):
            if channelSlot.ready() and channel < len(colors) and channel < len(names):
                predictsrc = LazyflowSource(channelSlot)
                predictLayer = AlphaModulatedLayer( predictsrc,
                                                    tintColor=QColor(*colors[channel]),
                                                    range=(0.0, 1.0),
                                                    normalize=(0.0, 1.0) )
                predictLayer.opacity = 0.25
                predictLayer.visible = True
                predictLayer.name = names[channel]
                layers.append(predictLayer)

        return layers