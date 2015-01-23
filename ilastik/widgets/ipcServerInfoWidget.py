from PyQt4.QtGui import *
from PyQt4 import uic
from PyQt4.QtCore import *

import logging
import os
from functools import partial

from ilastik.config import cfg as ilastik_config

logger = logging.getLogger(__name__)


def convert_to_type(string):
    if string[0] == "'" and string[-1] == "'" or \
            string[0] == '"' and string[-1] == '"':
        return string[1:-1]
    try:
        return int(string)
    except ValueError:
        pass
    try:
        return float(string)
    except ValueError:
        pass
    return string


class IPCServerInfoWidget(QWidget):
    """
    Displays various information about the IPCServerManager
    and allows manipulation of some of its properties
    """
    statusToggled = pyqtSignal()
    connectionChanged = pyqtSignal(int, bool)
    portChanged = pyqtSignal(int)

    broadcast = pyqtSignal(dict)  # debug

    connectionColors = [QColor("yellow"), QColor("lime")]
    commandFailureColor = QColor(255, 150, 150)  # bright red

    def __init__(self, parent=None):
        super(IPCServerInfoWidget, self).__init__(parent)

        ui_class, widget_class = uic.loadUiType(os.path.split(__file__)[0] + "/ipcServerInfoWidget.ui")
        self.ui = ui_class()
        self.ui.setupUi(self)

        self.server_status = {
            "port": None,
            "running": False
        }

        self.ui.toggleStatus.clicked.connect(partial(self.ui.toggleStatus.setEnabled, False))
        self.ui.toggleStatus.clicked.connect(self.statusToggled.emit)
        menu = QMenu("options")
        self.change_port_action = menu.addAction("Change Port", self.change_port)
        self.ui.toggleStatus.setMenu(menu)

        self.status_style = "background-color: %s; border: 3px inset gray"

        if ilastik_config.getboolean("ilastik", "debug"):
            args = {
                "hilite": "objectid 'Row0'",
                "0": "objectid 'Row0'",
                "unhilite": "objectid 'Row0'",
                "1": "objectid 'Row0'",
                "clearhilite": "",
                "2": "",
                "setviewerposition": "x 0.0\ny 0.0\nz 0.0\nt 0.0\nc 0.0",
                "handshake": "name ilastik\nport <port>",
                "brotbacken": "mehl 100g\nwasser 200ml\nhefe 20g",
            }

            def on_complete(text):
                self.ui.debugCommandArgs.setPlainText(args[str(text)])
            completer = QCompleter(args.keys())
            completer.setCaseSensitivity(Qt.CaseSensitive)
            self.ui.debugCommandName.setCompleter(completer)
            # noinspection PyUnresolvedReferences
            completer.activated.connect(on_complete)
            self.ui.broadcastButton.clicked.connect(self.broadcast_clicked)
        else:
            self.ui.debugDock.close()

    def notify_server_status_update(self, attribute, value):
        """
        Notifies to the GUI that the IPCServer's status has changed
        :param attribute: the attribute that has changed ("port", "running")
        :type attribute: str
        :param value: the value that the attribute has changed to
        :type value: any
        """

        if attribute == "port":
            pass
        elif attribute == "running":
            if value:  # server is running now
                self.ui.serverStatus.setText("running: %s" % self.server_status["port"])
                self.ui.serverStatus.setStyleSheet(self.status_style % "lime")
                self.ui.toggleStatus.setText("Stop Server")
            else:
                self.ui.serverStatus.setText("shutdown")
                self.ui.serverStatus.setStyleSheet(self.status_style % "red")
                self.ui.toggleStatus.setText("Start Server")
            self.change_port_action.setEnabled(not value)
            self.ui.toggleStatus.setEnabled(True)

        else:
            logger.warn("'%s' is no valid server status attribute ")
            return
        self.server_status[attribute] = value

    def add_command(self, cmd, success):
        """
        adds a new command to the list
        :param cmd: the command including the arguments
        :type cmd: dict
        :param success: flag if the execution of the command was successful
        :type success: bool
        """
        text = "%s (" % cmd["command"]
        for k, v in cmd.iteritems():
            if k == "command":
                continue
            text += " %s:%s" % (k, v)
        text += " )"

        item = QListWidgetItem("::RECV      :: {}".format(text))
        if not success:
            item.setBackground(QBrush(self.commandFailureColor, Qt.SolidPattern))
        self.ui.commandList.addItem(item)
        self.ui.commandList.scrollToBottom()

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

    def update_connections(self, connections):
        """
        Clears the connection list and adds an entry for each item in connetions
        :param connections: the new connections
        :type connections: dict
        """
        self.ui.connectionList.clear()
        for c in connections.iterkeys():
            item = QListWidgetItem("%s (%s)" % (c[0], c[1]))
            enabled = connections[c]["enabled"]
            client = connections[c]["client"]
            item.setCheckState(Qt.Checked if enabled else Qt.Unchecked)
            color = self.connectionColors[0 if client is None else 1]
            item.setBackground(QBrush(color, Qt.SolidPattern))
            self.ui.connectionList.addItem(item)

    def change_port(self, old_port=None, message=""):
        """
        shows the ChoosePortDialog and returns the new port
        :param old_port: the old port if None the Widgets internal server_port is used
        :type old_port: int or None
        :param message: an optinal message to be displayed why the port must be changed
        :type message: str
        :return: the new port
        """
        dialog = ChoosePortDialog(self.server_status["port"] if old_port is None else old_port)
        dialog.set_message(message)
        if dialog.exec_() == 1:
            self.portChanged.emit(dialog.get_port())

    # slot called from QListWidgetItem check
    def list_widget_changed(self, item):
        index = self.ui.connectionList.row(item)
        self.connectionChanged.emit(index, True if item.checkState() == Qt.Checked else False)

    #slot called from QCheckBox toggle
    def stay_on_top(self, state):
        pass

    # debug
    def broadcast_clicked(self):
        command = convert_to_type(str(self.ui.debugCommandName.text()))
        args = str(self.ui.debugCommandArgs.toPlainText())
        kvargs = {}
        for arg in args.splitlines():
            key, value = arg.split(None, 1)
            value = convert_to_type(value)
            kvargs[key] = value
        kvargs["command"] = command
        print kvargs
        self.broadcast.emit(kvargs)


class ChoosePortDialog(QDialog):
    def __init__(self, port, parent=None):
        super(ChoosePortDialog, self).__init__(parent)

        ui_class, widget_class = uic.loadUiType(os.path.split(__file__)[0] + "/choosePortDialog.ui")
        self.ui = ui_class()
        self.ui.setupUi(self)

        self.validator = QIntValidator(0, 65535)
        self.ui.port.setValidator(self.validator)
        self.ui.port.setText(str(port))
        self.ui.port.selectAll()

    def get_port(self):
        try:
            port = int(self.ui.port.text())
        except ValueError:
            return None
        return port

    def set_message(self, error):
        self.ui.error.setText(error)

if __name__ == "__main__":

    class IlastikConfig:
        def __init__(self):
            pass

        @staticmethod
        def getboolean(a, b):
            return True

    ilastik_config = IlastikConfig()
    import sys
    app = QApplication(sys.argv)

    widget = IPCServerInfoWidget()
    widget.show()

    sys.exit(app.exec_())