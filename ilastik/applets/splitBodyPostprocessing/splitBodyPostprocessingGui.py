import numpy

from PyQt4.QtGui import QColor

from volumina.pixelpipeline.datasources import LazyflowSource, ArraySource
from volumina.layer import ColortableLayer, GrayscaleLayer

from ilastik.applets.layerViewer import LayerViewerGui

from ilastik.utility import bind


class SplitBodyPostprocessingGui(LayerViewerGui):
    
    firstFragmentColors = [ QColor(0,0,0,0), # transparent (background)
                   QColor(0, 255, 255),   # cyan
                   QColor(255, 0, 255),   # magenta
                   QColor(0, 0, 128),     # navy
                   QColor(165,  42,  42), # brown        
                   QColor(255, 105, 180), # hot pink
                   QColor(255, 165, 0),   # orange
                   QColor(173, 255,  47), # green-yellow
                   QColor(102, 205, 170), # dark aquamarine
                   QColor(128,0, 128),    # purple
                   QColor(240, 230, 140), # khaki
                   QColor(192, 192, 192), # silver
                   QColor(69, 69, 69) ]   # dark grey

    _fragmentColors = []
    for i in range(254):
        r,g,b = numpy.random.randint(0,255), numpy.random.randint(0,255), numpy.random.randint(0,255)
        _fragmentColors.append(QColor(r,g,b))
    _fragmentColors[0:len(firstFragmentColors)] = firstFragmentColors

    def setupLayers(self):
        layers = []
        
        op = self.topLevelOperatorView
        
        ravelerLabelsSlot = op.RavelerLabels
        if ravelerLabelsSlot.ready():
            colortable = []
            for i in range(256):
                r,g,b = numpy.random.randint(0,255), numpy.random.randint(0,255), numpy.random.randint(0,255)
                colortable.append(QColor(r,g,b).rgba())
            ravelerLabelLayer = ColortableLayer(LazyflowSource(ravelerLabelsSlot), colortable, direct=True)
            ravelerLabelLayer.name = "Raveler Labels"
            ravelerLabelLayer.visible = False
            ravelerLabelLayer.opacity = 0.4
            layers.append(ravelerLabelLayer)

        def addFragmentSegmentationLayers(mslot, name):
            if mslot.ready():
                for index, slot in enumerate(mslot):
                    if slot.ready():
                        raveler_label = slot.meta.selected_label
                        colortable = map(QColor.rgba, self._fragmentColors)
                        fragSegLayer = ColortableLayer(LazyflowSource(slot), colortable, direct=True)
                        fragSegLayer.name = "{} #{} ({})".format( name, index, raveler_label )
                        fragSegLayer.visible = False
                        fragSegLayer.opacity = 1.0
                        layers.append(fragSegLayer)

        addFragmentSegmentationLayers( op.FragmentedBodies, "Saved Fragments" )
        addFragmentSegmentationLayers( op.RelabeledFragments, "Relabeled Fragments" )
        addFragmentSegmentationLayers( op.FilteredFragmentedBodies, "CC-Filtered Fragments" )
        addFragmentSegmentationLayers( op.WatershedFilledBodies, "Watershed-filled Fragments" )

        mslot = op.EditedRavelerBodies
        for index, slot in enumerate(mslot):
            if slot.ready():
                raveler_label = slot.meta.selected_label
                # 0=Black, 1=Transparent
                colortable = [QColor(0, 0, 0).rgba(), QColor(0, 0, 0, 0).rgba()]
                bodyMaskLayer = ColortableLayer(LazyflowSource(slot), colortable, direct=True)
                bodyMaskLayer.name = "Raveler Body Mask #{} ({})".format( index, raveler_label )
                bodyMaskLayer.visible = True
                bodyMaskLayer.opacity = 1.0
                layers.append(bodyMaskLayer)

        inputSlot = op.InputData
        if inputSlot.ready():
            layer = GrayscaleLayer( LazyflowSource(inputSlot) )
            layer.name = "WS Input"
            layer.visible = False
            layer.opacity = 1.0
            layers.append(layer)

        #raw data
        rawSlot = self.topLevelOperatorView.RawData
        if rawSlot.ready():
            raw5D = self.topLevelOperatorView.RawData.value
            layer = GrayscaleLayer(ArraySource(raw5D), direct=True)
            #layer = GrayscaleLayer( LazyflowSource(rawSlot) )
            layer.name = "raw"
            layer.visible = True
            layer.opacity = 1.0
            layers.append(layer)

        return layers
















