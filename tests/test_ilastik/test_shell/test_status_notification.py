import logging

import pytest

from ilastik.shell.gui.ilastikShell import NotificationsBar, NotificationsWindow
from lazyflow import USER_LOGLEVEL

logger = logging.getLogger("root")


@pytest.fixture
def notifications_bar(qtbot):
    notifications_bar = NotificationsBar()
    qtbot.addWidget(notifications_bar)
    qtbot.addWidget(notifications_bar.notifications_widget)
    with qtbot.waitExposed(notifications_bar):
        notifications_bar.show()
    return notifications_bar


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


def test_print_message(notifications_bar: NotificationsBar, enable_log):
    assert notifications_bar.text() == ""

    some_text = "ilastik logbar"
    logger.log(USER_LOGLEVEL, some_text)
    assert notifications_bar.text() == some_text


def test_double_click_opens_window(notifications_bar, qtbot):
    with qtbot.waitExposed(notifications_bar.notifications_widget):
        notifications_bar.mouseDoubleClickEvent(_event=None)

    assert isinstance(notifications_bar.notifications_widget, NotificationsWindow)


def test_reopen_shows_same_window(notifications_bar: NotificationsBar, qtbot):
    with qtbot.waitExposed(notifications_bar.notifications_widget):
        notifications_bar.mouseDoubleClickEvent(_event=None)

    assert isinstance(notifications_bar.notifications_widget, NotificationsWindow)

    original_id = id(notifications_bar.notifications_widget)
    notifications_bar.notifications_widget.close()

    with qtbot.waitExposed(notifications_bar.notifications_widget):
        notifications_bar.mouseDoubleClickEvent(_event=None)

    assert id(notifications_bar.notifications_widget) == original_id


def test_clear(notifications_bar: NotificationsBar, qtbot, enable_log):
    assert notifications_bar.text() == ""

    for i in range(42):
        logger.log(USER_LOGLEVEL, f"msg {i}")

    assert notifications_bar.text() == "msg 41"

    with qtbot.waitExposed(notifications_bar.notifications_widget):
        notifications_bar.mouseDoubleClickEvent(_event=None)

    log_history = notifications_bar.notifications_widget.toPlainText()
    assert len(log_history.split("\n")) == 42

    notifications_bar.cleanUp()

    assert notifications_bar.text() == ""
    assert notifications_bar.notifications_widget.toPlainText() == ""
