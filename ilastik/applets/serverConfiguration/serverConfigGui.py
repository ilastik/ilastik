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
from PyQt5.QtWidgets import QWidget, QStackedWidget, QListWidgetItem

from ilastik.applets.serverConfiguration.opServerConfig import DEFAULT_LOCAL_SERVER_CONFIG, DEFAULT_REMOTE_SERVER_CONFIG

from tiktorch.launcher import LocalServerLauncher, RemoteSSHServerLauncher, SSHCred
from tiktorch.rpc_interface import INeuralNetworkAPI
from tiktorch.rpc import Client, TCPConnConf


logger = logging.getLogger(__name__)


class ServerConfigGui(QWidget):
    def centralWidget(self):
        return self

    def appletDrawer(self):
        return self._drawer

    def menus(self):
        return []

    def viewerControlWidget(self):
        return self._viewerControlWidgetStack

    def __init__(self, parentApplet, topLevelOperatorView):
        super().__init__()
        self.parentApplet = parentApplet
        self._viewerControls = QWidget()
        self.topLevelOperator = topLevelOperatorView

        self._init_central_uic()
        # Disable box that contains username, password ect. while
        # local server (radio button) is activated

        def edit_button():
            for el in DEFAULT_REMOTE_SERVER_CONFIG.keys():
                if self.localServerButton.isChecked() and el == "address":
                    continue
                getattr(self, el).setEnabled(True)

        self.editButton.clicked.connect(edit_button)

        def server_button():
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
                if key == 'devices':
                    for d in value:
                        print('loaded device', d)
                        entry = QListWidgetItem(f"{d[0]} ({d[1]})", self.devices)
                        entry.setFlags(entry.flags() | QtCore.Qt.ItemIsUserCheckable)
                        if d[2]:
                            entry.setCheckState(QtCore.Qt.Checked)
                        else:
                            entry.setCheckState(QtCore.Qt.Unchecked)
                else:
                    getattr(self, key).setText(value)

            self.topLevelOperator.toggleServerConfig(use_local=self.localServerButton.isChecked())
            edit_button()  # enter 'edit mode' when switching between locale and remote server

        self.localServerButton.toggled.connect(server_button)

        use_local = self.topLevelOperator.UseLocalServer.value
        self.localServerButton.setChecked(use_local)
        self.remoteServerButton.setChecked(not use_local)
        server_button()

        def get_config(configurables, with_devices=True):
            config = {}
            for el in configurables:
                if el == 'devices':
                    if with_devices:
                        available_devices = []
                        for i in range(self.devices.count()):
                            d = self.devices.item(i)
                            available_devices.append((d.text().split(' (')[0], d.text().split(' (')[1][:-1], d.checkState()))
                        print('here')
                        print(available_devices)
                        print([type(el) for el in available_devices])
                        config['devices'] = available_devices
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
                addr, port1, port2 = socket.gethostbyname(server_config["address"]), server_config["port1"], server_config[
                    "port2"]
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
                finally:
                    launcher.stop()
            except Exception as e:
                logger.error(e)

            self.get_devices_button.setEnabled(True)

        self.get_devices_button.clicked.connect(get_devices_button)

        def save_button():
            if self.localServerButton.isChecked():
                assert not self.remoteServerButton.isChecked()
                self.topLevelOperator.setLocalServerConfig(get_config(DEFAULT_LOCAL_SERVER_CONFIG.keys()))
            else:
                assert self.remoteServerButton.isChecked()
                self.topLevelOperator.setRemoteServerConfig(get_config(DEFAULT_REMOTE_SERVER_CONFIG.keys()))

            print(self.topLevelOperator)

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
