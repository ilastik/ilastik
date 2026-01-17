from __future__ import absolute_import, print_function

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
# make the program quit on Ctrl+C
import signal

signal.signal(signal.SIGINT, signal.SIG_DFL)

import os
import sys

import numpy
import numpy as np
from qtpy import QtCore, QtWidgets, uic
from qtpy.QtWidgets import QApplication, QMainWindow
from volumina._testing.from_lazyflow import OpDataProvider5D, OpDelay
from volumina.api import ArraySource, ConstantSource, LazyflowSinkSource, createDataSource
from volumina.layer import ColortableLayer, GrayscaleLayer, RGBALayer
from volumina.layerstack import LayerStackModel
from volumina.pixelpipeline._testing import OpDataProvider
from volumina.volumeEditor import VolumeEditor
from volumina.volumeEditorWidget import VolumeEditorWidget
from volumina.widgets.layerwidget import LayerWidget

from lazyflow import operators as op
from lazyflow.graph import Graph, InputSlot, Operator, OutputSlot

from .featureDlg import *
from .labelListModel import LabelListModel
from .labelListView import Label, LabelListView


class Main(QMainWindow):
    def __init__(self, useGL, argv):
        QMainWindow.__init__(self)
        self.initUic()

    def initUic(self):
        self.g = g = Graph()

        # get the absolute path of the 'ilastik' module
        uic.loadUi("designerElements/MainWindow.ui", self)

        def _quitApp():
            qapp = QApplication.instance()
            if qapp:
                qapp.quit()

        self.actionQuit.triggered.connect(_quitApp)

        def toggleDebugPatches(show):
            self.editor.showDebugPatches = show

        self.actionShowDebugPatches.toggled.connect(toggleDebugPatches)

        self.layerstack = LayerStackModel()

        readerNew = op.OpH5ReaderBigDataset(g)
        readerNew.inputs["Filenames"].setValue(
            ["scripts/CB_compressed_XY.h5", "scripts/CB_compressed_XZ.h5", "scripts/CB_compressed_YZ.h5"]
        )
        readerNew.inputs["hdf5Path"].setValue("volume/data")

        datasrc = createDataSource(readerNew.outputs["Output"])

        layer1 = GrayscaleLayer(datasrc)
        layer1.name = "Big Data"

        self.layerstack.append(layer1)

        shape = readerNew.outputs["Output"].meta.shape
        print(shape)
        self.editor = VolumeEditor(shape, self.layerstack)
        # self.editor.setDrawingEnabled(False)

        self.volumeEditorWidget.init(self.editor)
        model = self.editor.layerStack
        self.layerWidget.init(model)

        self.UpButton.clicked.connect(model.moveSelectedUp)
        model.canMoveSelectedUp.connect(self.UpButton.setEnabled)
        self.DownButton.clicked.connect(model.moveSelectedDown)
        model.canMoveSelectedDown.connect(self.DownButton.setEnabled)
        self.DeleteButton.clicked.connect(model.deleteSelected)
        model.canDeleteSelected.connect(self.DeleteButton.setEnabled)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    t = Main(False, [])
    t.show()

    app.exec_()
