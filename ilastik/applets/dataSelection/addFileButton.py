# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Copyright 2011-2014, the ilastik developers

from PyQt4.QtCore import pyqtSignal
from PyQt4.QtGui import QMenu, QPushButton, QIcon

# this is used to find the location of the icon file
import os.path
FILEPATH = os.path.split(__file__)[0]

# Is DVID available?
try:
    import dvidclient
    _supports_dvid = True
except ImportError:
    _supports_dvid = False

class AddFileButton(QPushButton):
    """
    Button used for adding new files. It presents a drop down menu with
    three options:

        - Add separate image(s)
        - Add 3D/4D volume from stack
        - Add DVID volume
    """
    addFilesRequested = pyqtSignal()
    addStackRequested = pyqtSignal()
    addRemoteVolumeRequested = pyqtSignal()

    def __init__(self, parent, new=False):
        """
        -- ``new`` - boolean parameter to indicate if this button is used to
           add new lanes or files to new roles corresponding to an
           existing lane (such as prediction maps)
        """
        super(AddFileButton, self).__init__( QIcon(FILEPATH +
            "/../../shell/gui/icons/16x16/actions/list-add.png"),
            "Add..." if new == False else "Add New...", parent)

        # drop down menu for different add options
        menu = QMenu(parent=self)
        menu.addAction("Add separate image(s)...").triggered.\
                connect(self.addFilesRequested.emit)
        menu.addAction("Add a single 3D/4D Volume from Stack...").triggered.connect(
                self.addStackRequested.emit)
        
        if _supports_dvid:
            menu.addAction("Add DVID Volume...").triggered.connect(
                    self.addRemoteVolumeRequested.emit)

        self.setMenu( menu )
