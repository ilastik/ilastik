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
from PyQt4.QtGui import QColor
from PyQt4.QtGui import QMessageBox

from volumina.api import LazyflowSource, AlphaModulatedLayer, ColortableLayer
from volumina.colortables import create_default_16bit
from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui
from ilastik.utility import bind
from ilastik.utility.gui import threadRouted

# always available
import numpy as np

logger = logging.getLogger(__name__)
traceLogger = logging.getLogger("TRACE." + __name__)

_methods = {'vigra': 0, 'lazy': 1}


class ConnectedComponentsGui(LayerViewerGui):

    def stopAndCleanUp(self):
        # Unsubscribe to all signals
        for fn in self.__cleanup_fns:
            fn()

        super(ConnectedComponentsGui, self).stopAndCleanUp()

    def __init__(self, *args, **kwargs):
        self.__cleanup_fns = []
        super(ConnectedComponentsGui, self).__init__(*args, **kwargs)
        self._channelColors = self._createDefault16ColorColorTable()

        # connect callbacks last -> avoid undefined behaviour
        self._connectCallbacks()

    def initAppletDrawerUi(self):
        """
        Reimplemented from LayerViewerGui base class.
        """
        # Load the ui file (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        self._drawer = uic.loadUi(localDir+"/drawer.ui")

        box = self._drawer.methodSelectingBox
        for k, v in _methods.iteritems():
            box.insertItem(v, k, k)

        self._allWatchedWidgets = [box]

        for widget in self._allWatchedWidgets:
            # If the user pressed enter inside a spinbox, auto-click "Apply"
            widget.installEventFilter(self)

        self._updateGuiFromOperator()
        self.topLevelOperatorView.Input.notifyReady(
            bind(self._updateGuiFromOperator))
        self.__cleanup_fns.append(partial(
            self.topLevelOperatorView.Input.unregisterUnready,
            bind(self._updateGuiFromOperator)))

        self.topLevelOperatorView.Input.notifyMetaChanged(
            bind(self._updateGuiFromOperator))
        self.__cleanup_fns.append(partial(
            self.topLevelOperatorView.Input.unregisterMetaChanged,
            bind(self._updateGuiFromOperator)))

    def _connectCallbacks(self):
        self._drawer.applyButton.clicked.connect(
            bind(self._onApplyButtonClicked))

    @threadRouted
    def _updateGuiFromOperator(self):
        op = self.topLevelOperatorView

        # Thresholds
        val = _methods[op.Method.value]
        self._drawer.methodSelectingBox.setCurrentIndex(val)

    def _updateOperatorFromGui(self):
        op = self.topLevelOperatorView

        m = str(self._drawer.methodSelectingBox.currentText())
        op.Method.setValue(m)

    def _onApplyButtonClicked(self):
        self._updateOperatorFromGui()
        for layer in self.layerstack:
            if "Connect" in layer.name:
                layer.visible = True
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
            outputLayer.name = "Connected Components"
            outputLayer.visible = False
            outputLayer.opacity = 1.0
            outputLayer.setToolTip("Results of connected component analysis")
            layers.append(outputLayer)

        rawSlot = self.topLevelOperatorView.Input
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
