from __future__ import absolute_import
from __future__ import division
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
from builtins import range
from past.utils import old_div
import os
import logging
from functools import partial

import numpy as np

from PyQt5 import uic
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QColor, QPixmap, QIcon
from PyQt5.QtWidgets import QMessageBox

from volumina.api import LazyflowSource, AlphaModulatedLayer, ColortableLayer
from volumina import colortables
from volumina.colortables import create_default_16bit
from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui
from ilastik.utility import bind
from ilastik.utility.gui import threadRouted 
from lazyflow.operators.generic import OpSingleChannelSelector

from .opThresholdTwoLevels import ThresholdMethod, _has_graphcut

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
<<<<<<< 0cc75154bcba04da1e80833b8320133626126a53
        self._defaultInputChannelColors = colortables.default16_new[1:] #first color is transparent
=======
        self._defaultInputChannelColors = colortables.default16_new
>>>>>>> make all gui classes use the colortable16 from volumina.colortables

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

        self._drawer.methodComboBox.addItem("Simple")
        self._drawer.methodComboBox.addItem("Hysteresis")
        if _has_graphcut:
            self._drawer.methodComboBox.addItem("Graph Cut")
            

        self._sigmaSpinBoxes = { 'x' : self._drawer.sigmaSpinBox_X,
                                 'y' : self._drawer.sigmaSpinBox_Y,
                                 'z' : self._drawer.sigmaSpinBox_Z }

        self._allWatchedWidgets = list(self._sigmaSpinBoxes.values()) + \
        [
            self._drawer.inputChannelComboBox,
            self._drawer.coreChannelComboBox,
            self._drawer.lowThresholdSpinBox,
            self._drawer.highThresholdSpinBox,
            self._drawer.minSizeSpinBox,
            self._drawer.maxSizeSpinBox,
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
        self._drawer.methodComboBox.currentIndexChanged.connect( self._enableMethodSpecificControls )
        self._drawer.preserveIdentitiesCheckbox.stateChanged.connect( self._enableMethodSpecificControls )

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

        numChannels = 0
        if op.InputImage.ready():
            # Channel
            channelIndex = op.InputImage.meta.axistags.index('c')
            numChannels = op.InputImage.meta.shape[channelIndex]

        if op.InputChannelColors.ready():
            input_channel_colors = [QColor(r_g_b[0],r_g_b[1],r_g_b[2]) for r_g_b in op.InputChannelColors.value]
        else:
            if self._defaultInputChannelColors is None:
                self._defaultInputChannelColors = colortables.default16_new[1:]

            input_channel_colors = list(map(QColor, self._defaultInputChannelColors))

        self._drawer.inputChannelComboBox.clear()
        self._drawer.coreChannelComboBox.clear()
        
        for ichannel in range(numChannels):
            # make an icon
            pm = QPixmap(16, 16)
            pm.fill(input_channel_colors[ichannel])
            self._drawer.inputChannelComboBox.insertItem(ichannel, QIcon(pm), str(ichannel))
            self._drawer.coreChannelComboBox.insertItem(ichannel, QIcon(pm), str(ichannel))

        self._drawer.inputChannelComboBox.setCurrentIndex( op.Channel.value )
        self._drawer.coreChannelComboBox.setCurrentIndex( op.CoreChannel.value )

        # Sigmas
        sigmaDict = self.topLevelOperatorView.SmootherSigma.value
        for axiskey, spinBox in list(self._sigmaSpinBoxes.items()):
            spinBox.setValue( sigmaDict[axiskey] )

        # Thresholds
        self._drawer.lowThresholdSpinBox.setValue( op.LowThreshold.value )
        self._drawer.highThresholdSpinBox.setValue( op.HighThreshold.value )
        self._drawer.lambdaSpinBoxGC.setValue( op.Beta.value )

        # Size filters
        self._drawer.minSizeSpinBox.setValue( op.MinSize.value )
        self._drawer.maxSizeSpinBox.setValue( op.MaxSize.value )

        # Operator
        method = op.CurOperator.value
        
        # There isn't a 1-to-1 correspondence between the combo widget and ThresholdingMethod
        # Methods 0,1,2 are 1-to-1, but method 3 means "two-level, but don't merge cores."
        method_combo_index = {0:0, 1:1, 2:2, 3:1}[method]
        self._drawer.methodComboBox.setCurrentIndex( method_combo_index )
        self._drawer.preserveIdentitiesCheckbox.setChecked(op.CurOperator.value == 3)
        
        self._enableMethodSpecificControls()

    def _enableMethodSpecificControls(self):
        method = self._drawer.methodComboBox.currentIndex()
        if method == 1 and self._drawer.preserveIdentitiesCheckbox.isChecked():
            method = 3

        # Show/hide some controls depending on the selected method
        show_hysteresis_controls = (method in (ThresholdMethod.HYSTERESIS, ThresholdMethod.IPHT))
        self._drawer.highThresholdSpinBox.setVisible( show_hysteresis_controls )
        self._drawer.highThresholdLabel.setVisible( show_hysteresis_controls )
        self._drawer.preserveIdentitiesCheckbox.setVisible( show_hysteresis_controls )
        self._drawer.coreChannelComboBox.setVisible( show_hysteresis_controls )
        self._drawer.coreChannelLabel.setVisible( show_hysteresis_controls )
        self._drawer.finalChannelLabel.setVisible( show_hysteresis_controls )
        self._drawer.lowThresholdLabel.setVisible( show_hysteresis_controls )

        show_graphcut_controls = (method == ThresholdMethod.GRAPHCUT)
        self._drawer.lambdaLabel.setVisible( show_graphcut_controls )
        self._drawer.lambdaSpinBoxGC.setVisible( show_graphcut_controls )
        self._drawer.layout().update()

    def _updateOperatorFromGui(self):
        op = self.topLevelOperatorView

        # Read all gui settings before updating the operator
        # (The gui is still responding to operator changes, 
        #  and we don't want it to update until we've read all gui values.)

        # Read Channel
        final_channel = self._drawer.inputChannelComboBox.currentIndex()
        core_channel = self._drawer.coreChannelComboBox.currentIndex()

        # Read Sigmas
        block_shape_dict = dict( op.SmootherSigma.value )
        block_shape_dict['x'] = self._sigmaSpinBoxes['x'].value()
        block_shape_dict['y'] = self._sigmaSpinBoxes['y'].value()
        block_shape_dict['z'] = self._sigmaSpinBoxes['z'].value()
        neededAxes = 'zyx' if self._drawer.sigmaSpinBox_Z.isVisible() else 'yx'
        sigmaIsZero = [block_shape_dict[index] < .1 for index in neededAxes]
        if any(sigmaIsZero) and not all(sigmaIsZero):
            mexBox = QMessageBox()
            mexBox.setText("One of the smoothing sigma values is 0. Reset it to a value > 0.1 or set all sigmas to 0 for no smoothing.")
            mexBox.exec_()
            return

        # avoid 'kernel longer than line' errors
        shape = self.topLevelOperatorView.InputImage.meta.getTaggedShape()
        for ax in [item for item in 'zyx' if item in shape and shape[item] > 1]:
            req_sigma = np.floor(old_div(shape[ax],3))
            if block_shape_dict[ax] > req_sigma:
                mexBox = QMessageBox()
                mexBox.setText("The sigma value {} for dimension '{}'"
                               "is too high, should be at most {:.1f}.".format(
                                   block_shape_dict[ax], ax, req_sigma))
                mexBox.exec_()
                return

        # Read Thresholds
        lowThreshold = self._drawer.lowThresholdSpinBox.value()
        highThreshold = self._drawer.highThresholdSpinBox.value()
        beta = self._drawer.lambdaSpinBoxGC.value()

        # Read Size filters
        minSize = self._drawer.minSizeSpinBox.value()
        maxSize = self._drawer.maxSizeSpinBox.value()

        # Read the current thresholding method
        curIndex = self._drawer.methodComboBox.currentIndex()

        op_index = curIndex
        if curIndex == 1 and self._drawer.preserveIdentitiesCheckbox.isChecked():
            curIndex = 3
        # Apply new settings to the operator
        op.CurOperator.setValue(curIndex)
        op.Channel.setValue(final_channel)
        op.CoreChannel.setValue(core_channel)
        op.SmootherSigma.setValue(block_shape_dict)
        op.LowThreshold.setValue(lowThreshold)
        op.HighThreshold.setValue( highThreshold )
        
        op.Beta.setValue(beta)
        op.MinSize.setValue(minSize)
        op.MaxSize.setValue(maxSize)

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
            input_channel_colors = [QColor(r_g_b1[0],r_g_b1[1],r_g_b1[2]) for r_g_b1 in op.InputChannelColors.value]
        else:
            input_channel_colors = list(map(QColor, self._defaultInputChannelColors))
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
