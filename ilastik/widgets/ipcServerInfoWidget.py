from PyQt4.QtGui import *
from PyQt4 import uic
from PyQt4.QtCore import *

import os
from functools import partial


class IPCServerInfoWidget(QWidget):
    statusToggled = pyqtSignal()
    connectionChanged = pyqtSignal(int, bool)

    def __init__(self, parent=None):
        super(IPCServerInfoWidget, self).__init__(parent)

        ui_class, widget_class = uic.loadUiType(os.path.split(__file__)[0] + "/ipcServerInfoWidget.ui")
        self.ui = ui_class()
        self.ui.setupUi(self)

        self.ui.toggleStatus.clicked.connect(partial(self.ui.toggleStatus.setEnabled, False))
        self.ui.toggleStatus.clicked.connect(self.statusToggled.emit)

        self.status_style = "background-color: %s; border: 3px inset gray"

    def server_running(self, is_running, port=None):
        if is_running:
            self.ui.serverStatus.setText("running: %s" % port)
            self.ui.serverStatus.setStyleSheet(self.status_style % "lime")
            self.ui.toggleStatus.setText("Stop Server")
        else:
            self.ui.serverStatus.setText("shutdown")
            self.ui.serverStatus.setStyleSheet(self.status_style % "red")
            self.ui.toggleStatus.setText("Start Server")
        self.ui.toggleStatus.setEnabled(True)

    """
    adds a new command to the list
    :param cmd: the command including the arguments
    :type cmd: dict
    """
    def add_command(self, cmd):
        text = "%s (" % cmd["command"]
        for k, v in cmd.iteritems():
            if k == "command":
                continue
            text += " %s:%s" % (k, v)
        text += " )"
        self.ui.commandList.addItem(QListWidgetItem(text))

    def connections_changed(self, connections):
        self.ui.connectionList.clear()
        for c in connections.iterkeys():
            item = QListWidgetItem("%s (%s)" % (c[0], c[1]))
            enabled = connections[c]["enabled"]
            item.setCheckState(Qt.Checked if enabled else Qt.Unchecked)
            self.ui.connectionList.addItem(item)

    # slot called from QListWidgetItem check
    def list_widget_changed(self, item):
        index = self.ui.connectionList.row(item)
        self.connectionChanged(index, True if item.checkState == Qt.Checked else False)



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