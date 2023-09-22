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

import importlib.util
from pathlib import Path

from PyQt5.QtCore import pyqtSignal, QModelIndex
from PyQt5.QtWidgets import QMenu, QPushButton
from PyQt5.QtGui import QIcon

import ilastik.config

_ICON_PATH = Path(__file__).parents[2] / "shell/gui/icons/16x16/actions/list-add.png"
_SUPPORTS_DVID = importlib.util.find_spec("libdvid") is not None


class AddFileButton(QPushButton):
    """Button used for adding new files.

    It presents a drop down menu with the following options:

    - Add separate image(s)
    - Add multiple image(s)
    - Add 3D/4D volume from sequence
    - Add DVID volume
    - Add precomputed chunked volume

    Attributes:
        index (QModelIndex): Index of the gui dataset table cell to which this button is added
    """

    addFilesRequested = pyqtSignal()
    addFromPatternsRequested = pyqtSignal()
    addStackRequested = pyqtSignal()
    addRemoteVolumeRequested = pyqtSignal()
    addPrecomputedVolumeRequested = pyqtSignal()

    def __init__(self, parent, *, index=None, new=False):
        """
        Args:
            parent (QWidget): Parent widget
            index (QModelIndex): Index of the gui dataset table cell to which this button is added
            new (bool): Indicating if this button is used to add new lanes or files to new roles
            corresponding to an existing lane (such as prediction maps)
        """
        super(AddFileButton, self).__init__(QIcon(str(_ICON_PATH)), "Add New..." if new else "Add...", parent)

        self.index = index
        # drop down menu for different add options
        menu = QMenu(parent=self)
        menu.addAction("Add separate Image(s)...").triggered.connect(self.addFilesRequested)
        menu.addAction("Add multiple Image(s)...").triggered.connect(self.addFromPatternsRequested)
        menu.addAction("Add a single 3D/4D Volume from Sequence...").triggered.connect(self.addStackRequested)

        if ilastik.config.cfg.getboolean("ilastik", "hbp", fallback=False):
            menu.addAction("Add a precomputed chunked volume...").triggered.connect(self.addPrecomputedVolumeRequested)

        if _SUPPORTS_DVID:
            menu.addAction("Add DVID Volume...").triggered.connect(self.addRemoteVolumeRequested)

        self.setMenu(menu)
