import pytest

from unittest import mock

from ilastik.widgets import appletDrawerToolBox as at
from PyQt5.QtWidgets import QLabel, QApplication, QFrame, QVBoxLayout, QPushButton, QWidget
from PyQt5.QtCore import QSize, QPropertyAnimation, QRect, QVariantAnimation
from PyQt5.QtGui import QIcon, QImage


@pytest.fixture
def widget(qtbot):
    w = at.AppletDrawerToolBox()
    qtbot.addWidget(w)
    w.show()

    qtbot.waitForWindowShown(w)

    return w


def test_change_index_changes_visibility(qtbot, widget):
    l1 = QLabel("TestLabel")
    l2 = QLabel("TestLabel")

    widget.addItem(l1, "Tab1")
    widget.addItem(l2, "Tab2")

    assert l1.isVisible()
    assert not l2.isVisible()

    widget.setCurrentIndex(1)

    assert not l1.isVisible()
    assert l2.isVisible()


def as_qimage(qicon: QIcon) -> QImage:
    return qicon.pixmap(QSize(64, 64)).toImage()


def test_change_index_changes_icon_state(qtbot, widget):
    l1 = QLabel("TestLabel")
    l2 = QLabel("TestLabel")

    widget.addItem(l1, "Tab1")
    widget.addItem(l2, "Tab2")

    icon_open = as_qimage(widget.ICON_OPEN)
    icon_closed = as_qimage(widget.ICON_CLOSED)

    assert as_qimage(widget.itemIcon(0)) == icon_open
    assert as_qimage(widget.itemIcon(1)) == icon_closed

    widget.setCurrentIndex(1)

    assert as_qimage(widget.itemIcon(0)) == icon_closed
    assert as_qimage(widget.itemIcon(1)) == icon_open


@pytest.fixture
def widget_mngr(widget):
    mngr = at.AppletBarManager(widget)
    return mngr


class IAppletDrawer:
    def appletDrawer(self) -> QWidget:
        pass


class IMultilaneGui:
    @property
    def name(self) -> str:
        raise NotImplementedError

    @property
    def interactive(self) -> bool:
        raise NotImplementedError

    def getMultiLaneGui(self) -> IAppletDrawer:
        raise NotImplementedError


def applet_provider(widget: QWidget, name: str) -> IMultilaneGui:
    applet = mock.Mock(spec=IMultilaneGui)
    applet_prov = mock.Mock(spec=IAppletDrawer)

    applet_prov.appletDrawer.return_value = widget
    applet.getMultiLaneGui.return_value = applet_prov
    applet.interative = True
    applet.name = name
    return applet


def test_applet_manager_adds_widget(qtbot, widget, widget_mngr):
    applet = QLabel("MyApplet")
    name = "widget name"
    provider = applet_provider(applet, name)

    widget.show()
    qtbot.waitForWindowShown(widget)

    assert not applet.isVisible()
    widget_mngr.addApplet(100, provider)
    assert applet.isVisible()

    assert widget.itemText(0) == f"1. {name}"


def test_applet_manager_not_interactive(qtbot, widget, widget_mngr):
    applet = QLabel("Widget")
    prov = applet_provider(applet, "test")
    prov.interactive = False

    widget_mngr.addApplet(100, prov)
    widget.show()
    qtbot.waitForWindowShown(widget)

    assert widget.currentWidget() is None
    assert not applet.isVisible()


def test_applet_manager_change_focus_displays_corresponding_applets(qtbot, widget, widget_mngr):
    applet = QLabel("Widget")
    prov = applet_provider(applet, "test")

    applet2 = QLabel("Widget2")
    prov2 = applet_provider(applet2, "test2")

    widget_mngr.addApplet(100, prov)
    widget_mngr.addApplet(200, prov2)

    widget.show()
    qtbot.waitForWindowShown(widget)

    assert applet.isVisible()
    assert not applet2.isVisible()

    widget_mngr.focusApplet(200)

    assert not applet.isVisible()
    assert applet2.isVisible()


def test_applet_manager_item_title(qtbot, widget, widget_mngr):
    applet = QLabel("Widget")
    prov = applet_provider(applet, "test")

    applet2 = QLabel("Widget2")
    prov2 = applet_provider(applet2, "test another")

    widget_mngr.addApplet(100, prov)
    widget_mngr.addApplet(200, prov2)

    assert widget.itemText(0) == "1. test"
    assert widget.itemText(1) == "2. test another"


def test_update_applet_title(qtbot, widget, widget_mngr):
    applet = QLabel("Widget")
    prov = applet_provider(applet, "test")

    widget_mngr.addApplet(100, prov)

    assert widget.itemText(0) == "1. test"

    widget_mngr.updateAppletTitle(100, "my new title")
    assert widget.itemText(0) == "1. my new title"


def test_disabling_applet(qtbot, widget, widget_mngr):
    applet = QLabel("Widget")
    prov = applet_provider(applet, "test")

    applet2 = QLabel("Widget2")
    prov2 = applet_provider(applet2, "test another")

    widget_mngr.addApplet(100, prov)
    widget_mngr.addApplet(200, prov2)
    widget_mngr.focusApplet(200)

    assert widget.currentIndex() == 1
    assert widget.isItemEnabled(1)
    widget_mngr.setEnabled(200, False)
    assert widget.isItemEnabled(1), "Should be still enabled because it's an active widget"

    assert widget.isItemEnabled(0)
    widget_mngr.setEnabled(100, False)
    assert not widget.isItemEnabled(0)
