from PyQt4.QtCore import pyqtSignal
from PyQt4.QtGui import QMenu, QPushButton, QIcon

# this is used to find the location of the icon file
import os.path
FILEPATH = os.path.split(__file__)[0]

class AddFileButton(QPushButton):
    """
    Button used for adding new files. It presents a drop down menu with
    two options:

        - Add one or more files
        - Add volume from stack
    """
    addFilesRequested = pyqtSignal()
    addStackRequested = pyqtSignal()

    def __init__(self, parent):
        super(AddFileButton, self).__init__( QIcon(FILEPATH +
            "/../../shell/gui/icons/16x16/actions/list-add.png"),
            "Add...", parent)

        # drop down menu for different add options
        menu = QMenu(parent=self)
        menu.addAction("Add one or more separate files ...").triggered.\
                connect(self.addFilesRequested.emit)
        menu.addAction("Add Volume from Stack...").triggered.connect(
                self.addStackRequested.emit)
        self.setMenu( menu )
