from PyQt4.QtGui import *
from PyQt4 import uic
from PyQt4.QtCore import *

import os
from functools import partial

from ilastik.config import cfg as ilastik_config


class IPCServerInfoWidget(QWidget):
    """
    Displays various information about the IPCServerManager
    and allows manipulation of some of its properties
    """
    statusToggled = pyqtSignal()
    connectionChanged = pyqtSignal(int, bool)

    broadcast = pyqtSignal(str, dict)  # debug

    connectionColors = [QColor("yellow"), QColor("lime")]
    commandFailureColor = QColor(255, 150, 150)  # bright red

    def __init__(self, parent=None):
        super(IPCServerInfoWidget, self).__init__(parent)

        ui_class, widget_class = uic.loadUiType(os.path.split(__file__)[0] + "/ipcServerInfoWidget.ui")
        self.ui = ui_class()
        self.ui.setupUi(self)

        self.ui.toggleStatus.clicked.connect(partial(self.ui.toggleStatus.setEnabled, False))
        self.ui.toggleStatus.clicked.connect(self.statusToggled.emit)

        self.status_style = "background-color: %s; border: 3px inset gray"

        if ilastik_config.getboolean("ilastik", "debug"):
            args = {
                "hilite": "row? 0?",
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

    def set_server_running(self, is_running, port=None):
        """
        Changes the server status label to display the server status
        Enables the server toggle button
        :param is_running: new server status
        :type is_running: bool
        :param port: the port to display
        :type port: int
        """
        if is_running:
            self.ui.serverStatus.setText("running: %s" % port)
            self.ui.serverStatus.setStyleSheet(self.status_style % "lime")
            self.ui.toggleStatus.setText("Stop Server")
        else:
            self.ui.serverStatus.setText("shutdown")
            self.ui.serverStatus.setStyleSheet(self.status_style % "red")
            self.ui.toggleStatus.setText("Start Server")
        self.ui.toggleStatus.setEnabled(True)

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

        item = QListWidgetItem(text)
        if not success:
            item.setBackground(QBrush(self.commandFailureColor, Qt.SolidPattern))
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

    # slot called from QListWidgetItem check
    def list_widget_changed(self, item):
        index = self.ui.connectionList.row(item)
        self.connectionChanged(index, True if item.checkState == Qt.Checked else False)

    # debug
    def broadcast_clicked(self):
        command = self.ui.debugCommandName.text()
        args = str(self.ui.debugCommandArgs.toPlainText())
        kvargs = {}
        for arg in args.splitlines():
            key, value = arg.split(None, 1)
            kvargs[key] = value
        self.broadcast.emit(command, kvargs)


class ChoosePortDialog(QDialog):
    def __init__(self, port, parent=None):
        super(ChoosePortDialog, self).__init__(parent)

        ui_class, widget_class = uic.loadUiType(os.path.split(__file__)[0] + "/choosePortDialog.ui")
        self.ui = ui_class()
        self.ui.setupUi(self)

        self.validator = QIntValidator(0, 65535)
        self.ui.port.setValidator(self.validator)
        self.ui.port.setText(port)

    def get_port(self):
        try:
            port = int(self.ui.port.text())
        except ValueError:
            return None
        return port

    def set_error(self, error):
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