import numpy

from PyQt4.QtGui import QColor

from volumina.pixelpipeline.datasources import LazyflowSource
from volumina.layer import ColortableLayer

#ilastik
from ilastik.applets.layerViewer import LayerViewerGui

class PreprocessingViewerGui( LayerViewerGui ):
    
    def __init__(self, *args, **kwargs):
        super(PreprocessingViewerGui, self).__init__(*args, **kwargs)
    
    def setupLayers(self):
        layers = []
        opLane = self.topLevelOperatorView
        
        # Supervoxels
        watershedSlot = opLane.WatershedImage
        if watershedSlot.ready():
            colortable = []
            for i in range(256):
                r,g,b = numpy.random.randint(0,255), numpy.random.randint(0,255), numpy.random.randint(0,255)
                colortable.append(QColor(r,g,b).rgba())
            watershedLayer = ColortableLayer(LazyflowSource(watershedSlot), colortable)
            watershedLayer.name = "Watershed"
            watershedLayer.visible = False
            watershedLayer.opacity = 1.0
            layers.append(watershedLayer)


        filteredSlot = opLane.FilteredImage
        if filteredSlot.ready():
            filteredLayer = self.createStandardLayerFromSlot( filteredSlot )
            filteredLayer.name = "Filtered Data"
            filteredLayer.visible = False
            filteredLayer.opacity = 1.0
            layers.append( filteredLayer )

        # Raw data        
        rawSlot = opLane.RawData
        if rawSlot.ready():
            rawLayer = self.createStandardLayerFromSlot( rawSlot )
            rawLayer.name = "Raw Data"
            rawLayer.visible = True
            rawLayer.opacity = 1.0
            layers.append( rawLayer )

        return layers 
