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

from ilastik.applets.serverConfiguration.opServerConfig import DEFAULT_LOCAL_SERVER_CONFIG, DEFAULT_REMOTE_SERVER_CONFIG

from tiktorch.launcher import LocalServerLauncher, RemoteSSHServerLauncher, SSHCred
from tiktorch.rpc_interface import INeuralNetworkAPI
from tiktorch.rpc import Client, TCPConnConf


logger = logging.getLogger(__name__)


def _items_checked_state(lst: QListWidget):
    for idx in range(lst.count()):
        yield lst.item(idx).checkState() == QtCore.Qt.Checked


class CheckedTranstion(QSignalTransition):
    def __init__(self, signal, *, reverse=False):
        super().__init__(signal)
        self.reverse = reverse

    def eventTest(self, event) -> bool:
        if not super().eventTest(event):
            return False

        has_checked = any(_items_checked_state(event.sender()))

        if self.reverse:
            return not has_checked
        else:
            return has_checked


class ServerConfigGui(QWidget):
    gotDevices = pyqtSignal()

    def centralWidget(self):
        return self

    def appletDrawer(self):
        return self._drawer

    def menus(self):
        return []

    def viewerControlWidget(self):
        return self._viewerControlWidgetStack

    def _make_initial_state(self) -> QState:
        s = QState()
        s.assignProperty(self.editButton, "enabled", False)
        s.assignProperty(self.saveButton, "enabled", False)
        s.assignProperty(self.devices, "enabled", False)

        # Inputs
        s.assignProperty(self.port1, "enabled", True)
        s.assignProperty(self.port2, "enabled", True)
        return s

    def _make_dev_fetched_state(self) -> QState:
        s = QState()
        s.assignProperty(self.editButton, "enabled", True)
        s.assignProperty(self.devices, "enabled", True)
        s.assignProperty(self.saveButton, "enabled", False)
        s.assignProperty(self.port1, "enabled", False)
        s.assignProperty(self.port2, "enabled", False)
        return s

    def _make_save_state(self):
        s = QState()
        s.assignProperty(self.saveButton, "enabled", True)
        return s

    def _create_state_machine(self) -> QStateMachine:
        machine = QStateMachine()

        init = self._make_initial_state()
        dev_fetched = self._make_dev_fetched_state()
        save = self._make_save_state()

        machine.addState(init)
        machine.addState(dev_fetched)
        machine.addState(save)
        machine.setInitialState(init)

        selected_tr = CheckedTranstion(self.devices.itemChanged)
        selected_tr.setTargetState(save)

        unselected_tr = CheckedTranstion(self.devices.itemChanged, reverse=True)
        unselected_tr.setTargetState(dev_fetched)

        init.addTransition(self.gotDevices, dev_fetched)

        save.addTransition(unselected_tr)
        dev_fetched.addTransition(selected_tr)
        dev_fetched.addTransition(self.editButton.clicked, init)

        return machine

    def __init__(self, parentApplet, topLevelOperatorView):
        super().__init__()
        self.parentApplet = parentApplet
        self._viewerControls = QWidget()
        self.topLevelOperator = topLevelOperatorView

        self._init_central_uic()
        # Disable box that contains username, password ect. while
        # local server (radio button) is activated

        self._state_machine = self._create_state_machine()
        self._state_machine.start()

        use_local = (
            True if not self.topLevelOperator.UseLocalServer.ready() else self.topLevelOperator.UseLocalServer.value
        )
        self.localServerButton.setChecked(use_local)
        self.remoteServerButton.setChecked(not use_local)

        def edit_button():
            self.topLevelOperator.UseLocalServer.disconnect()
            self.topLevelOperator.UseLocalServer.meta.NOTREADY = True
            for el in DEFAULT_REMOTE_SERVER_CONFIG.keys():
                if self.localServerButton.isChecked() and el == "address":
                    continue
                getattr(self, el).setEnabled(True)

        self.editButton.clicked.connect(edit_button)

        def server_button():
            self.topLevelOperator.UseLocalServer.disconnect()
            self.topLevelOperator.UseLocalServer.meta.NOTREADY = True
            if self.localServerButton.isChecked():
                assert not self.remoteServerButton.isChecked()
                config = self.topLevelOperator.LocalServerConfig.value
                getattr(self, "address").setEnabled(False)
                getattr(self, "username").hide()
                getattr(self, "usernameLabel").hide()
                getattr(self, "ssh_key").hide()
                getattr(self, "ssh_keyLabel").hide()
                getattr(self, "password").hide()
                getattr(self, "passwordLabel").hide()
            else:
                assert self.remoteServerButton.isChecked()
                config = self.topLevelOperator.RemoteServerConfig.value
                getattr(self, "usernameLabel").show()
                getattr(self, "password").show()
                getattr(self, "passwordLabel").show()
                getattr(self, "ssh_key").show()
                getattr(self, "ssh_keyLabel").show()
                getattr(self, "username").show()

            self.devices.clear()
            for key, value in config.items():
                if key == "devices":
                    for d in value:
                        entry = QListWidgetItem(f"{d[0]} ({d[1]})", self.devices)
                        entry.setFlags(entry.flags() | QtCore.Qt.ItemIsUserCheckable)
                        if d[2]:
                            entry.setCheckState(QtCore.Qt.Checked)
                        else:
                            entry.setCheckState(QtCore.Qt.Unchecked)
                else:
                    getattr(self, key).setText(value)

            edit_button()  # enter 'edit mode' when switching between locale and remote server

        self.localServerButton.toggled.connect(server_button)
        server_button()

        def get_config(configurables, with_devices=True):
            config = {}
            for el in configurables:
                if el == "devices":
                    if with_devices:
                        available_devices = []
                        for i in range(self.devices.count()):
                            d = self.devices.item(i)
                            available_devices.append(
                                (d.text().split(" (")[0], d.text().split(" (")[1][:-1], bool(d.checkState()))
                            )
                        config["devices"] = available_devices
                        self.devices.setEnabled(False)
                else:
                    attr = getattr(self, el)
                    attr.setEnabled(False)
                    config[el] = attr.text()

            return config

        def get_devices_button():
            self.get_devices_button.setEnabled(False)
            self.devices.clear()
            if self.localServerButton.isChecked():
                assert not self.remoteServerButton.isChecked()
                server_config = get_config(DEFAULT_LOCAL_SERVER_CONFIG.keys(), with_devices=False)
            else:
                assert self.remoteServerButton.isChecked()
                server_config = get_config(DEFAULT_REMOTE_SERVER_CONFIG.keys(), with_devices=False)

            try:
                addr, port1, port2 = (
                    socket.gethostbyname(server_config["address"]),
                    # in order not to block address for real server todo: remove port hack
                    str(int(server_config["port1"]) - 20),
                    str(int(server_config["port2"]) - 20),
                )
                conn_conf = TCPConnConf(addr, port1, port2)

                if addr == "127.0.0.1":
                    launcher = LocalServerLauncher(conn_conf)
                else:
                    launcher = RemoteSSHServerLauncher(
                        conn_conf, cred=SSHCred(server_config["username"], server_config["password"])
                    )

                launcher.start()
                try:
                    tikTorchClient = Client(INeuralNetworkAPI(), conn_conf)
                    available_devices = tikTorchClient.get_available_devices()
                except Exception as e:
                    logger.error(e)
                else:
                    for d in available_devices:
                        entry = QListWidgetItem(f"{d[0]} ({d[1]})", self.devices)
                        entry.setFlags(entry.flags() | QtCore.Qt.ItemIsUserCheckable)
                        entry.setCheckState(QtCore.Qt.Unchecked)
                    self.gotDevices.emit()
                finally:
                    launcher.stop()
            except Exception as e:
                logger.error(e)

            self.get_devices_button.setEnabled(True)

        self.get_devices_button.clicked.connect(get_devices_button)

        def save_button():
            self.topLevelOperator.UseLocalServer.disconnect()
            self.topLevelOperator.UseLocalServer.meta.NOTREADY = True

            use_local = self.localServerButton.isChecked()
            if use_local:
                assert not self.remoteServerButton.isChecked()
                self.topLevelOperator.setLocalServerConfig(get_config(DEFAULT_LOCAL_SERVER_CONFIG.keys()))
            else:
                assert self.remoteServerButton.isChecked()
                self.topLevelOperator.setRemoteServerConfig(get_config(DEFAULT_REMOTE_SERVER_CONFIG.keys()))

            self.topLevelOperator.UseLocalServer.setValue(use_local)
            self.parentApplet.appletStateUpdateRequested()

        self.saveButton.clicked.connect(save_button)

        self._init_applet_drawer_uic()
        self._viewerControlWidgetStack = QStackedWidget(self)

    def _init_central_uic(self):
        """
        Load the ui file for the central widget.
        """
        local_dir = os.path.split(__file__)[0] + "/"
        uic.loadUi(local_dir + "/serverConfig.ui", self)

    def _init_applet_drawer_uic(self):
        """
        Load the ui file for the applet drawer.
        """
        local_dir = os.path.split(__file__)[0] + "/"
        self._drawer = uic.loadUi(local_dir + "/serverConfigDrawer.ui")
