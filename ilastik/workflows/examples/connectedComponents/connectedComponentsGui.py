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

from volumina.api import LazyflowSource, ColortableLayer
from volumina.colortables import create_default_16bit
from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui
from ilastik.utility.gui import threadRouted

# always available
import numpy as np

logger = logging.getLogger(__name__)


class ConnectedComponentsGui(LayerViewerGui):

    _methods = {'vigra': 0, 'lazy': 1}

    def __init__(self, *args, **kwargs):
        super(ConnectedComponentsGui, self).__init__(*args, **kwargs)

        self._drawer.applyButton.clicked.connect(
            self._onApplyButtonClicked)

    def initAppletDrawerUi(self):
        """
        Reimplemented from LayerViewerGui base class.
        """
        # Load the ui file (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        self._drawer = uic.loadUi(localDir+"/drawer.ui")

        box = self._drawer.methodSelectingBox
        for k, v in self._methods.iteritems():
            box.insertItem(v, k, k)

        self._allWatchedWidgets = [box]

        for widget in self._allWatchedWidgets:
            # If the user pressed enter inside a spinbox, auto-click "Apply"
            widget.installEventFilter(self)

        self._updateGuiFromOperator()

        '''
        self.topLevelOperatorView.Input.notifyReady(
            self._updateGuiFromOperator)
        self.topLevelOperatorView.Input.notifyMetaChanged(
            self._updateGuiFromOperator)
        '''

    @threadRouted
    def _updateGuiFromOperator(self):
        op = self.topLevelOperatorView

        # Thresholds
        val = self._methods[op.Method.value]
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
        #binct[0] = 0
        ct = create_default_16bit()
        # associate label 0 with black/transparent?
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

        if op.Input.ready():
            rawSrc = LazyflowSource(op.Input)
            rawLayer = ColortableLayer(outputSrc, binct)
            #rawLayer = self.createStandardLayerFromSlot(op.Input)
            rawLayer.name = "Raw data"
            rawLayer.visible = True
            rawLayer.opacity = 1.0
            layers.append(rawLayer)

        return layers

