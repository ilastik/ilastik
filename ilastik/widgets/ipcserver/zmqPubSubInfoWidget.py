from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QMenu, QListWidgetItem

import logging
import os
from functools import partial
from ilastik.utility.ipcProtocol import Protocol

logger = logging.getLogger(__name__)


class ZMQPublisherInfoWidget(QWidget):
    """
    Displays various information about the ZMQPublisher
    and allows manipulation of some of its properties
    """
    subStatusToggled = pyqtSignal()
    pubStatusToggled = pyqtSignal()
    changeSubAddress = pyqtSignal()
    changePubAddress = pyqtSignal()

    def __init__(self, parent=None):
        super(ZMQPublisherInfoWidget, self).__init__(parent)

        ui_class, widget_class = uic.loadUiType(os.path.split(__file__)[0] + "/zmqPubSubInfoWidget.ui")
        self.ui = ui_class()
        self.ui.setupUi(self)

        self.status = {
            "pub": {
                "address": None,
                "running": False
            },
            "sub": {
                "address": None,
                "running": False
            }
        }

        self.ui.toggleSubStatus.clicked.connect(partial(self.ui.toggleSubStatus.setEnabled, False))
        self.ui.togglePubStatus.clicked.connect(partial(self.ui.togglePubStatus.setEnabled, False))
        self.ui.toggleSubStatus.clicked.connect(self.subStatusToggled.emit)
        self.ui.togglePubStatus.clicked.connect(self.pubStatusToggled.emit)

        menu = QMenu("options")
        self.change_pub_addr_action = menu.addAction("Change Address", self.changePubAddress.emit)
        self.ui.togglePubStatus.setMenu(menu)

        menu = QMenu("options")
        self.change_sub_addr_action = menu.addAction("Change Address", self.changeSubAddress.emit)
        self.ui.toggleSubStatus.setMenu(menu)

        self.status_style = "background-color: %s; border: 3px inset gray; padding: 5px"

    def notify_server_status_update(self, mode, attribute, value):
        if attribute == "address":
            pass
        elif attribute == "running":
            if mode == "pub":
                status_widget = self.ui.pubStatus
                status = self.status["pub"]
                toggle_widget = self.ui.togglePubStatus
                action = self.change_pub_addr_action
                msg = "publish"
            elif mode == "sub":
                status_widget = self.ui.subStatus
                status = self.status["sub"]
                toggle_widget = self.ui.toggleSubStatus
                action = self.change_sub_addr_action
                msg = "subscribe"
            else:
                logger.warning("'{}' is not a valid mode".format(mode))
                return
            if value:
                status_widget.setText("running: %s" % status["address"])
                status_widget.setStyleSheet(self.status_style % "lime")
                toggle_widget.setText("Un{}".format(msg))
            else:
                status_widget.setText("shutdown")
                status_widget.setStyleSheet(self.status_style % "red")
                toggle_widget.setText(msg.capitalize())
            toggle_widget.setEnabled(True)
            action.setEnabled(not value)
        else:
            logger.warning("'%s' is no valid server status attribute ")
            return
        self.status[mode][attribute] = value

    def add_sent_command(self, cmd, _):
        """
        Adds the sent command to the history list
        :param cmd: the command
        :type cmd: str
        """
        item = QListWidgetItem("::SENT:: {}".format(cmd))
        self.ui.commandList.addItem(item)
        self.ui.commandList.scrollToBottom()

    def add_recv_command(self, name, data):
        item = QListWidgetItem("::RECV:: {} {}".format(name, data))
        self.ui.commandList.addItem(item)
        self.ui.commandList.scrollToBottom()
