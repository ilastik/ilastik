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

from PyQt5 import uic, QtCore
from PyQt5.QtWidgets import QWidget, QStackedWidget, QListWidgetItem, QListWidget
from PyQt5.QtCore import QStateMachine, QState, QSignalTransition, pyqtSignal

from tiktorch.launcher import LocalServerLauncher, RemoteSSHServerLauncher, SSHCred
from tiktorch.rpc_interface import INeuralNetworkAPI
from tiktorch.rpc import Client, TCPConnConf


logger = logging.getLogger(__name__)
from PyQt5.Qt import QIcon, QStringListModel, QAbstractItemModel, QAbstractItemDelegate, Qt, QModelIndex, QDataWidgetMapper, pyqtProperty, QItemDelegate, QAbstractListModel, QListWidgetItem, pyqtSignal
from PyQt5.QtWidgets import QWidget, QComboBox, QToolButton, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QListWidget

from .serverConfigForm import ServerConfigForm, ServerFormWorkflow
from .serverListWidget import ServerListWidget, ServerListModel
from .configStorage import ServerConfigStorage
from . import types
from ilastik import config


class ServerConfigGui(QWidget):
    gotDevices = pyqtSignal()

    def centralWidget(self):
        return self._centralWidget

    def appletDrawer(self):
        return self._drawer

    def menus(self):
        return []

    def viewerControlWidget(self):
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
        w = ServerConfigurationEditor()
        srv_storage = ServerConfigStorage(config.cfg, dst=config.CONFIG_PATH)
        w.setModel(ServerListModel(conf_store=srv_storage))
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


class ServerFormItemDelegate(QItemDelegate):
    def setEditorData(self, editor: QWidget, index: QModelIndex) -> None:
        dst_prop = editor.metaObject().userProperty()
        if dst_prop.isValid():
            name = dst_prop.name()
            setattr(editor, name, index.data(role=Qt.EditRole))

        super().setEditorData(editor, index)


def _fetch_devices(config: types.ServerConfig):
    try:
        addr, port1, port2 = (
            socket.gethostbyname(config.address),
            # in order not to block address for real server todo: remove port hack
            str(int(config.port1) - 20),
            str(int(config.port2) - 20),
        )
        conn_conf = TCPConnConf(addr, port1, port2)

        if addr == "127.0.0.1":
            launcher = LocalServerLauncher(conn_conf, path=config.path)
        else:
            launcher = RemoteSSHServerLauncher(
                conn_conf, cred=SSHCred(user=config.username, key_path=config.ssh_key), path=config.path
            )

        try:
            launcher.start()
            client = Client(INeuralNetworkAPI(), conn_conf)
            return client.get_available_devices()
        except Exception as e:
            logger.exception('Failed to fetch devices')
        finally:
            try:
                launcher.stop()
            except Exception:
                pass

    except Exception as e:
        logger.error(e)

    return []


class ServerConfigurationEditor(QWidget):
    currentConfigChanged = pyqtSignal(object)
    saved = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._srv_list = ServerListWidget()
        self._srv_form = ServerConfigForm(_fetch_devices)
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
