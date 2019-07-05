import pytest

from ilastik.applets.networkClassification import nnClassGui as nngui
from ilastik.applets.serverConfiguration.serverConfigGui import ServerConfigurationEditor
from ilastik.applets.serverConfiguration.serverListWidget import ServerListModel

from PyQt5 import uic
from PyQt5.Qt import QIcon, QStringListModel, QAbstractItemModel, QAbstractItemDelegate, Qt, QModelIndex, QDataWidgetMapper, pyqtProperty, QItemDelegate, QAbstractListModel, QListWidgetItem, pyqtSignal
from PyQt5.QtWidgets import QWidget, QComboBox, QToolButton, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QListWidget
from ilastik.shell.gui.iconMgr import ilastikIcons
from ilastik.applets.serverConfiguration.configStorage import ServerConfigStorage
from ilastik.applets.serverConfiguration import types


from configparser import ConfigParser

# TODO: Config with no servers

@pytest.fixture
def widget(qtbot):
    conf = ConfigParser()
    conf.read_string("")
    # with open("/home/novikov/myconfig", "r") as conf_file:
    #     conf.read_file(conf_file)


    w = ServerConfigurationEditor()
    srv_storage = ServerConfigStorage(conf, dst="/home/novikov/myconfig")
    w.setModel(ServerListModel(conf_store=srv_storage))

    qtbot.addWidget(w)
    w.show()

    qtbot.waitForWindowShown(w)

    return w

# TODO: Add datawidget mapper to map config values to form
# TODO: Add user=True property to form widget which will accept json config as an argument

def test_change_index_changes_visibility(qtbot, widget):
    qtbot.stopForInteraction()


from io import StringIO



def test_server_config_storage():
    conf = ConfigParser()
    conf.read_string(CONFIG)
    srv_storage = ServerConfigStorage(conf)
    assert len(srv_storage.get_servers()) == 3
