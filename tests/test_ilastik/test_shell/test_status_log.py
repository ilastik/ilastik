import logging

import pytest
from PyQt5.QtCore import Qt

from ilastik.shell.gui.ilastikShell import NotificationsBar, NotificationsWindow
from lazyflow import USER_LOGLEVEL

logger = logging.getLogger("root")


@pytest.fixture
def log_bar(qtbot):
    log_bar = NotificationsBar()
    qtbot.addWidget(log_bar)
    with qtbot.waitExposed(log_bar):
        log_bar.show()
    return log_bar


@pytest.fixture
def enable_log(caplog):
    # necessary to override otherwise log message would not be handled
    caplog.set_level(logging.INFO, logger="root")
    return caplog


def test_log_window_scroll_to_last(qtbot):
    log_win = NotificationsWindow(data=[f"some_text {i}" for i in range(100)])
    qtbot.addWidget(log_win)
    with qtbot.waitExposed(log_win):
        log_win.show()

    log_scroll_max_tmp = log_win.verticalScrollBar().maximum()

    assert log_win.verticalScrollBar().value() == log_scroll_max_tmp

    log_win.appendMessage("another one")

    assert log_win.verticalScrollBar().maximum() > log_scroll_max_tmp
    assert log_win.verticalScrollBar().value() == log_win.verticalScrollBar().maximum()


def test_print_message(log_bar: NotificationsBar, enable_log):
    assert log_bar.text() == ""

    some_text = "ilastik logbar"
    logger.log(USER_LOGLEVEL, some_text)
    assert log_bar.text() == some_text


def test_double_click_opens_window(log_bar: NotificationsBar, qtbot):
    qtbot.mouseDClick(log_bar, Qt.MouseButton.LeftButton)

    assert isinstance(log_bar.notifications_widget, NotificationsWindow)


def test_reopen_shows_same_window(log_bar: NotificationsBar, qtbot):
    qtbot.mouseDClick(log_bar, Qt.MouseButton.LeftButton)

    assert isinstance(log_bar.notifications_widget, NotificationsWindow)

    original_id = id(log_bar.notifications_widget)

    qtbot.mouseDClick(log_bar, Qt.MouseButton.LeftButton)
    with qtbot.waitExposed(log_bar.notifications_widget):
        pass
    assert id(log_bar.notifications_widget) == original_id


def test_clear(log_bar: NotificationsBar, qtbot, enable_log):
    assert log_bar.text() == ""

    for i in range(42):
        logger.log(USER_LOGLEVEL, f"msg {i}")

    assert log_bar.text() == "msg 41"

    qtbot.mouseDClick(log_bar, Qt.MouseButton.LeftButton)

    log_history = log_bar.notifications_widget.toPlainText()
    assert len(log_history.split("\n")) == 42

    log_bar.cleanUp()

    assert log_bar.text() == ""
    assert log_bar.notifications_widget.toPlainText() == ""
