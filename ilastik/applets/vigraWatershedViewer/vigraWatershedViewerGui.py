from PyQt4 import uic
from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import QShortcut, QKeySequence

import os
import time
import copy
import threading
from functools import partial

import numpy

from volumina.utility import PreferencesManager
from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui
from ilastik.utility import bind
from ilastik.utility.gui import ThunkEventHandler

from volumina.slicingtools import index2slice

import logging
logger = logging.getLogger(__name__)
traceLogger = logging.getLogger('TRACE.' + __name__)
from lazyflow.utility import traceLogged

class VigraWatershedViewerGui(LayerViewerGui):
    """
    """
    
    ###########################################
    ### AppletGuiInterface Concrete Methods ###
    ###########################################
    
    def appletDrawer(self):
        return self.getAppletDrawerUi()

    # (Other methods already provided by our base class)

    ###########################################
    ###########################################
    
    @traceLogged(traceLogger)
    def __init__(self, topLevelOperatorView):
        """
        """
        super(VigraWatershedViewerGui, self).__init__( topLevelOperatorView )
        self.topLevelOperatorView = topLevelOperatorView
        
        self.topLevelOperatorView.FreezeCache.setValue(True)
        self.topLevelOperatorView.OverrideLabels.setValue( { 0: (0,0,0,0) } )

        # Default settings (will be overwritten by serializer)
        self.topLevelOperatorView.InputChannelIndexes.setValue( [] )
        self.topLevelOperatorView.SeedThresholdValue.setValue( 0.0 )
        self.topLevelOperatorView.MinSeedSize.setValue( 0 )

        # Init padding gui updates
        blockPadding = PreferencesManager().get( 'vigra watershed viewer', 'block padding', 10)
        self.topLevelOperatorView.WatershedPadding.notifyDirty( self.updatePaddingGui )
        self.topLevelOperatorView.WatershedPadding.setValue(blockPadding)
        self.updatePaddingGui()
        
        # Init block shape gui updates
        cacheBlockShape = PreferencesManager().get( 'vigra watershed viewer', 'cache block shape', (256, 10))
        self.topLevelOperatorView.CacheBlockShape.notifyDirty( self.updateCacheBlockGui )
        self.topLevelOperatorView.CacheBlockShape.setValue( cacheBlockShape )
        self.updateCacheBlockGui()

        # Init seeds gui updates
        self.topLevelOperatorView.SeedThresholdValue.notifyDirty( self.updateSeedGui )
        self.topLevelOperatorView.SeedThresholdValue.notifyReady( self.updateSeedGui )
        self.topLevelOperatorView.SeedThresholdValue.notifyUnready( self.updateSeedGui )
        self.topLevelOperatorView.MinSeedSize.notifyDirty( self.updateSeedGui )
        self.updateSeedGui()
        
        # Init input channel gui updates
        self.topLevelOperatorView.InputChannelIndexes.notifyDirty( self.updateInputChannelGui )
        self.topLevelOperatorView.InputChannelIndexes.setValue( [0] )
        self.topLevelOperatorView.InputImage.notifyMetaChanged( bind(self.updateInputChannelGui) )
        self.updateInputChannelGui()

        self.thunkEventHandler = ThunkEventHandler(self)
    
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
        if self.topLevelOperatorView.CacheBlockShape.ready() and self.topLevelOperatorView.WatershedPadding.ready():
            with PreferencesManager() as prefsMgr:
                prefsMgr.set( 'vigra watershed viewer', 'cache block shape', self.topLevelOperatorView.CacheBlockShape.value )
                prefsMgr.set( 'vigra watershed viewer', 'block padding', self.topLevelOperatorView.WatershedPadding.value )
        super( VigraWatershedViewerGui, self ).hideEvent(event)
    
    @traceLogged(traceLogger)
    def setupLayers(self):
        layers = []

        self.updateInputChannelGui()
        
        # Show the watershed data
        outputImageSlot = self.topLevelOperatorView.ColoredPixels
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
        seedSlot = self.topLevelOperatorView.ColoredSeeds
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

        selectedInputImageSlot = self.topLevelOperatorView.SelectedInputChannels
        if selectedInputImageSlot.ready():
            # Show the summed input if there's more than one input channel 
            if len(selectedInputImageSlot) > 1:
                summedSlot = self.topLevelOperatorView.SummedInput
                if summedSlot.ready():
                    sumLayer = self.createStandardLayerFromSlot( summedSlot )
                    sumLayer.name = "Summed Input"
                    sumLayer.visible = True
                    sumLayer.opacity = 1.0
                    layers.append(sumLayer)

            # Show selected input channels
            inputChannelIndexes = self.topLevelOperatorView.InputChannelIndexes.value
            for channel, slot in enumerate(selectedInputImageSlot):
                inputLayer = self.createStandardLayerFromSlot( slot )
                inputLayer.name = "Input (Ch.{})".format(inputChannelIndexes[channel])
                inputLayer.visible = True
                inputLayer.opacity = 1.0
                layers.append(inputLayer)

        # Show the raw input (if provided) 
        rawImageSlot = self.topLevelOperatorView.RawImage
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
            self.topLevelOperatorView.FreezeCache.setValue(False)
            self.topLevelOperatorView.opWatershed.clearMaxLabels()

            # Force the cache to update.
            self.topLevelOperatorView.InputImage.setDirty( slice(None) )
            
            # Wait for the image to be rendered into all three image views
            time.sleep(2)
            for imgView in self.editor.imageViews:
                imgView.scene().joinRendering()
            self.topLevelOperatorView.FreezeCache.setValue(True)

            self.updateSupervoxelStats()

        th = threading.Thread(target=updateThread)
        th.start()

    def updateSupervoxelStats(self):
        """
        Use the accumulated state in the watershed operator to display the stats for the most recent watershed computation.
        """
        totalVolume = 0
        totalCount = 0
        for (start, stop), maxLabel in  self.topLevelOperatorView.opWatershed.maxLabels.items():
            blockshape = numpy.subtract(stop, start)
            vol = numpy.prod(blockshape)
            totalVolume += vol
            
            totalCount += maxLabel
        
        vol_caption = "Refresh Volume: {} megavox".format( totalVolume / float(1000 * 1000) )
        count_caption = "Supervoxel Count: {}".format( totalCount )
        if totalVolume != 0:
            density_caption = "Density: {} supervox/megavox".format( totalCount * float(1000 * 1000) / totalVolume )
        else:
            density_caption = ""
        
        # Update the GUI text, but do it in the GUI thread (even if we were called from a worker thread)
        self.thunkEventHandler.post( self._drawer.refreshVolumeLabel.setText,  vol_caption )
        self.thunkEventHandler.post( self._drawer.superVoxelCountLabel.setText,  count_caption )
        self.thunkEventHandler.post( self._drawer.densityLabel.setText,  density_caption )

    def getLabelAt(self, position5d):
        labelSlot = self.topLevelOperatorView.WatershedLabels
        if labelSlot.ready():
            labelData = labelSlot[ index2slice(position5d) ].wait()
            return labelData.squeeze()[()]
        else:
            return None

    def handleEditorLeftClick(self, position5d, globalWindowCoordinate):
        """
        This is an override from the base class.  Called when the user clicks in the volume.
        
        For left clicks, we highlight the clicked label.
        """
        label = self.getLabelAt(position5d)
        if label != 0 and label is not None:
            overrideSlot = self.topLevelOperatorView.OverrideLabels
            overrides = copy.copy(overrideSlot.value)
            overrides[label] = (255, 255, 255, 255)
            overrideSlot.setValue(overrides)
            
    def handleEditorRightClick(self, position5d, globalWindowCoordinate):
        """
        This is an override from the base class.  Called when the user clicks in the volume.
        
        For right clicks, we un-highlight the clicked label.
        """
        label = self.getLabelAt(position5d)
        overrideSlot = self.topLevelOperatorView.OverrideLabels
        overrides = copy.copy(overrideSlot.value)
        if label != 0 and label in overrides:
            del overrides[label]
            overrideSlot.setValue(overrides)
    
    ##
    ## GUI -> Operator
    ##
    def onPaddingChanged(self, value):
        self.topLevelOperatorView.WatershedPadding.setValue(value)

    def onBlockShapeChanged(self, value):
        width = self._drawer.blockWidthSpinBox.value()
        depth = self._drawer.blockDepthSpinBox.value()
        self.topLevelOperatorView.CacheBlockShape.setValue( (width, depth) )
    
    def onInputSelectionsChanged(self):
        inputImageSlot = self.topLevelOperatorView.InputImage
        if inputImageSlot.ready():
            channelAxis = inputImageSlot.meta.axistags.channelIndex
            numInputChannels = inputImageSlot.meta.shape[channelAxis]
        else:
            numInputChannels = 0
        channels = []
        for i, checkbox in enumerate( self._inputChannelCheckboxes[0:numInputChannels] ):
            if checkbox.isChecked():
                channels.append(i)
        
        self.topLevelOperatorView.InputChannelIndexes.setValue( channels )
    
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
            self.topLevelOperatorView.SeedThresholdValue.setValue( threshold )
            self.topLevelOperatorView.MinSeedSize.setValue( minSize )
        else:
            self.topLevelOperatorView.SeedThresholdValue.disconnect()

    ##
    ## Operator -> GUI
    ##
    def updatePaddingGui(self, *args):
        padding = self.topLevelOperatorView.WatershedPadding.value
        self._drawer.paddingSlider.setValue( padding )
        self._drawer.paddingSpinBox.setValue( padding )

    def updateCacheBlockGui(self, *args):
        width, depth = self.topLevelOperatorView.CacheBlockShape.value
        self._drawer.blockWidthSpinBox.setValue( width )
        self._drawer.blockDepthSpinBox.setValue( depth )

    def updateSeedGui(self, *args):
        useSeeds = self.topLevelOperatorView.SeedThresholdValue.ready()
        self._drawer.seedThresholdSpinBox.setEnabled(useSeeds)
        self._drawer.seedSizeSpinBox.setEnabled(useSeeds)
        self._drawer.useSeedsCheckbox.setChecked(useSeeds)
        if useSeeds:
            threshold = self.topLevelOperatorView.SeedThresholdValue.value
            minSize = self.topLevelOperatorView.MinSeedSize.value
            self._drawer.seedThresholdSpinBox.setValue( threshold )
            self._drawer.seedSizeSpinBox.setValue( minSize )

    def updateInputChannelGui(self, *args):
        # Show only checkboxes that can be used (limited by number of input channels)
        numChannels = 0
        inputImageSlot = self.topLevelOperatorView.InputImage
        if inputImageSlot.ready():
            channelAxis = inputImageSlot.meta.axistags.channelIndex
            numChannels = inputImageSlot.meta.shape[channelAxis]
        for i, checkbox in enumerate(self._inputChannelCheckboxes):
#            if i >= numChannels:
#                checkbox.setChecked(False)
            checkbox.setVisible( i < numChannels )

        # Make sure the correct boxes are checked
        if self.topLevelOperatorView.InputChannelIndexes.ready():
            inputChannels = self.topLevelOperatorView.InputChannelIndexes.value
            for i, checkbox in enumerate( self._inputChannelCheckboxes ):
                checkbox.setChecked( i in inputChannels )

