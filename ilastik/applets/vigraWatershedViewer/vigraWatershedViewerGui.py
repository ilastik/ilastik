from PyQt4 import uic
from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import QShortcut, QKeySequence

import os
import time
import copy
import threading
from functools import partial

from ilastik.applets.layerViewer import LayerViewerGui
from ilastik.utility import bind, PreferencesManager

from volumina.slicingtools import index2slice

import logging
logger = logging.getLogger(__name__)
traceLogger = logging.getLogger('TRACE.' + __name__)
from lazyflow.tracer import traceLogged

class VigraWatershedViewerGui(LayerViewerGui):
    """
    """
    
    ###########################################
    ### AppletGuiInterface Concrete Methods ###
    ###########################################
    
    def appletDrawers(self):
        return [ ("Watershed Viewer", self.getAppletDrawerUi() ) ]

    # (Other methods already provided by our base class)

    ###########################################
    ###########################################
    
    @traceLogged(traceLogger)
    def __init__(self, mainOperator):
        """
        """
        super(VigraWatershedViewerGui, self).__init__( mainOperator )
        self.mainOperator = mainOperator
        
        self.mainOperator.FreezeCache.setValue(True)
        self.mainOperator.OverrideLabels.setValue( { 0: (0,0,0,0) } )

        # Default settings (will be overwritten by serializer)
        self.mainOperator.InputChannelIndexes.setValue( [] )
        self.mainOperator.SeedThresholdValue.setValue( 0.0 )
        self.mainOperator.MinSeedSize.setValue( 0 )

        # Init padding gui updates
        blockPadding = PreferencesManager().get( 'vigra watershed viewer', 'block padding', 10)
        self.mainOperator.WatershedPadding.notifyDirty( self.updatePaddingGui )
        self.mainOperator.WatershedPadding.setValue(blockPadding)
        self.updatePaddingGui()
        
        # Init block shape gui updates
        cacheBlockShape = PreferencesManager().get( 'vigra watershed viewer', 'cache block shape', (256, 10))
        self.mainOperator.CacheBlockShape.notifyDirty( self.updateCacheBlockGui )
        self.mainOperator.CacheBlockShape.setValue( cacheBlockShape )
        self.updateCacheBlockGui()

        # Init seeds gui updates
        self.mainOperator.SeedThresholdValue.notifyDirty( self.updateSeedGui )
        self.mainOperator.SeedThresholdValue.notifyReady( self.updateSeedGui )
        self.mainOperator.SeedThresholdValue.notifyUnready( self.updateSeedGui )
        self.mainOperator.MinSeedSize.notifyDirty( self.updateSeedGui )
        self.updateSeedGui()
        
        # Init input channel gui updates
        self.mainOperator.InputChannelIndexes.notifyDirty( self.updateInputChannelGui )
        self.mainOperator.InputChannelIndexes.setValue( [0] )
        def subscribeToInputMetaChanges(multislot, index):
            multislot[index].notifyMetaChanged( self.updateInputChannelGui )
        self.mainOperator.InputImage.notifyInserted( bind(subscribeToInputMetaChanges) )
        self.updateInputChannelGui()
    
    @traceLogged(traceLogger)
    def initAppletDrawerUi(self):
        # Load the ui file (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        self._drawer = uic.loadUi(localDir+"/drawer.ui")

        # Input channels
        self._inputChannelCheckboxes = []
        self._inputChannelCheckboxes.append( self._drawer.input_ch0 )
        self._inputChannelCheckboxes.append( self._drawer.input_ch1 )
        self._inputChannelCheckboxes.append( self._drawer.input_ch2 )
        self._inputChannelCheckboxes.append( self._drawer.input_ch3 )
        self._inputChannelCheckboxes.append( self._drawer.input_ch4 )
        self._inputChannelCheckboxes.append( self._drawer.input_ch5 )
        self._inputChannelCheckboxes.append( self._drawer.input_ch6 )
        self._inputChannelCheckboxes.append( self._drawer.input_ch7 )
        self._inputChannelCheckboxes.append( self._drawer.input_ch8 )
        self._inputChannelCheckboxes.append( self._drawer.input_ch9 )
        for checkbox in self._inputChannelCheckboxes:
            checkbox.toggled.connect( self.onInputSelectionsChanged )

        # Seed thresholds
        self._drawer.useSeedsCheckbox.toggled.connect( self.onUseSeedsToggled )
        self._drawer.seedThresholdSpinBox.valueChanged.connect( self.onSeedThresholdChanged )
        
        # Seed size
        self._drawer.seedSizeSpinBox.valueChanged.connect( self.onSeedSizeChanged )

        # Padding
        self._drawer.updateWatershedsButton.clicked.connect( self.onUpdateWatershedsButton )
        self._drawer.paddingSlider.valueChanged.connect( self.onPaddingChanged )
        self._drawer.paddingSpinBox.valueChanged.connect( self.onPaddingChanged )

        # Block shape
        self._drawer.blockWidthSpinBox.valueChanged.connect( self.onBlockShapeChanged )
        self._drawer.blockDepthSpinBox.valueChanged.connect( self.onBlockShapeChanged )
                
    def getAppletDrawerUi(self):
        return self._drawer
    
    def hideEvent(self, event):
        """
        This GUI is being hidden because the user selected another applet or the window is closing.
        Save all preferences.
        """
        with PreferencesManager() as prefsMgr:
            prefsMgr.set( 'vigra watershed viewer', 'cache block shape', self.mainOperator.CacheBlockShape.value )
            prefsMgr.set( 'vigra watershed viewer', 'block padding', self.mainOperator.WatershedPadding.value )
        super( VigraWatershedViewerGui, self ).hideEvent(event)
    
    @traceLogged(traceLogger)
    def setupLayers(self, currentImageIndex):
        layers = []

        self.updateInputChannelGui()
        
        # Show the watershed data
        outputImageSlot = self.mainOperator.ColoredPixels[ currentImageIndex ]
        if outputImageSlot.ready():
            outputLayer = self.createStandardLayerFromSlot( outputImageSlot, lastChannelIsAlpha=True )
            outputLayer.name = "Watershed"
            outputLayer.visible = True
            outputLayer.opacity = 0.5
            outputLayer.shortcutRegistration = (
                "Watershed Layers",
                "Show/Hide Watershed",
                QShortcut( QKeySequence("w"), self.viewerControlWidget(), outputLayer.toggleVisible ),
                outputLayer )
            layers.append(outputLayer)
        
        # Show the watershed seeds
        seedSlot = self.mainOperator.ColoredSeeds[ currentImageIndex ]
        if seedSlot.ready():
            seedLayer = self.createStandardLayerFromSlot( seedSlot, lastChannelIsAlpha=True )
            seedLayer.name = "Watershed Seeds"
            seedLayer.visible = True
            seedLayer.opacity = 0.5
            seedLayer.shortcutRegistration = (
                "Watershed Layers",
                "Show/Hide Watershed Seeds",
                QShortcut( QKeySequence("s"), self.viewerControlWidget(), seedLayer.toggleVisible ),
                seedLayer )
            layers.append(seedLayer)

        selectedInputImageSlot = self.mainOperator.SelectedInputChannels[ currentImageIndex ]
        if selectedInputImageSlot.ready():
            # Show the summed input if there's more than one input channel 
            if len(selectedInputImageSlot) > 1:
                summedSlot = self.mainOperator.SummedInput[ currentImageIndex ]
                if summedSlot.ready():
                    sumLayer = self.createStandardLayerFromSlot( summedSlot )
                    sumLayer.name = "Summed Input"
                    sumLayer.visible = True
                    sumLayer.opacity = 1.0
                    layers.append(sumLayer)

            # Show selected input channels
            inputChannelIndexes = self.mainOperator.InputChannelIndexes.value
            for channel, slot in enumerate(selectedInputImageSlot):
                inputLayer = self.createStandardLayerFromSlot( slot )
                inputLayer.name = "Input (Ch.{})".format(inputChannelIndexes[channel])
                inputLayer.visible = True
                inputLayer.opacity = 1.0
                layers.append(inputLayer)

        # Show the raw input (if provided) 
        rawImageSlot = self.mainOperator.RawImage[ currentImageIndex ]
        if rawImageSlot.ready():
            rawLayer = self.createStandardLayerFromSlot( rawImageSlot )
            rawLayer.name = "Raw Image"
            rawLayer.visible = True
            rawLayer.opacity = 1.0

            def toggleTopToBottom():
                index = self.layerstack.layerIndex( rawLayer )
                self.layerstack.selectRow( index )
                if index == 0:
                    self.layerstack.moveSelectedToBottom()
                else:
                    self.layerstack.moveSelectedToTop()

            rawLayer.shortcutRegistration = (
                "Watershed Layers",
                "Bring Raw Data To Top/Bottom",
                QShortcut( QKeySequence("i"), self.viewerControlWidget(), toggleTopToBottom),
                rawLayer )
            layers.append(rawLayer)

        return layers

    @pyqtSlot()
    @traceLogged(traceLogger)
    def onUpdateWatershedsButton(self):        
        @traceLogged(traceLogger)
        def updateThread():
            """
            Temporarily unfreeze the cache and freeze it again after the views are finished rendering.
            """
            self.mainOperator.FreezeCache.setValue(False)

            # Force the cache to update.
            self.mainOperator.InputImage[self.imageIndex].setDirty( slice(None) )
            
            # Wait for the image to be rendered into all three image views
            time.sleep(2)
            for imgView in self.editor.imageViews:
                imgView.scene().joinRendering()
            self.mainOperator.FreezeCache.setValue(True)

        if self.imageIndex >= 0:
            th = threading.Thread(target=updateThread)
            th.start()

    def getLabelAt(self, currentImageIndex, position5d):
        labelSlot = self.mainOperator.WatershedLabels[currentImageIndex]
        if labelSlot.ready():
            labelData = labelSlot[ index2slice(position5d) ].wait()
            return labelData.squeeze()[()]
        else:
            return None

    def handleEditorLeftClick(self, currentImageIndex, position5d, globalWindowCoordinate):
        """
        This is an override from the base class.  Called when the user clicks in the volume.
        
        For left clicks, we highlight the clicked label.
        """
        label = self.getLabelAt(currentImageIndex, position5d)
        if label != 0 and label is not None:
            overrideSlot = self.mainOperator.OverrideLabels[currentImageIndex]
            overrides = copy.copy(overrideSlot.value)
            overrides[label] = (255, 255, 255, 255)
            overrideSlot.setValue(overrides)
            
    def handleEditorRightClick(self, currentImageIndex, position5d, globalWindowCoordinate):
        """
        This is an override from the base class.  Called when the user clicks in the volume.
        
        For right clicks, we un-highlight the clicked label.
        """
        label = self.getLabelAt(currentImageIndex, position5d)
        overrideSlot = self.mainOperator.OverrideLabels[currentImageIndex]
        overrides = copy.copy(overrideSlot.value)
        if label != 0 and label in overrides:
            del overrides[label]
            overrideSlot.setValue(overrides)
    
    ##
    ## GUI -> Operator
    ##
    def onPaddingChanged(self, value):
        self.mainOperator.WatershedPadding.setValue(value)

    def onBlockShapeChanged(self, value):
        width = self._drawer.blockWidthSpinBox.value()
        depth = self._drawer.blockDepthSpinBox.value()
        self.mainOperator.CacheBlockShape.setValue( (width, depth) )
    
    def onInputSelectionsChanged(self):
        if 0 <= self.imageIndex < len(self.mainOperator.InputImage):
            inputImageSlot = self.mainOperator.InputImage[self.imageIndex]
            if inputImageSlot.ready():
                channelAxis = inputImageSlot.meta.axistags.channelIndex
                numInputChannels = inputImageSlot.meta.shape[channelAxis]
            channels = []
            for i, checkbox in enumerate( self._inputChannelCheckboxes[0:numInputChannels] ):
                if checkbox.isChecked():
                    channels.append(i)
            
            self.mainOperator.InputChannelIndexes.setValue( channels )
    
    def onUseSeedsToggled(self):
        self.updateSeeds()

    def onSeedThresholdChanged(self):
        self.updateSeeds()
        
    def onSeedSizeChanged(self):
        self.updateSeeds()

    def updateSeeds(self):
        useSeeds = self._drawer.useSeedsCheckbox.isChecked()
        self._drawer.seedThresholdSpinBox.setEnabled(useSeeds)
        self._drawer.seedSizeSpinBox.setEnabled(useSeeds)
        if useSeeds:
            threshold = self._drawer.seedThresholdSpinBox.value()
            minSize = self._drawer.seedSizeSpinBox.value()
            self.mainOperator.SeedThresholdValue.setValue( threshold )
            self.mainOperator.MinSeedSize.setValue( minSize )
        else:
            self.mainOperator.SeedThresholdValue.disconnect()

    ##
    ## Operator -> GUI
    ##
    def updatePaddingGui(self, *args):
        padding = self.mainOperator.WatershedPadding.value
        self._drawer.paddingSlider.setValue( padding )
        self._drawer.paddingSpinBox.setValue( padding )

    def updateCacheBlockGui(self, *args):
        width, depth = self.mainOperator.CacheBlockShape.value
        self._drawer.blockWidthSpinBox.setValue( width )
        self._drawer.blockDepthSpinBox.setValue( depth )

    def updateSeedGui(self, *args):
        useSeeds = self.mainOperator.SeedThresholdValue.ready()
        self._drawer.seedThresholdSpinBox.setEnabled(useSeeds)
        self._drawer.seedSizeSpinBox.setEnabled(useSeeds)
        self._drawer.useSeedsCheckbox.setChecked(useSeeds)
        if useSeeds:
            threshold = self.mainOperator.SeedThresholdValue.value
            minSize = self.mainOperator.MinSeedSize.value
            self._drawer.seedThresholdSpinBox.setValue( threshold )
            self._drawer.seedSizeSpinBox.setValue( minSize )

    def updateInputChannelGui(self, *args):
        # Show only checkboxes that can be used (limited by number of input channels)
        numChannels = 0
        if 0 <= self.imageIndex < len(self.mainOperator.InputImage):
            inputImageSlot = self.mainOperator.InputImage[self.imageIndex]
            if inputImageSlot.ready():
                channelAxis = inputImageSlot.meta.axistags.channelIndex
                numChannels = inputImageSlot.meta.shape[channelAxis]
        for i, checkbox in enumerate(self._inputChannelCheckboxes):
#            if i >= numChannels:
#                checkbox.setChecked(False)
            checkbox.setVisible( i < numChannels )

        # Make sure the correct boxes are checked
        if self.mainOperator.InputChannelIndexes.ready():
            inputChannels = self.mainOperator.InputChannelIndexes.value
            for i, checkbox in enumerate( self._inputChannelCheckboxes ):
                checkbox.setChecked( i in inputChannels )

