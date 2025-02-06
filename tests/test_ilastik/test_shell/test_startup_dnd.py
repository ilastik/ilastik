from unittest.mock import Mock, patch

import pytest
from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QMessageBox

from ilastik.shell.gui.ilastikShell import StartupContainer


@pytest.fixture
def startup_container(qtbot):
    container = StartupContainer()
    qtbot.addWidget(container)
    return container


@pytest.fixture
def intercept_info_popup(monkeypatch):
    info_mock = Mock()
    monkeypatch.setattr(QMessageBox, "information", lambda *args: info_mock(*args))
    return info_mock


def drag_n_drop_event(filenames):
    dndevent = Mock()
    urls = [QUrl.fromLocalFile(x) for x in filenames]
    dndevent.mimeData.return_value.has_urls.return_value = True
    dndevent.mimeData.return_value.urls.return_value = urls
    return dndevent


def test_single_ilp_file_drop(qtbot, startup_container):
    event = drag_n_drop_event(["/path/to/project.ilp"])

    with qtbot.waitSignal(startup_container.ilpDropped, timeout=100) as sig_receiver:
        startup_container.dropEvent(event)

    assert sig_receiver.args == ["/path/to/project.ilp"]


def test_multiple_files_drop(intercept_info_popup, startup_container):
    event = drag_n_drop_event(["/path/to/project1.ilp", "/path/to/project2.ilp"])

    startup_container.dropEvent(event)

    intercept_info_popup.assert_called_once_with(
        startup_container,
        "Cannot open more than one 'ilp' file",
        (
            "You were trying to open an ilastik project file via drag and drop. "
            "However, you gave more than a single file.\n\n"
            "Please try again using only a single file with the '.ilp' file extension."
        ),
    )


def test_non_ilp_file_drop(intercept_info_popup, startup_container):
    event = drag_n_drop_event(["/path/to/project.txt"])

    startup_container.dropEvent(event)

    intercept_info_popup.assert_called_once_with(
        startup_container,
        "Cannot open /path/to/project.txt",
        (
            "You were trying to open an ilastik project file via drag and drop. "
            "However, you gave a single file that seems not to be an ilastik project file. "
            "Got /path/to/project.txt.\n\n"
            "Please try again using only a single file with the '.ilp' file extension instead."
        ),
    )


def test_drag_enter_event_local_file_accepted(startup_container):
    event = drag_n_drop_event(["/path/to/project.txt"])
    startup_container.dragEnterEvent(event)
    event.acceptProposedAction.assert_called_once_with()


def test_drag_enter_event_no_urls_returns(startup_container):
    event = Mock()
    event.mimeData.return_value.hasUrls.return_value = False
    startup_container.dragEnterEvent(event)
    event.acceptProposedAction.assert_not_called()
