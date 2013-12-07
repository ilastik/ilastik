import os
import logging
from functools import partial

from PyQt4 import uic
from PyQt4.QtCore import Qt, QEvent
from PyQt4.QtGui import QColor
from PyQt4.QtGui import QMessageBox

from volumina.api import LazyflowSource, AlphaModulatedLayer, ColortableLayer
from volumina.colortables import create_default_16bit
from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui
from ilastik.utility import bind
from ilastik.utility.gui import threadRouted
from lazyflow.operators.generic import OpSingleChannelSelector

logger = logging.getLogger(__name__)
traceLogger = logging.getLogger("TRACE." + __name__)


class GraphCutSegmentationGui(LayerViewerGui):

    def stopAndCleanUp(self):
        # Unsubscribe to all signals
        for fn in self.__cleanup_fns:
            fn()

        super(GraphCutSegmentationGui, self).stopAndCleanUp()

    def __init__(self, *args, **kwargs):
        self.__cleanup_fns = []
        super(GraphCutSegmentationGui, self).__init__(*args, **kwargs)
        self._channelColors = self._createDefault16ColorColorTable()

    def initAppletDrawerUi(self):
        """
        Reimplemented from LayerViewerGui base class.
        """
        # Load the ui file (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        self._drawer = uic.loadUi(os.path.join(localDir,"drawer.ui"))

        self._allWatchedWidgets = [
            self._drawer.inputChannelSpinBox,
            self._drawer.thresholdSpinBox,
            self._drawer.betaSpinBox,
            self._drawer.minSizeSpinBox,
            self._drawer.maxSizeSpinBox]

        for widget in self._allWatchedWidgets:
            # If the user pressed enter inside a spinbox, auto-click "Apply"
            widget.installEventFilter(self)

        self._updateGuiFromOperator()
        self.topLevelOperatorView.Input.notifyReady(
            bind(self._updateGuiFromOperator))
        self.__cleanup_fns.append(
            partial(self.topLevelOperatorView.Input.unregisterUnready,
                    bind(self._updateGuiFromOperator)))

        self.topLevelOperatorView.Input.notifyMetaChanged(
            bind(self._updateGuiFromOperator))
        self.__cleanup_fns.append(
            partial(self.topLevelOperatorView.Input.unregisterMetaChanged,
                    bind(self._updateGuiFromOperator)))

    @threadRouted
    def _updateGuiFromOperator(self):
        op = self.topLevelOperatorView

        numChannels = 0
        if op.Input.ready():
            # Channel
            channelIndex = op.Input.meta.axistags.index('c')
            numChannels = op.Input.meta.shape[channelIndex]
        self._drawer.inputChannelSpinBox.setRange(0, numChannels-1)
        self._drawer.inputChannelSpinBox.setValue(op.Channel.value)

        # Threshold
        self._drawer.thresholdSpinBox.setValue(op.Threshold.value)

        # Beta
        self._drawer.betaSpinBox.setValue(op.Beta.value)

        # Size filters
        self._drawer.minSizeSpinBox.setValue(op.MinSize.value)
        self._drawer.maxSizeSpinBox.setValue(op.MaxSize.value)

    def _updateOperatorFromGui(self):
        op = self.topLevelOperatorView

        # Read all gui settings before updating the operator
        # (The gui is still responding to operator changes, 
        #  and we don't want it to update until we've read all gui values.)

        # Read Channel
        channel = self._drawer.inputChannelSpinBox.value()

        # Read Thresholds
        threshold = self._drawer.thresholdSpinBox.value()

        # Read Size filters
        minSize = self._drawer.minSizeSpinBox.value()
        maxSize = self._drawer.maxSizeSpinBox.value()

        if minSize >= maxSize:
            mexBox = QMessageBox()
            mexBox.setText("Min size must be smaller than max size ")
            mexBox.exec_()
            return

        # Apply new settings to the operator
        op.Channel.setValue(channel)
        op.Threshold.setValue(threshold)
        op.MinSize.setValue(minSize)
        op.MaxSize.setValue(maxSize)

    def _onApplyButtonClicked(self):
        self._updateOperatorFromGui()
        for layer in self.layerstack:
            if "Final" in layer.name:
                layer.visible = True

    def eventFilter(self, watched, event):
        """
        If the user pressed 'enter' within a spinbox, auto-click the "apply" button.
        """
        if watched in self._allWatchedWidgets:
            if event.type() == QEvent.KeyPress and\
                    (event.key() == Qt.Key_Enter or
                     event.key() == Qt.Key_Return):
                self._drawer.applyButton.click()
                return True
        return False

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

        if op.Input.ready():
            numChannels = op.Input.meta.getTaggedShape()['c']

            for channel in range(numChannels):
                channelProvider = OpSingleChannelSelector(
                    parent=op.Input.getRealOperator().parent)
                channelProvider.Input.connect(op.Input)
                channelProvider.Index.setValue(channel)
                channelSrc = LazyflowSource(channelProvider.Output)
                color = QColor(self._channelColors[channel])
                inputChannelLayer = \
                    AlphaModulatedLayer(channelSrc, tintColor=color,
                                        range=(0.0, 1.0), normalize=(0.0, 1.0))
                inputChannelLayer.opacity = 0.5
                inputChannelLayer.visible = True
                inputChannelLayer.name = "Input Channel " + str(channel)
                inputChannelLayer.setToolTip(
                    "Select input channel {}"
                    " if this prediction image contains"
                    " the objects of interest.".format(channel))
                layers.append(inputChannelLayer)

        # Show the raw input data
        rawSlot = self.topLevelOperatorView.RawInput
        if rawSlot.ready():
            rawLayer = self.createStandardLayerFromSlot(rawSlot)
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
