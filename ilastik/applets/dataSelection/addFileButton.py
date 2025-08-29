###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2024, the ilastik developers
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
from qtpy.QtCore import Signal, QModelIndex
from qtpy.QtWidgets import QMenu, QPushButton
from qtpy.QtGui import QIcon

# this is used to find the location of the icon file
import os.path

FILEPATH = os.path.split(__file__)[0]

# Is DVID available?
try:
    import libdvid

    _supports_dvid = True
except ImportError:
    _supports_dvid = False


class AddFileButton(QPushButton):
    """
    Button used for adding new files. It presents a drop down menu with
    three options:

        - Add separate image(s)
        - Add 3D/4D volume from sequence
        - Add multiscale/pyramidal dataset
        - Add DVID volume
    """

    addFilesRequested = Signal()
    addStackRequested = Signal()
    addDvidVolumeRequested = Signal()
    addMultiscaleDatasetRequested = Signal()

    def __init__(self, parent, *, index=None, new=False):
        """
        Args:
            parent (QWidget): Parent widget
            index (QModelIndex): Index of the gui dataset table cell to which this button is added
            new (bool): Indicating if this button is used to add new lanes or files to new roles
            corresponding to an existing lane (such as prediction maps)
        """
        super(AddFileButton, self).__init__(
            QIcon(FILEPATH + "/../../shell/gui/icons/16x16/actions/list-add.png"),
            "Add..." if new == False else "Add New...",
            parent,
        )

        self._index = index
        # drop down menu for different add options
        menu = QMenu(parent=self)
        menu.addAction("Add separate Image(s)...").triggered.connect(self.addFilesRequested.emit)
        menu.addAction("Add a single 3D/4D Volume from Sequence...").triggered.connect(self.addStackRequested.emit)
        menu.addAction("Add multiscale dataset...").triggered.connect(self.addMultiscaleDatasetRequested.emit)

        if _supports_dvid:
            menu.addAction("Add DVID Volume...").triggered.connect(self.addDvidVolumeRequested.emit)

        self.setMenu(menu)

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, index):
        self._index = index
