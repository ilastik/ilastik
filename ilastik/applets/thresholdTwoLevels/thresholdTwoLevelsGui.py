###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#		   http://ilastik.org/license.html
###############################################################################
import os
import logging
from functools import partial

from PyQt4 import uic
from PyQt4.QtCore import Qt, QEvent
from PyQt4.QtGui import QColor, QPixmap, QIcon
from PyQt4.QtGui import QMessageBox

from volumina.api import LazyflowSource, AlphaModulatedLayer, ColortableLayer
from volumina.colortables import create_default_16bit
from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui
from ilastik.utility import bind
from ilastik.utility.gui import threadRouted 
from lazyflow.operators.generic import OpSingleChannelSelector

from opThresholdTwoLevels import ThresholdMethod

from opGraphcutSegment import haveGraphCut

# always available
import numpy as np

logger = logging.getLogger(__name__)
traceLogger = logging.getLogger("TRACE." + __name__)

class ThresholdTwoLevelsGui( LayerViewerGui ):
    _defaultInputChannelColors = None
    def stopAndCleanUp(self):
        # Unsubscribe to all signals
        for fn in self.__cleanup_fns:
            fn()

        super(ThresholdTwoLevelsGui, self).stopAndCleanUp()
    
    def __init__(self, *args, **kwargs):
        self.__cleanup_fns = []
        super( ThresholdTwoLevelsGui, self ).__init__(*args, **kwargs)
        self._defaultInputChannelColors = self._createDefault16ColorColorTable()

        self._onInputMetaChanged()

        # connect callbacks last -> avoid undefined behaviour
        self._connectCallbacks()

    def initAppletDrawerUi(self):
        """
        Reimplemented from LayerViewerGui base class.
        """
        # Load the ui file (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        self._drawer = uic.loadUi(localDir+"/drawer.ui")

        # disable graph cut applet if not available
        if not haveGraphCut():
            self._drawer.tabWidget.setTabEnabled(2, False)

        self._sigmaSpinBoxes = { 'x' : self._drawer.sigmaSpinBox_X,
                                 'y' : self._drawer.sigmaSpinBox_Y,
                                 'z' : self._drawer.sigmaSpinBox_Z }

        self._allWatchedWidgets = self._sigmaSpinBoxes.values() + \
        [
            self._drawer.inputChannelComboBox,
            self._drawer.lowThresholdSpinBox,
            self._drawer.highThresholdSpinBox,
            self._drawer.thresholdSpinBox,
            self._drawer.minSizeSpinBox,
            self._drawer.maxSizeSpinBox,
            self._drawer.thresholdSpinBoxGC,
            self._drawer.lambdaSpinBoxGC
        ]
        
        for widget in self._allWatchedWidgets:
            # If the user pressed enter inside a spinbox, auto-click "Apply"
            widget.installEventFilter( self )
        
        self._drawer.showDebugCheckbox.stateChanged.connect( self._onShowDebugChanged )
        self._showDebug = False
        
        self._updateGuiFromOperator()
        self.topLevelOperatorView.InputImage.notifyReady( bind(self._updateGuiFromOperator) )
        self.__cleanup_fns.append( partial( self.topLevelOperatorView.InputImage.unregisterUnready, bind(self._updateGuiFromOperator) ) )

        self.topLevelOperatorView.InputImage.notifyMetaChanged( bind(self._updateGuiFromOperator) )
        self.__cleanup_fns.append( partial( self.topLevelOperatorView.InputImage.unregisterMetaChanged, bind(self._updateGuiFromOperator) ) )

    def _connectCallbacks(self):
        self.topLevelOperatorView.InputImage.notifyMetaChanged(bind(self._onInputMetaChanged))
        self._drawer.applyButton.clicked.connect(self._onApplyButtonClicked)
        self._drawer.tabWidget.currentChanged.connect(bind(self._onTabCurrentChanged))

    def showEvent(self, event):
        super( ThresholdTwoLevelsGui, self ).showEvent(event)
        self._updateGuiFromOperator()

    @threadRouted
    def _updateGuiFromOperator(self):
        op = self.topLevelOperatorView

        # check if the data is 2D. If so, hide the z-dependent spinboxes
        data_has_z_axis = True
        if self.topLevelOperatorView.InputImage.ready():
            tShape = self.topLevelOperatorView.InputImage.meta.getTaggedShape()
            if not 'z' in tShape or tShape['z']==1:
                data_has_z_axis = False

        self._drawer.sigmaSpinBox_Z.setVisible(data_has_z_axis)
        self._drawer.marginSpinBoxGC_Z.setVisible(data_has_z_axis)

        numChannels = 0
        if op.InputImage.ready():
            # Channel
            channelIndex = op.InputImage.meta.axistags.index('c')
            numChannels = op.InputImage.meta.shape[channelIndex]

        if op.InputChannelColors.ready():
            input_channel_colors = map(lambda (r,g,b): QColor(r,g,b), op.InputChannelColors.value)
        else:
            if self._defaultInputChannelColors is None:
                self._defaultInputChannelColors = self._createDefault16ColorColorTable()
            input_channel_colors = map(QColor, self._defaultInputChannelColors)
        for ichannel in range(numChannels):
            # make an icon
            pm = QPixmap(16, 16)
            pm.fill(input_channel_colors[ichannel])
            self._drawer.inputChannelComboBox.insertItem(ichannel, QIcon(pm), "Input Channel "+ str(ichannel))

        self._drawer.inputChannelComboBox.setCurrentIndex( op.Channel.value )

        # Sigmas
        sigmaDict = self.topLevelOperatorView.SmootherSigma.value
        for axiskey, spinBox in self._sigmaSpinBoxes.items():
            spinBox.setValue( sigmaDict[axiskey] )

        # Thresholds
        self._drawer.lowThresholdSpinBox.setValue( op.LowThreshold.value )
        self._drawer.highThresholdSpinBox.setValue( op.HighThreshold.value )
        self._drawer.thresholdSpinBox.setValue( op.LowThreshold.value )
        self._drawer.thresholdSpinBoxGC.setValue( op.LowThreshold.value )
        self._drawer.lambdaSpinBoxGC.setValue( op.Beta.value )
        margin = op.Margin.value
        self._drawer.marginSpinBoxGC_X.setValue(margin[0])
        self._drawer.marginSpinBoxGC_Y.setValue(margin[1])
        self._drawer.marginSpinBoxGC_Z.setValue(margin[2])
        if op.UsePreThreshold.value:
            self._drawer.radioButtonGC_local.setChecked(True)
        else:
            self._drawer.radioButtonGC_global.setChecked(True)

        # Size filters
        self._drawer.minSizeSpinBox.setValue( op.MinSize.value )
        self._drawer.maxSizeSpinBox.setValue( op.MaxSize.value )

        # Operator
        tab_index = {0:0, 1:1, 2:2, 3:1}[op.CurOperator.value]
        self._drawer.tabWidget.setCurrentIndex( tab_index )
        self._drawer.preserveIdentitiesCheckbox.setChecked(op.CurOperator.value == 3)

    def _updateOperatorFromGui(self):
        op = self.topLevelOperatorView

        # Read all gui settings before updating the operator
        # (The gui is still responding to operator changes, 
        #  and we don't want it to update until we've read all gui values.)

        # Read Channel
        channel = self._drawer.inputChannelComboBox.currentIndex()

        # Read Sigmas
        sigmaSlot = self.topLevelOperatorView.SmootherSigma
        block_shape_dict = dict( sigmaSlot.value )
        block_shape_dict['x'] = self._sigmaSpinBoxes['x'].value()
        block_shape_dict['y'] = self._sigmaSpinBoxes['y'].value()
        block_shape_dict['z'] = self._sigmaSpinBoxes['z'].value()
        neededAxes = 'xyz' if self._drawer.sigmaSpinBox_Z.isVisible() else 'xy'
        sigmaIsZero = [block_shape_dict[index] < .1 for index in neededAxes]
        if any(sigmaIsZero) and not all(sigmaIsZero):
            mexBox = QMessageBox()
            mexBox.setText("One of the smoothing sigma values is 0. Reset it to a value > 0.1 or set all sigmas to 0 for no smoothing.")
            mexBox.exec_()
            return

        # avoid 'kernel longer than line' errors
        shape = self.topLevelOperatorView.InputImage.meta.getTaggedShape()
        for ax in [item for item in 'xyz' if item in shape and shape[item] > 1]:
            req_sigma = np.floor(shape[ax]/3)
            if block_shape_dict[ax] > req_sigma:
                mexBox = QMessageBox()
                mexBox.setText("The sigma value {} for dimension '{}'"
                               "is too high, should be at most {:.1f}.".format(
                                   block_shape_dict[ax], ax, req_sigma))
                mexBox.exec_()
                return

        # Read Thresholds
        singleThreshold = self._drawer.thresholdSpinBox.value()
        lowThreshold = self._drawer.lowThresholdSpinBox.value()
        highThreshold = self._drawer.highThresholdSpinBox.value()
        singleThresholdGC = self._drawer.thresholdSpinBoxGC.value()
        beta = self._drawer.lambdaSpinBoxGC.value()
        margin = [self._drawer.marginSpinBoxGC_X.value(),
                  self._drawer.marginSpinBoxGC_Y.value(),
                  self._drawer.marginSpinBoxGC_Z.value()]
        margin = np.asarray(margin)

        if lowThreshold>highThreshold:
            mexBox=QMessageBox()
            mexBox.setText("Low threshold must be lower than high threshold ")
            mexBox.exec_()
            return

        # Read Size filters
        minSize = self._drawer.minSizeSpinBox.value()
        maxSize = self._drawer.maxSizeSpinBox.value()

        if minSize>=maxSize:
            mexBox=QMessageBox()
            mexBox.setText("Min size must be smaller than max size ")
            mexBox.exec_()
            return

        # Read the current thresholding method
        curIndex = self._drawer.tabWidget.currentIndex()

        op_index = curIndex
        if curIndex == 1 and self._drawer.preserveIdentitiesCheckbox.isChecked():
            curIndex = 3
        # Apply new settings to the operator
        op.CurOperator.setValue(curIndex)
        op.Channel.setValue(channel)
        sigmaSlot.setValue(block_shape_dict)
        if curIndex == ThresholdMethod.SIMPLE:
            op.LowThreshold.setValue(singleThreshold)
        elif curIndex in (ThresholdMethod.HYSTERESIS, ThresholdMethod.IPHT):
            op.LowThreshold.setValue(lowThreshold)
        elif curIndex == ThresholdMethod.GRAPHCUT:
            op.LowThreshold.setValue(singleThresholdGC)
        else:
            assert False, "Unsupported method"
        

        op.HighThreshold.setValue( highThreshold )
        
        op.Beta.setValue(beta)
        op.Margin.setValue(margin)
        op.MinSize.setValue(minSize)
        op.MaxSize.setValue(maxSize)
        op.UsePreThreshold.setValue(
            self._drawer.radioButtonGC_local.isChecked())

    def _onApplyButtonClicked(self):
        self._updateOperatorFromGui()
        for layer in self.layerstack:
            if "Final" in layer.name:
                layer.visible = True
        self.updateAllLayers()

    def _onTabCurrentChanged(self):
        pass
        # not needed, we update ONLY on apply button
        #self._updateOperatorFromGui()
        #not needed, LayerViewerGui monitors op.CurOperator
        #self.updateAllLayers()

    def _onShowDebugChanged(self, state):
        if state==Qt.Checked:
            self._showDebug = True
            self.updateAllLayers()
        else:
            self._showDebug = False
            self.updateAllLayers()

    def eventFilter(self, watched, event):
        """
        If the user pressed 'enter' within a spinbox, auto-click the "apply" button.
        """
        if watched in self._allWatchedWidgets:
            if  event.type() == QEvent.KeyPress and\
              ( event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return):
                self._drawer.applyButton.click()
                return True
        return False

    def _onInputMetaChanged(self):
        op = self.topLevelOperatorView
        self._channelProviders = []
        if not op.InputImage.ready():
            return

        numChannels = op.InputImage.meta.getTaggedShape()['c']
        for channel in range(numChannels):
            channelProvider = OpSingleChannelSelector(parent=op.InputImage.getRealOperator().parent)
            channelProvider.Input.connect(op.InputImage)
            channelProvider.Index.setValue(channel)
            self._channelProviders.append(channelProvider)

    def setupLayers(self):
        layers = []
        op = self.topLevelOperatorView
        binct = [QColor(Qt.black), QColor(Qt.white)]
        binct[0] = 0
        ct = create_default_16bit()
        ct[0] = 0
        # Show the cached output, since it goes through a blocked cache

        if op.CachedOutput.ready():
            outputSrc = LazyflowSource(op.CachedOutput)
            outputLayer = ColortableLayer(outputSrc, ct)
            outputLayer.name = "Final output"
            outputLayer.visible = False
            outputLayer.opacity = 1.0
            outputLayer.setToolTip("Results of thresholding and size filter")
            layers.append(outputLayer)

        if op.InputChannelColors.ready():
            input_channel_colors = map(lambda (r,g,b): QColor(r,g,b), op.InputChannelColors.value)
        else:
            input_channel_colors = map(QColor, self._defaultInputChannelColors)
        for channel, channelProvider in enumerate(self._channelProviders):
            slot_drange = channelProvider.Output.meta.drange
            if slot_drange is not None:
                drange = slot_drange
            else:
                drange = (0.0, 1.0)
            channelSrc = LazyflowSource(channelProvider.Output)
            inputChannelLayer = AlphaModulatedLayer(
                channelSrc, tintColor=input_channel_colors[channel],
                range=drange, normalize=drange)
            inputChannelLayer.opacity = 0.5
            inputChannelLayer.visible = True
            inputChannelLayer.name = "Input Channel " + str(channel)
            inputChannelLayer.setToolTip("Select input channel " + str(channel) + \
                                            " if this prediction image contains the objects of interest.")                    
            layers.append(inputChannelLayer)

        if self._showDebug:
            #FIXME: We have to do that, because lazyflow doesn't have a way to make an operator partially ready
            curIndex = op.CurOperator.value
            if curIndex==1:
                if op.BigRegions.ready():
                    lowThresholdSrc = LazyflowSource(op.BigRegions)
                    lowThresholdLayer = ColortableLayer(lowThresholdSrc, binct)
                    lowThresholdLayer.name = "After low threshold"
                    lowThresholdLayer.visible = False
                    lowThresholdLayer.opacity = 1.0
                    lowThresholdLayer.setToolTip("Results of thresholding with the low pixel value threshold")
                    layers.append(lowThresholdLayer)
        
                if op.FilteredSmallLabels.ready():
                    filteredSmallLabelsSrc = LazyflowSource(op.FilteredSmallLabels)
                    #filteredSmallLabelsLayer = self.createStandardLayerFromSlot( op.FilteredSmallLabels )
                    filteredSmallLabelsLayer = ColortableLayer(filteredSmallLabelsSrc, binct)
                    filteredSmallLabelsLayer.name = "After high threshold and size filter"
                    filteredSmallLabelsLayer.visible = False
                    filteredSmallLabelsLayer.opacity = 1.0
                    filteredSmallLabelsLayer.setToolTip("Results of thresholding with the high pixel value threshold,\
                                                         followed by the size filter")
                    layers.append(filteredSmallLabelsLayer)
        
                if op.SmallRegions.ready():
                    highThresholdSrc = LazyflowSource(op.SmallRegions)
                    highThresholdLayer = ColortableLayer(highThresholdSrc, binct)
                    highThresholdLayer.name = "After high threshold"
                    highThresholdLayer.visible = False
                    highThresholdLayer.opacity = 1.0
                    highThresholdLayer.setToolTip("Results of thresholding with the high pixel value threshold")
                    layers.append(highThresholdLayer)
            elif curIndex==0:
                if op.BeforeSizeFilter.ready():
                    thSrc = LazyflowSource(op.BeforeSizeFilter)
                    thLayer = ColortableLayer(thSrc, ct)
                    thLayer.name = "Before size filter"
                    thLayer.visible = False
                    thLayer.opacity = 1.0
                    thLayer.setToolTip("Results of thresholding before the size filter is applied")
                    layers.append(thLayer)
            
            # Selected input channel, smoothed.
            if op.Smoothed.ready():
                smoothedLayer = self.createStandardLayerFromSlot( op.Smoothed )
                smoothedLayer.name = "Smoothed input"
                smoothedLayer.visible = True
                smoothedLayer.opacity = 1.0
                smoothedLayer.setToolTip("Selected channel data, smoothed with a Gaussian with user-defined sigma")
                layers.append(smoothedLayer)
                
        
        # Show the raw input data
        rawSlot = self.topLevelOperatorView.RawInput
        if rawSlot.ready():
            rawLayer = self.createStandardLayerFromSlot( rawSlot )
            rawLayer.name = "Raw data"
            rawLayer.visible = True
            rawLayer.opacity = 1.0
            layers.append(rawLayer)

        return layers

    #FIXME: why do we do it here? why not take the one from volumina?
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
