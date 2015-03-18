from PyQt4.QtGui import *
from PyQt4 import uic
import os


class IPCServerInfoWindow(QMainWindow):
    def __init__(self, parent=None):
        super(IPCServerInfoWindow, self).__init__(parent)

        ui_class, widget_class = uic.loadUiType(os.path.split(__file__)[0] + "/ipcServerInfoWindow.ui")
        self.ui = ui_class()
        self.ui.setupUi(self)

    def add_widget(self, name, widget):
        self.ui.tabWidget.addTab(widget, name)
