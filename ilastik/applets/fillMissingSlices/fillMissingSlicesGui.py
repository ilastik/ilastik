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
# 		   http://ilastik.org/license.html
###############################################################################
from builtins import range
from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui

import os.path
import sys

from qtpy.QtWidgets import QFileDialog
from qtpy.QtCore import QDir

import qtpy

import logging
from lazyflow.operators.opInterpMissingData import logger as remoteLogger


remoteLogger.setLevel(logging.DEBUG)
loggerName = __name__
logger = logging.getLogger(loggerName)
logger.setLevel(logging.DEBUG)


class FillMissingSlicesGui(LayerViewerGui):

    _standardPatchSizes = [1, 2, 4, 8] + [16 * i for i in range(1, 6)]
    _standardHaloSizes = [8 * i for i in range(7)]

    _recentDetectorDir = QDir.homePath()
    _recentExportDir = QDir.homePath()

    def initAppletDrawerUi(self):
        """"""
        # Load the ui file (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        self._drawer = qtpy.uic.loadUi(localDir + "/drawer.ui")

        self._drawer.loadDetectorButton.clicked.connect(self._loadDetectorButtonPressed)
        if hasattr(self._drawer, "loadHistogramsButton"):
            self._drawer.loadHistogramsButton.clicked.connect(self._loadHistogramsButtonPressed)
        self._drawer.exportDetectorButton.clicked.connect(self._exportDetectorButtonPressed)
        if hasattr(self._drawer, "trainButton"):
            self._drawer.trainButton.clicked.connect(self._trainButtonPressed)

        self._drawer.patchSizeComboBox.activated.connect(self._patchSizeComboBoxActivated)

        for s in self._standardPatchSizes:
            self._drawer.patchSizeComboBox.addItem(str(s), userData=s)

        self._drawer.haloSizeComboBox.activated.connect(self._haloSizeComboBoxActivated)
        for s in self._standardHaloSizes:
            self._drawer.haloSizeComboBox.addItem(str(s), userData=s)

        self.patchSizeChanged(update=True)
        self.haloSizeChanged(update=True)

        self.topLevelOperatorView.PatchSize.notifyValueChanged(self.patchSizeChanged, update=True)
        self.topLevelOperatorView.HaloSize.notifyValueChanged(self.haloSizeChanged, update=True)

    def _loadDetectorButtonPressed(self):
        fname, _filter = QFileDialog.getOpenFileName(
            self,
            caption="Open Detector File",
            filter="Pickled Objects (*.pkl);;All Files (*)",
            directory=self._recentDetectorDir,
        )
        if len(fname) > 0:  # not cancelled
            with open(fname, "r") as f:
                pkl = f.read()

            # reset it first
            self.topLevelOperatorView.OverloadDetector.setValue("")

            self.topLevelOperatorView.OverloadDetector.setValue(pkl)
            logger.debug("Loaded detectors from file '{}'".format(fname))
            self._recentDetectorDir = os.path.dirname(fname)

    def _loadHistogramsButtonPressed(self):
        fname, _filter = QFileDialog.getOpenFileName(
            self,
            caption="Open Histogram File",
            filter="HDF5 Files (*.h5 *.hdf5);;All Files (*)",
            directory=QDir.homePath(),
        )
        if len(fname) > 0:  # not cancelled
            # FIXME where do we get the real h5 path from???
            h5path = "volume/data"

            # no try-catch because we want to propagate errors to the GUI
            with h5py.File(fname, "r") as f:
                histos = f[h5path][()]

            self.topLevelOperatorView.setPrecomputedHistograms(histos)
            logger.debug("Loaded histograms from file '{}' (shape: {})".format(fname, histos.shape))

    def _exportDetectorButtonPressed(self):
        fname, _filter = QFileDialog.getSaveFileName(
            self,
            caption="Export Trained Detector",
            filter="Pickled Objects (*.pkl);;All Files (*)",
            directory=self._recentExportDir,
        )
        if len(fname) > 0:  # not cancelled
            with open(fname, "w") as f:
                f.write(self.topLevelOperatorView.Detector[:].wait())

            logger.debug("Exported detectors to file '{}'".format(fname))
            self._recentExportDir = os.path.dirname(fname)

    def _trainButtonPressed(self):
        self.topLevelOperatorView.train()

    def _patchSizeComboBoxActivated(self, i):
        desiredPatchSize = self._drawer.patchSizeComboBox.itemData(i)
        self.topLevelOperatorView.PatchSize.setValue(desiredPatchSize)

    def _haloSizeComboBoxActivated(self, i):
        desiredHaloSize = self._drawer.haloSizeComboBox.itemData(i)
        self.topLevelOperatorView.HaloSize.setValue(desiredHaloSize)

    @staticmethod
    def _insertIntoComboBox(cb, n):

        i = cb.findData(n)
        if i < 0:
            j = 0
            for i in range(cb.count()):
                k = cb.itemData(i)
                if k == n:
                    return i
                elif k > n:
                    j = i
                    break
                else:
                    j += 1

            cb.insertItem(j, str(n), userData=n)
            return j
        else:
            return i

    def patchSizeChanged(self, update=False):
        patchSize = self.topLevelOperatorView.PatchSize.value
        pos = self._insertIntoComboBox(self._drawer.patchSizeComboBox, patchSize)
        self._patchSizeComboBoxActivated(pos)

        if update:
            self._drawer.patchSizeComboBox.setCurrentIndex(pos)

    def haloSizeChanged(self, update=False):
        haloSize = self.topLevelOperatorView.HaloSize.value
        pos = self._insertIntoComboBox(self._drawer.haloSizeComboBox, haloSize)
        self._haloSizeComboBoxActivated(pos)

        if update:
            self._drawer.haloSizeComboBox.setCurrentIndex(pos)
