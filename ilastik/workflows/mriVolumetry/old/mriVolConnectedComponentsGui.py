import os
import itertools
from functools import partial

from PyQt4 import uic
from PyQt4.QtCore import Qt, QEvent
from PyQt4.QtGui import QColor

from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui
from ilastik.utility.gui import threadRouted
from volumina.api import LazyflowSource, AlphaModulatedLayer, ColortableLayer
from lazyflow.operators import OpMultiArraySlicer


class MriVolConnectedComponentsGui ( LayerViewerGui ):

    def __init__(self, *args, **kwargs):
        super( MriVolConnectedComponentsGui, self ).__init__(*args, **kwargs)
        self._channelColors = self._createDefault16ColorColorTable()

    def initAppletDrawerUi(self):
        localDir = os.path.split(__file__)[0]
        self._drawer = uic.loadUi(localDir+"/cc_drawer.ui")

        self._drawer.applyButton.clicked.connect( self._onApplyButtonClicked )

        # syncronize slider and spinbox
        self._drawer.slider.valueChanged.connect( self._slider_value_changed )
        self._drawer.thresSpinBox.valueChanged.connect( \
                                                self._spinbox_value_changed )

        # connect channel spin box
        self._drawer.channelComboBox.currentIndexChanged.connect( \
                                                        self._channelChanged )
        
        # link checkbox to disable channel spin box
        self._drawer.channelCheckBox.stateChanged.connect( \
                                                    self._onCheckBoxChecked )

        #  If the user pressed enter inside a spinbox, auto-click "Apply"
        self._allWatchedWidgets = [ self._drawer.thresSpinBox]
 
        for widget in self._allWatchedWidgets:
            widget.installEventFilter( self )

        self._updateGuiFromOperator()

    def eventFilter(self, watched, event):
        """
        If the user pressed 'enter' within a spinbox, 
        auto-click the "apply" button.
        """
        if watched in self._allWatchedWidgets:
            if  event.type() == QEvent.KeyPress and\
              ( event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return):
                self._drawer.applyButton.click()
                return True
        return False

    @threadRouted
    def _updateGuiFromOperator(self):
        # Set maximum nummber of channels
        op = self.topLevelOperatorView
        for i in range(len(op.Input)):
            self._drawer.channelComboBox.addItem(op.LabelNames.value[i])

    def _channelChanged(self):
        idx = self._drawer.channelComboBox.currentIndex()-1
        op = self.topLevelOperatorView
        self._drawer.thresSpinBox.setValue( op.Threshold[idx].value )


    def _onCheckBoxChecked(self):
        if self._drawer.channelCheckBox.isChecked():
            self._drawer.channelComboBox.setDisabled(True)
        else:
            self._drawer.channelComboBox.setEnabled(True)

    def _onApplyButtonClicked(self):
        self._updateOperatorFromGui()

    def _updateOperatorFromGui(self):
        op = self.topLevelOperatorView
        thres = self._drawer.thresSpinBox.value()
        if self._drawer.channelCheckBox.isChecked():
            op.CurOperator.setValue(1)
            # same threshold for all channels
            for i in range(len(op.Threshold)):
                op.Threshold[i].setValue(thres)
        else:
            op.CurOperator.setValue(0)
            idx = self._drawer.channelComboBox.currentIndex()-1
            # print 'Threshold {} changed: {}'.format(idx, thres)
            op.Threshold[idx].setValue(thres)
        
        # for i in range(len(op.Threshold)):
            # print 'Threshold channel {}: {}'.format(i, op.Threshold[i].value)
                                                    

    def _slider_value_changed(self, value):
        self._drawer.thresSpinBox.setValue(value)

    def _spinbox_value_changed(self, value):
        self._drawer.slider.setValue(value)

    def setupLayers(self):
        layers = []
        op = self.topLevelOperatorView

        if op.FanInOutput.ready():
            outLayer = ColortableLayer( LazyflowSource(op.FanInOutput),
                                        colorTable=self._channelColors)
            outLayer.name = "Output"
            outLayer.visible = True
            outLayer.opacity = 1.0
            layers.append( outLayer )

        if op.Output.ready():
            numChannels = len(op.Output)
            # print 'Number of channels: {}'.format(numChannels)
            for i in range(numChannels):
                # slicer maps each channel to a subslot of slicer. Slices
                # i.e. slicer.Slices is not really slot, but a list of slots
                channelSrc = LazyflowSource( op.Output[i] )
                inputChannelLayer = AlphaModulatedLayer(
                    channelSrc,
                    tintColor=QColor(self._channelColors[i+1]),
                    range=(0.0, 1.0),
                    normalize=(0.0, 1.0) )
                inputChannelLayer.opacity = 0.5
                inputChannelLayer.visible = True
                inputChannelLayer.name = op.LabelNames.value[i]
                # inputChannelLayer.name = 'Prediction {}'.format(i+1)
                '''
                inputChannelLayer.setToolTip(
                    "Select input channel " + str(i) + \
                    " if this prediction image contains the objects of interest.")               
                '''
                layers.append(inputChannelLayer)
                def layerNameChangedHandler(layer, k, *args, **kwargs):
                    layer.name = op.LabelNames.value[k]
                    self._drawer.channelComboBox.setItemText(k,
                    op.LabelNames.value[k])
                op.LabelNames.notifyDirty( partial(layerNameChangedHandler,
                                                   inputChannelLayer, i) )

        '''
        if op.Input.ready():
            #outLayer = ColortableLayer( LazyflowSource(op.Input),
             #                           colorTable=self._channelColors)
            outLayer = self.createStandardLayerFromSlot( op.Input )
            outLayer.name = "Input"
            outLayer.visible = True
            outLayer.opacity = 1.0
            layers.append( outLayer )
        '''
        if op.RawInput.ready():
            rawLayer = self.createStandardLayerFromSlot( op.RawInput )
            rawLayer.name = "Raw data"
            rawLayer.visible = True
            rawLayer.opacity = 1.0
            layers.append(rawLayer)

        return layers

    def _createDefault16ColorColorTable(self):
        colors = []

        # SKIP: Transparent for the zero label
        colors.append(QColor(0,0,0,0))

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

        assert len(colors) == 17
        return [c.rgba() for c in colors]
