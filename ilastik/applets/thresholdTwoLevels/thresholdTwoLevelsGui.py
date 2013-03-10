from PyQt4.QtCore import Qt
from PyQt4.QtGui import QColor


from volumina.api import LazyflowSource, AlphaModulatedLayer
from ilastik.applets.layerViewer import LayerViewerGui

class ThresholdTwoLevelsGui( LayerViewerGui ):
    
    def __init__(self, *args, **kwargs):
        super( self.__class__, self ).__init__(*args, **kwargs)
        self._channelColors = self._createDefault16ColorColorTable()
    
    def setupLayers(self):
        layers = []        
        op = self.topLevelOperatorView

        # Show the cached output, since it goes through a blocked cache
        if op.CachedOutput.ready():
            outputLayer = self.createStandardLayerFromSlot( op.CachedOutput )
            outputLayer.name = "Output (Cached)"
            outputLayer.visible = False
            outputLayer.opacity = 1.0
            layers.append(outputLayer)

        if op.BigRegions.ready():
            lowThresholdLayer = self.createStandardLayerFromSlot( op.BigRegions )
            lowThresholdLayer.name = "Big Regions"
            lowThresholdLayer.visible = False
            lowThresholdLayer.opacity = 1.0
            layers.append(lowThresholdLayer)

        if op.FilteredSmallLabels.ready():
            filteredSmallLabelsLayer = self.createStandardLayerFromSlot( op.FilteredSmallLabels, lastChannelIsAlpha=True )
            filteredSmallLabelsLayer.name = "Filtered Small Labels"
            filteredSmallLabelsLayer.visible = False
            filteredSmallLabelsLayer.opacity = 1.0
            layers.append(filteredSmallLabelsLayer)

        if op.SmallRegions.ready():
            lowThresholdLayer = self.createStandardLayerFromSlot( op.SmallRegions )
            lowThresholdLayer.name = "Small Regions"
            lowThresholdLayer.visible = False
            lowThresholdLayer.opacity = 1.0
            layers.append(lowThresholdLayer)

        # Selected input channel, smoothed.
        if op.Smoothed.ready():
            smoothedLayer = self.createStandardLayerFromSlot( op.Smoothed )
            smoothedLayer.name = "Smoothed Input"
            smoothedLayer.visible = True
            smoothedLayer.opacity = 1.0
            layers.append(smoothedLayer)

        # Show each input channel as a separate layer
        for channelIndex, channelSlot in enumerate(op.InputChannels):
            if op.InputChannels.ready():
                drange = channelSlot.meta.drange
                if drange is None:
                    drange = (0.0, 1.0)
                channelSrc = LazyflowSource(channelSlot)
                channelLayer = AlphaModulatedLayer( channelSrc,
                                                    tintColor=QColor(self._channelColors[channelIndex]),
                                                    range=drange,
                                                    normalize=drange )
                channelLayer.name = "Input Ch{}".format(channelIndex)
                channelLayer.opacity = 1.0
                channelLayer.visible = channelIndex == op.Channel.value # By default, only the selected input channel is visible.    
                layers.append(channelLayer)
        
        # Show the raw input data
        rawSlot = self.topLevelOperatorView.RawInput
        if rawSlot.ready():
            rawLayer = self.createStandardLayerFromSlot( rawSlot )
            rawLayer.name = "Raw Data"
            rawLayer.visible = True
            rawLayer.opacity = 1.0
            layers.append(rawLayer)

        return layers

    def _createDefault16ColorColorTable(self):
        colors = []

        # SKIP: Transparent for the zero label
        #colors.append(QColor(0,0,0,0))

        # ilastik v0.5 colors
        colors.append( QColor( Qt.red ) )
        colors.append( QColor( Qt.green ) )
        colors.append( QColor( Qt.yellow ) )
        colors.append( QColor( Qt.blue ) )
        colors.append( QColor( Qt.magenta ) )
        colors.append( QColor( Qt.darkYellow ) )
        colors.append( QColor( Qt.lightGray ) )

        # Additional colors
        colors.append( QColor(255, 105, 180) ) #hot pink
        colors.append( QColor(102, 205, 170) ) #dark aquamarine
        colors.append( QColor(165,  42,  42) ) #brown
        colors.append( QColor(0, 0, 128) )     #navy
        colors.append( QColor(255, 165, 0) )   #orange
        colors.append( QColor(173, 255,  47) ) #green-yellow
        colors.append( QColor(128,0, 128) )    #purple
        colors.append( QColor(240, 230, 140) ) #khaki

        colors.append( QColor(192, 192, 192) ) #silver

#        colors.append( QColor(69, 69, 69) )    # dark grey
#        colors.append( QColor( Qt.cyan ) )

        assert len(colors) == 16

        return [c.rgba() for c in colors]
