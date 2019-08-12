from unittest import mock

import pytest
from ilastik.applets.batchProcessing.batchProcessingGui import (BatchProcessingGui,
                                                                BatchRoleWidget,
                                                                FileListWidget)
from PyQt5.QtCore import Qt, QUrl


def construct_widget(qtbot, widget_class, *args, **kwargs):
    widget = widget_class(*args, **kwargs)
    qtbot.addWidget(widget)
    widget.show()
    qtbot.waitForWindowShown(widget)
    return widget


@pytest.fixture
def file_list_widget(qtbot):
    return construct_widget(qtbot, FileListWidget)


@pytest.fixture
def batch_role_widget(qtbot):
    return construct_widget(qtbot, BatchRoleWidget, "TestRoleName")


@pytest.fixture
def filenames():
    return ["file1", "file2"]


@pytest.fixture
def drag_n_drop_event(filenames):
    dndevent = mock.Mock()
    urls = [QUrl(x) for x in filenames]
    for url in urls:
        url.isLocalFile = mock.Mock(return_value=True)
    dndevent.mimeData.return_value.has_urls.return_value = True
    dndevent.mimeData.return_value.urls.return_value = urls
    return dndevent


def test_FileListWidget_drag_n_drop(file_list_widget, drag_n_drop_event, filenames):
    assert file_list_widget.count() == 0

    file_list_widget.dragEnterEvent(drag_n_drop_event)
    assert drag_n_drop_event.acceptProposedAction.called_once()
    assert file_list_widget.count() == 0

    file_list_widget.dropEvent(drag_n_drop_event)
    assert file_list_widget.count() == len(filenames)
    for url in filenames:
        items = file_list_widget.findItems(url, Qt.MatchFixedString)
        assert len(items) == 1


def test_BatchRoleWidget(qtbot, batch_role_widget, filenames):
    assert batch_role_widget.select_button.text() == f"Select TestRoleName Files..."
    assert batch_role_widget.clear_button.text() == f"Clear TestRoleName Files"

    assert batch_role_widget.list_widget.count() == 0

    batch_role_widget.list_widget.addItems(filenames)
    assert batch_role_widget.filepaths == filenames

    qtbot.mouseClick(batch_role_widget.clear_button, Qt.LeftButton, delay=1)
    assert len(batch_role_widget.filepaths) == 0
