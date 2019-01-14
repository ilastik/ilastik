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

        self._initCentralUic()
        # Disable box that contains username, password ect. while
        # local server (radio button) is activated
        self.localServerButton.setChecked(True)

        def localButtonState():
            if self.localServerButton.isChecked():
                self.remoteServerBox.setEnabled(False)
        self.localServerButton.toggled.connect(localButtonState)

        self.remoteServerButton.setChecked(False)

        def remoteButtonState():
            if self.remoteServerButton.isChecked():
                self.remoteServerBox.setEnabled(True)
        self.remoteServerButton.toggled.connect(remoteButtonState)

        self.remoteServerBox.setEnabled(False)

        def saveButtonState():
            config = {}
            for line in {'usernameLine', 'passwordLine', 'addressLine', 'portLine', 'metaPortLine'}:
                attr = getattr(self, line)
                attr.setEnabled(False)
                config.update({line[:-4]: attr.text()})
            self.topLevelOperator.setServerConfig(config)
        self.saveButton.clicked.connect(saveButtonState)

        def editButtonState():
            for line in {'usernameLine', 'passwordLine', 'addressLine', 'portLine', 'metaPortLine'}:
                getattr(self, line).setEnabled(True)
        self.editButton.clicked.connect(editButtonState)

        self._initAppletDrawerUic()

        self._viewerControlWidgetStack = QStackedWidget(self)


    def _initCentralUic(self):
        """
        Load the ui file for the central widget.
        """
        localDir = os.path.split(__file__)[0] + '/'
        uic.loadUi(localDir + "/serverConfig.ui", self)


    def _initAppletDrawerUic(self):
        """
        Load the ui file for the applet drawer.
        """
        localDir = os.path.split(__file__)[0]+'/'
        self._drawer = uic.loadUi(localDir+"/serverConfigDrawer.ui")



