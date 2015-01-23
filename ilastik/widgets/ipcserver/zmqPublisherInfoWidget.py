from PyQt4.QtGui import *
from PyQt4 import uic
from PyQt4.QtCore import *

import logging
import os
from functools import partial

logger = logging.getLogger(__name__)


class ZMQPublisherInfoWidget(QWidget):
    """
    Displays various information about the ZMQPublisher
    and allows manipulation of some of its properties
    """
    statusToggled = pyqtSignal()
    #changeAddress = pyqtSignal()

    def __init__(self, parent=None):
        super(ZMQPublisherInfoWidget, self).__init__(parent)

        ui_class, widget_class = uic.loadUiType(os.path.split(__file__)[0] + "/zmqPublisherInfoWidget.ui")
        self.ui = ui_class()
        self.ui.setupUi(self)

        self.server_status = {
            "address": None,
            "running": False
        }

        self.ui.toggleStatus.clicked.connect(partial(self.ui.toggleStatus.setEnabled, False))
        self.ui.toggleStatus.clicked.connect(self.statusToggled.emit)

        self.status_style = "background-color: %s; border: 3px inset gray; padding: 5px"

    def notify_server_status_update(self, attribute, value):
        """
        Notifies to the GUI that the Server's status has changed
        :param attribute: the attribute that has changed
        :type attribute: str
        :param value: the value that the attribute has changed to
        :type value: any
        """
        if attribute == "address":
            pass
        elif attribute == "running":
            if value:  # server is running now
                self.ui.serverStatus.setText("running: %s" % self.server_status["address"])
                self.ui.serverStatus.setStyleSheet(self.status_style % "lime")
                self.ui.toggleStatus.setText("Unpublish")
            else:
                self.ui.serverStatus.setText("shutdown")
                self.ui.serverStatus.setStyleSheet(self.status_style % "red")
                self.ui.toggleStatus.setText("Publish")
            self.ui.toggleStatus.setEnabled(True)
        else:
            logger.warn("'%s' is no valid server status attribute ")
            return
        self.server_status[attribute] = value

    def add_sent_command(self, cmd, count):
        """
        Adds the sent command to the history list
        :param cmd: the command
        :type cmd: str
        :param count: the number of clients that received the message
        :type count: int
        """
        item = QListWidgetItem("::SENT({:^4}):: {}".format(count, cmd))
        self.ui.commandList.addItem(item)
        self.ui.commandList.scrollToBottom()
