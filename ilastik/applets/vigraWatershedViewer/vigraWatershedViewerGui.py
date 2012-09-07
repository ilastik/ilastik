from PyQt4 import uic
from PyQt4.QtCore import pyqtSlot

import os
import time
import copy
import threading
from functools import partial

from ilastik.applets.layerViewer import LayerViewerGui
from ilastik.utility import bind

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
        super(VigraWatershedViewerGui, self).__init__( [ mainOperator.InputImage,
                                                         mainOperator.SelectedInputChannels,
                                                         mainOperator.ColoredPixels,
                                                         mainOperator.SummedInput ] )
        self.mainOperator = mainOperator
        self.mainOperator.FreezeCache.setValue(True)
        self.mainOperator.OverrideLabels.setValue( { 0: (0,0,0,0) } )
        self.mainOperator.InputChannelIndexes.setValue( [0,2] )
        self.mainOperator.SeedThresholdValue.setValue( 0.0 )

        # Init padding gui updates        
        self.mainOperator.WatershedPadding.notifyDirty( self.updatePaddingGui )
        self.mainOperator.WatershedPadding.setValue(10)
        self.updatePaddingGui(self.mainOperator.WatershedPadding)

        # Init seeds gui updates
        self.mainOperator.SeedThresholdValue.notifyDirty( self.updateSeedGui )
        self.mainOperator.SeedThresholdValue.notifyReady( self.updateSeedGui )
        self.mainOperator.SeedThresholdValue.notifyUnready( self.updateSeedGui )
        self.updateSeedGui(self.mainOperator.SeedThresholdValue)
        
        # Init input channel gui updates
        self.mainOperator.InputChannelIndexes.notifyDirty( self.updateInputChannelGui )
        self.mainOperator.InputChannelIndexes.setValue( [0] )

        def subscribeToInputMetaChanges(multislot, index):
            multislot[index].notifyMetaChanged( self.updateInputChannelGui )
        self.mainOperator.InputImage.notifyInserted( bind(subscribeToInputMetaChanges) )

        self.updateInputChannelGui( self.mainOperator.InputChannelIndexes )
    
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

        # Padding
        self._drawer.updateWatershedsButton.clicked.connect( self.onUpdateWatershedsButton )
        self._drawer.paddingSlider.valueChanged.connect( self.onPaddingChanged )
        self._drawer.paddingSpinBox.valueChanged.connect( self.onPaddingChanged )

                
    def getAppletDrawerUi(self):
        return self._drawer
    
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
            layers.append(outputLayer)
        
        # Show the summed input 
        summedSlot = self.mainOperator.SummedInput[ currentImageIndex ]
        if summedSlot.ready():
            sumLayer = self.createStandardLayerFromSlot( summedSlot )
            sumLayer.name = "Summed Input"
            sumLayer.visible = True
            sumLayer.opacity = 1.0
            layers.append(sumLayer)

        # Show selected input channels
        selectedInputImageSlot = self.mainOperator.SelectedInputChannels[ currentImageIndex ]
        if selectedInputImageSlot.ready():
            inputChannelIndexes = self.mainOperator.InputChannelIndexes.value
            for channel, slot in enumerate(selectedInputImageSlot):
                inputLayer = self.createStandardLayerFromSlot( slot )
                inputLayer.name = "Raw Input (Ch.{})".format(inputChannelIndexes[channel])
                inputLayer.visible = True
                inputLayer.opacity = 1.0
                layers.append(inputLayer)

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

    def handleEditorLeftClick(self, currentImageIndex, position5d):
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
            
    def handleEditorRightClick(self, currentImageIndex, position5d):
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
    
    def onPaddingChanged(self, value):
        self.mainOperator.WatershedPadding.setValue(value)
    
    def updatePaddingGui(self, slot, *args):
        value = slot.value
        self._drawer.paddingSlider.setValue( value )
        self._drawer.paddingSpinBox.setValue( value )

    def updateSeedGui(self, slot, *args):
        useSeeds = self.mainOperator.SeedThresholdValue.ready()
        self._drawer.seedThresholdSpinBox.setEnabled(useSeeds)
        self._drawer.useSeedsCheckbox.setChecked(useSeeds)
        if useSeeds:
            threshold = self.mainOperator.SeedThresholdValue.value
            self._drawer.seedThresholdSpinBox.setValue( threshold )

    def updateInputChannelGui(self, *args):
        # Show only checkboxes that can be used (limited by number of input channels)
        inputImageSlot = self.mainOperator.InputImage[self.imageIndex]
        if inputImageSlot.ready():
            channelAxis = inputImageSlot.meta.axistags.channelIndex
            numChannels = inputImageSlot.meta.shape[channelAxis]
            for i, checkbox in enumerate(self._inputChannelCheckboxes):
                if i >= numChannels:
                    checkbox.setChecked(False)
                checkbox.setVisible( i < numChannels )

        # Make sure the correct boxes are checked
        if self.mainOperator.InputChannelIndexes.ready():
            inputChannels = self.mainOperator.InputChannelIndexes.value
            for i, checkbox in enumerate( self._inputChannelCheckboxes ):
                checkbox.setChecked( i in inputChannels )

    def onInputSelectionsChanged(self):
        channels = []
        for i, checkbox in enumerate( self._inputChannelCheckboxes ):
            if checkbox.isChecked():
                channels.append(i)
        
        self.mainOperator.InputChannelIndexes.setValue( channels )
    
    def onUseSeedsToggled(self):
        self.updateSeeds()

    def onSeedThresholdChanged(self):
        self.updateSeeds()

    def updateSeeds(self):
        useSeeds = self._drawer.useSeedsCheckbox.isChecked()
        self._drawer.seedThresholdSpinBox.setEnabled(useSeeds)
        if useSeeds:
            threshold = self._drawer.seedThresholdSpinBox.value()
            self.mainOperator.SeedThresholdValue.setValue( threshold )
        else:
            self.mainOperator.SeedThresholdValue.disconnect()

