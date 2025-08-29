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
#             http://ilastik.org/license.html
###############################################################################
# Built-in
import os

# Third-party
from qtpy import uic
from qtpy.QtWidgets import QWidget

from volumina.widgets.exportHelper import prompt_export_settings_and_export_layer


class ViewerControls(QWidget):
    def __init__(self, parent=None, model=None):
        QWidget.__init__(self, parent)
        localDir = os.path.split(__file__)[0]
        uic.loadUi(os.path.join(localDir, "viewerControls.ui"), self)

    def setupConnections(self, model):
        # The editor's layerstack is in charge of which layer movement buttons are enabled
        model.canMoveSelectedUp.connect(self.UpButton.setEnabled)
        model.canMoveSelectedDown.connect(self.DownButton.setEnabled)
        model.canDeleteSelected.connect(self.SaveButton.setEnabled)

        # Connect our layer movement buttons to the appropriate layerstack actions
        self.layerWidget.init(model)
        self.UpButton.clicked.connect(model.moveSelectedUp)
        self.DownButton.clicked.connect(model.moveSelectedDown)
        self.SaveButton.clicked.connect(self.export)

    def export(self):
        modelindex = self.layerWidget.currentIndex()
        model = self.layerWidget.model()
        layer = model[modelindex.row()]
        dataSource = layer.datasources[0]

        if not hasattr(dataSource, "dataSlot"):
            raise RuntimeError(
                f"can not export from a non-lazyflow data source (layer={type(layer)!r}, "
                f"datasource={type(dataSource)!r}"
            )
        import lazyflow

        assert isinstance(dataSource.dataSlot, lazyflow.graph.Slot), f"slot is of type {type(dataSource.dataSlot)!r}"
        assert isinstance(
            dataSource.dataSlot.operator, lazyflow.graph.Operator
        ), f"slot's operator is of type {type(dataSource.dataSlot.operator)!r}"
        prompt_export_settings_and_export_layer(layer, self)
