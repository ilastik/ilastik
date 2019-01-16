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
        super(ServerConfigGui, self).__init__()
        self.parentApplet = parentApplet
        self._viewerControls = QWidget()
        self.topLevelOperator = topLevelOperatorView

        self._init_central_uic()
        # Disable box that contains username, password ect. while
        # local server (radio button) is activated
        self.localServerButton.setChecked(True)

        def local_button_state():
            if self.localServerButton.isChecked():
                self.topLevelOperator.setServerConfig()
                self.remoteServerBox.setEnabled(False)
        self.localServerButton.toggled.connect(local_button_state)

        self.remoteServerButton.setChecked(False)

        def remote_button_state():
            if self.remoteServerButton.isChecked():
                self.remoteServerBox.setEnabled(True)
        self.remoteServerButton.toggled.connect(remote_button_state)

        self.remoteServerBox.setEnabled(False)

        def save_button_state():
            config = {}
            for line in {'usernameLine', 'passwordLine', 'addressLine', 'portLine', 'meta_portLine'}:
                attr = getattr(self, line)
                attr.setEnabled(False)
                value = attr.text() if attr.text() else None
                config.update({line[:-4]: value})
            self.topLevelOperator.setServerConfig(config)
        self.saveButton.clicked.connect(save_button_state)

        def edit_button_state():
            for line in {'usernameLine', 'passwordLine', 'addressLine', 'portLine', 'meta_portLine'}:
                getattr(self, line).setEnabled(True)
        self.editButton.clicked.connect(edit_button_state)

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
