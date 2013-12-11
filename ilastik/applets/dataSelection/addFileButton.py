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

        - Add one or more files
        - Add volume from stack
        - Add remote volume
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
        menu.addAction("Add one or more separate files ...").triggered.\
                connect(self.addFilesRequested.emit)
        menu.addAction("Add Volume from Stack...").triggered.connect(
                self.addStackRequested.emit)
        
        if _supports_dvid:
            menu.addAction("Add DVID Volume...").triggered.connect(
                    self.addRemoteVolumeRequested.emit)

        self.setMenu( menu )
