###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2019, the ilastik team
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
import logging
import os
import socket

from qtpy import uic
from qtpy.QtWidgets import QWidget
from qtpy.QtCore import Signal

logger = logging.getLogger(__name__)
from qtpy.QtCore import (
    QAbstractItemModel,
    Qt,
    QModelIndex,
    QDataWidgetMapper,
    QItemDelegate,
    QListWidgetItem,
    Signal,
)
from qtpy.QtWidgets import QWidget, QVBoxLayout

from .serverConfigForm import ServerConfigForm, ServerFormWorkflow
from .serverListWidget import ServerListWidget, ServerListModel
from .configStorage import SERVER_CONFIG
from . import types
from ilastik import config


class ServerConfigGui(QWidget):
    gotDevices = Signal()

    def centralWidget(self):
        return self._centralWidget

    def appletDrawer(self):
        return self._drawer

    def menus(self):
        return []

    def viewerControlWidget(self):
        return None

    def secondaryControlsWidget(self):
        return None

    def getServerIdFromOp(self):
        if self.topLevelOp.ServerId.ready():
            return self.topLevelOp.ServerId.value
        return None

    def __init__(self, parentApplet, topLevelOperatorView):
        super().__init__()
        self.parentApplet = parentApplet
        self.topLevelOp = topLevelOperatorView
        self._centralWidget = self._makeServerConfigWidget(self.getServerIdFromOp())
        self._centralWidget.saved.connect(self._serverSelected)
        self._initAppletDrawer()

    def _serverSelected(self):
        self.topLevelOp.ServerId.disconnect()
        self.topLevelOp.ServerId.setValue(self._centralWidget.currentServerId())

    def _makeServerConfigWidget(self, serverId):
        w = ServerConfigurationEditor(self.parentApplet.connectionFactory)
        w.setModel(ServerListModel(conf_store=SERVER_CONFIG))
        w.selectServer(serverId)
        return w

    def _initAppletDrawer(self):
        """
        Load the ui file for the applet drawer.
        """
        local_dir = os.path.split(__file__)[0] + "/"
        self._drawer = uic.loadUi(local_dir + "/serverConfigDrawer.ui")

    def stopAndCleanUp(self):
        pass

    def setEnabled(self, enabled):
        pass

    def setImageIndex(self, index):
        pass

    def imageLaneAdded(self, laneIndex):
        pass

    def imageLaneRemoved(self, laneIndex, finalLength):
        pass

    def allowLaneSelectionChange(self):
        return False


class ServerFormItemDelegate(QItemDelegate):
    def setEditorData(self, editor: QWidget, index: QModelIndex) -> None:
        conf = index.data(role=Qt.EditRole)
        editor.config = conf
        super().setEditorData(editor, index)

    def setModelData(self, editor: QWidget, model: QAbstractItemModel, index: QModelIndex) -> None:
        conf = editor.config
        model.setData(index, conf)


class ServerConfigurationEditor(QWidget):
    currentConfigChanged = Signal(object)
    saved = Signal()

    def __init__(self, connectionFactory, parent=None) -> None:
        super().__init__(parent)
        self._srv_list = ServerListWidget()
        self._srv_form = ServerConfigForm(connectionFactory)
        self._workflow = ServerFormWorkflow(self._srv_form)
        self._model = None
        layout = QVBoxLayout(self)
        layout.addWidget(self._srv_list)
        layout.addWidget(self._srv_form)

    def selectServer(self, serverId):
        self._srv_list.selectServer(serverId)

    def _selectedServer(self, idx):
        data = self._model.index(idx).data(role=Qt.EditRole)
        self.currentConfigChanged.emit(data)

    def currentServerId(self):
        return self._srv_list.currentServerId()

    def setModel(self, model):
        self._model = model
        self._srv_list.setModel(model)

        self._mapper = QDataWidgetMapper(self)
        self._mapper.setModel(model)
        self._mapper.setItemDelegate(ServerFormItemDelegate(self))
        self._mapper.addMapping(self._srv_form, 1)
        self._mapper.currentIndexChanged.connect(self._workflow.restart)
        self._mapper.setCurrentIndex(self._srv_list.currentIndex())

        self._mapper.setSubmitPolicy(QDataWidgetMapper.ManualSubmit)
        self._srv_form.saveBtn.clicked.connect(self._mapper.submit)
        self._srv_form.saveBtn.clicked.connect(self.saved)

        self._srv_list.currentIndexChanged.connect(self._mapper.setCurrentIndex)
        self._srv_list.currentIndexChanged.connect(self._selectedServer)
