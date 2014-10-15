import os 
import itertools
from functools import partial

from PyQt4 import uic
from PyQt4.QtCore import Qt, QEvent
from PyQt4.QtGui import QColor, QMessageBox, QListView, QStandardItemModel, \
    QStandardItem, QPixmap, QIcon

from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui
from ilastik.utility.gui import threadRouted

from volumina.api import LazyflowSource, AlphaModulatedLayer, ColortableLayer
# from volumina.colortables import create_default_16bit

from lazyflow.operators import OpMultiArraySlicer

import numpy as np

import logging
logger = logging.getLogger(__name__)

from opSmoothing import smoothers_available
smoothing_methods_map = ['gaussian', 'guided', 'opengm']


class MriVolFilterGui(LayerViewerGui):

    def stopAndCleanUp(self):
        super(MriVolFilterGui, self).stopAndCleanUp()
        op = self.topLevelOperatorView
        op.Input.unregisterMetaChanged(self._setupLabelNames)

    def __init__(self, *args, **kwargs):
        # self.__cleanup_fns = []
        self._channelColors = self._createDefault16ColorColorTable()
        super(MriVolFilterGui, self).__init__(*args, **kwargs)
        #  use default colors
        # self._channelColors = create_default_16bit()
        # self._channelColors[0] = 0 # make first channel transparent

    def initAppletDrawerUi(self):
        """
        Reimplemented from LayerViewerGui base class.
        """
        # Load the ui file (find it in our own directory)
        localDir = os.path.split(__file__)[0]

        self._drawer = uic.loadUi(localDir+"/filter_drawer.ui")

        self._drawer.applyButton.clicked.connect(self._onApplyButtonClicked)

        for i, name in enumerate(smoothing_methods_map):
            if name not in smoothers_available:
                self._drawer.tabWidget.setTabEnabled(i, False)

        # TODO extend the watched widgets list
        self._allWatchedWidgets = [self._drawer.sigmaSpinBox,
                                   self._drawer.thresSpinBox]

        # If the user pressed enter inside a spinbox, auto-click "Apply"
        for widget in self._allWatchedWidgets:
            widget.installEventFilter(self)

        self.model = QStandardItemModel(self._drawer.labelListView)
        self._setupLabelNames()
        self._connectCallbacks()
        self._updateGuiFromOperator()

    def _connectCallbacks(self):
        op = self.topLevelOperatorView
        op.Input.notifyMetaChanged(self._setupLabelNames)

        # syncronize slider and spinbox
        self._drawer.slider.valueChanged.connect(self._slider_value_changed)
        self._drawer.thresSpinBox.valueChanged.connect(
            self._spinbox_value_changed)

    def _slider_value_changed(self, value):
        self._drawer.thresSpinBox.setValue(value)

    def _spinbox_value_changed(self, value):
        self._drawer.slider.setValue(value)

    def _setupLabelNames(self, *args, **kwargs):
        op = self.topLevelOperatorView

        if not op.Input.ready():
            # do nothing if we have no data
            numChannels = 0
        else:
            numChannels = op.Input.meta.getTaggedShape()['c']
        layer_names = []

        # setup labels
        self.model.clear()
        for i in range(numChannels):
            item = QStandardItem()
            item_name = 'Prediction {}'.format(i+1)
            item.setText(item_name)
            item.setCheckable(True)
            # Per default set the last channel active
            if i == numChannels-1:
                item.setCheckState(2)

            pixmap = QPixmap(16, 16)
            pixmap.fill(QColor(self._channelColors[i+1]))
            item.setIcon(QIcon(pixmap))

            layer_names.append(item_name)
            self.model.appendRow(item)
        self._drawer.labelListView.setModel(self.model)

    def _updateOperatorFromGui(self):
        op = self.topLevelOperatorView

        tab_index = self._drawer.tabWidget.currentIndex()
        conf = self._getTabConfig()

        op.SmoothingMethod.setValue(smoothing_methods_map[tab_index])
        op.Configuration.setValue(conf)

        # Read Size Threshold
        thres = self._drawer.thresSpinBox.value()
        op.Threshold.setValue(thres)

        # Read Active Channels
        self._setActiveChannels()

    def _getTabConfig(self):
        # TODO
        tab_index = self._drawer.tabWidget.currentIndex()
        if tab_index == 0:
            sigma = self._drawer.sigmaSpinBox.value()
            conf = {'sigma': sigma}
        elif tab_index == 1:
            eps = self._drawer.epsGuidedSpinBox.value()
            sigma = self._drawer.sigmaGuidedSpinBox.value()
            conf = { 'sigma': sigma,
                     'eps': eps }
        elif tab_index == 2:
            raise NotImplementedError("Tab {} is not implemented".format(
                smoothing_methods_map[tab_index]))
        else:
            raise ValueError('Unknown tab {} selected'.format(tab_index))
        return conf

    def _setActiveChannels(self):
        op = self.topLevelOperatorView
        new_states = [self.model.item(i).checkState()
                      for i in range(self.model.rowCount())]
        new_states = np.array(new_states, dtype=np.int)
        op.ActiveChannels.setValue(new_states)

    @threadRouted
    def _updateGuiFromOperator(self):
        # Set Maximum Value of Sigma
        op = self.topLevelOperatorView
        tagged_shape = op.Input.meta.getTaggedShape()
        shape = np.min([tagged_shape[c] for c in 'xyz' if c in tagged_shape])
        max_sigma = np.floor(shape/6.) - .1  # Experimentally 3. (see Anna)
        # https://github.com/ilastik/ilastik/issues/996
        # FIXME does not support 2d with explicit z, for example
        self._drawer.sigmaSpinBox.setMaximum(max_sigma)
        # FIXME is this the correct maximum for guided, too?
        self._drawer.sigmaGuidedSpinBox.setMaximum(max_sigma)

        thres = self._drawer.thresSpinBox.value()
        thres = op.Threshold.value
        self._drawer.thresSpinBox.setValue(thres)
        self._spinbox_value_changed(thres)

        method = op.SmoothingMethod.value
        try:
            i = smoothing_methods_map.index(method)
        except ValueError:
            logger.warn("Smoothing method '{}' unknown to GUI, "
                        "using default...".format(method))
            i = 0
        self._drawer.tabWidget.setCurrentIndex(i)
        self._setTabConfig(op.Configuration.value)

        # update the channel list
        states = op.ActiveChannels.value
        for i in range(min(self.model.rowCount(), len(states))):
            self.model.item(i).setCheckState(states[i])

    def _setTabConfig(self, conf):
        try:
            tab_index = self._drawer.tabWidget.currentIndex()
            if tab_index == 0:
                sigma = conf['sigma']
                sigma = min(sigma, self._drawer.sigmaSpinBox.maximum())
                sigma = max(sigma, self._drawer.sigmaSpinBox.minimum())
                self._drawer.sigmaSpinBox.setValue(sigma)

            elif tab_index == 1:
                # TODO check range
                self._drawer.epsGuidedSpinBox.setValue(conf['eps'])
                self._drawer.sigmaGuidedSpinBox.setValue(conf['sigma'])
            elif tab_index == 2:
                raise NotImplementedError(
                    "Tab {} is not implemented".format(
                        smoothing_methods_map[tab_index]))
            else:
                raise ValueError(
                    'Unknown tab {} selected'.format(tab_index))
        except KeyError:
            logger.warn("Bad smoothing configuration encountered")

    def _onApplyButtonClicked(self):
        self._updateOperatorFromGui()

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

    def setupLayers(self):
        layers = []
        op = self.topLevelOperatorView


        if op.Output.ready():
            outputLayer = ColortableLayer( LazyflowSource(op.Output),
                                        colorTable=self._channelColors)
            outputLayer.name = "Output"
            outputLayer.visible = True
            outputLayer.opacity = 0.7
            layers.append( outputLayer )

        if op.ArgmaxOutput.ready():
            outLayer = ColortableLayer( LazyflowSource(op.ArgmaxOutput),
                                        colorTable=self._channelColors)
            outLayer.name = "Argmax"
            outLayer.visible = False
            outLayer.opacity = 1.0
            layers.append( outLayer )

        if op.Smoothed.ready():
            numChannels = op.Smoothed.meta.getTaggedShape()['c']
            slicer = OpMultiArraySlicer(parent=\
                                        op.Smoothed.getRealOperator().parent)
            slicer.Input.connect(op.Smoothed)
            slicer.AxisFlag.setValue('c')  # slice along c

            for i in range(numChannels):
                # slicer maps each channel to a subslot of slicer.Slices
                # i.e. slicer.Slices is not really slot, but a list of slots
                channelSrc = LazyflowSource( slicer.Slices[i] )
                inputChannelLayer = AlphaModulatedLayer(
                    channelSrc,
                    tintColor=QColor(self._channelColors[i+1]),
                    range=(0.0, 1.0),
                    normalize=(0.0, 1.0) )
                inputChannelLayer.opacity = 0.5
                inputChannelLayer.visible = False
                inputChannelLayer.name = op.LabelNames.value[i]
                # inputChannelLayer.name = "Prediction " + str(i)
                '''
                inputChannelLayer.setToolTip(
                    "Select input channel " + str(i) + \
                    " if this prediction image contains the objects of interest.")               
                '''
                layers.append(inputChannelLayer)

        # raw layer
        if op.RawInput.ready():
            rawLayer = self.createStandardLayerFromSlot( op.RawInput )
            rawLayer.name = "Raw data"
            rawLayer.visible = True
            rawLayer.opacity = 1.0
            layers.append(rawLayer)
        return layers

    def getLayer(self, name):
        """ 
        find a layer by its name
        """
        try:
            layer = itertools.ifilter(lambda l: l.name == name, self.layerstack).next()
        except StopIteration:
            return None
        else:
            return layer
        
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
