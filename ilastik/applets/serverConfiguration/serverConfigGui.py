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
#		   http://ilastik.org/license.html
###############################################################################
import os
from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QStackedWidget

from ilastik.applets.serverConfiguration.opServerConfig import DEFAULT_SERVER_CONFIG


class ServerConfigGui(QWidget):
    configurables = DEFAULT_SERVER_CONFIG.keys()

    def centralWidget(self):
        return self

    def appletDrawer(self):
        return self._drawer

    def menus(self):
        return []

    def viewerControlWidget(self):
        return self._viewerControlWidgetStack

    def __init__(self, parentApplet, topLevelOperatorView):
        super(ServerConfigGui, self).__init__()
        self.parentApplet = parentApplet
        self._viewerControls = QWidget()
        self.topLevelOperator = topLevelOperatorView

        self._init_central_uic()
        # Disable box that contains username, password ect. while
        # local server (radio button) is activated
        def edit_button():
            for el in self.configurables:
                if self.localServerButton.isChecked() and el == 'address':
                    continue
                getattr(self, el).setEnabled(True)

        self.editButton.clicked.connect(edit_button)

        def server_button():
            if self.localServerButton.isChecked():
                assert not self.remoteServerButton.isChecked()
                config = self.topLevelOperator.LocalServerConfig.value
                getattr(self, 'address').setEnabled(False)
                getattr(self, 'username').hide()
                getattr(self, 'usernameLabel').hide()
                getattr(self, 'password').hide()
                getattr(self, 'passwordLabel').hide()
            else:
                assert self.remoteServerButton.isChecked()
                config = self.topLevelOperator.RemoteServerConfig.value
                getattr(self, 'username').show()
                getattr(self, 'usernameLabel').show()
                getattr(self, 'password').show()
                getattr(self, 'passwordLabel').show()

            for el in self.configurables:
                getattr(self, el).setText(config[el])

            self.topLevelOperator.toggleServerConfig(use_local=self.localServerButton.isChecked())
            edit_button()  # enter 'edit mode' when switching between locale and remote server

        self.localServerButton.toggled.connect(server_button)

        use_local = self.topLevelOperator.UseLocalServer.value
        self.localServerButton.setChecked(use_local)
        self.remoteServerButton.setChecked(not use_local)
        server_button()

        def save_button():
            config = {}
            for el in self.configurables:
                attr = getattr(self, el)
                attr.setEnabled(False)
                config.update({el: attr.text()})

            if self.localServerButton.isChecked():
                self.topLevelOperator.setLocalServerConfig(config)
            else:
                self.topLevelOperator.setRemoteServerConfig(config)

        self.saveButton.clicked.connect(save_button)

        self._init_applet_drawer_uic()
        self._viewerControlWidgetStack = QStackedWidget(self)

    def _init_central_uic(self):
        """
        Load the ui file for the central widget.
        """
        local_dir = os.path.split(__file__)[0] + '/'
        uic.loadUi(local_dir + "/serverConfig.ui", self)

    def _init_applet_drawer_uic(self):
        """
        Load the ui file for the applet drawer.
        """
        local_dir = os.path.split(__file__)[0] + '/'
        self._drawer = uic.loadUi(local_dir + "/serverConfigDrawer.ui")
