from unittest import mock

import pytest
from ilastik.applets.batchProcessing.batchProcessingGui import (
    BatchProcessingDataConstraintException,
    BatchProcessingGui,
    BatchRoleWidget,
    FileListWidget,
)
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


@pytest.fixture()
def role_names():
    return ["testRoleName1", "testRoleName2", "testRoleName3"]


@pytest.fixture()
def parent_applet(role_names):
    parent_applet = mock.Mock()
    parent_applet.dataSelectionApplet.topLevelOperator.DatasetRoles.value = role_names
    parent_applet.run_export = mock.Mock()

    return parent_applet


@pytest.fixture()
def batch_processing_gui(qtbot, parent_applet):
    return construct_widget(qtbot, BatchProcessingGui, parent_applet)


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


class RequestMock:
    _instances = []

    def __new__(cls, *args, **kwargs):
        instance = mock.Mock()
        cls._instances.append(instance)
        return instance


def assert_buttons_in_init_state(batch_processing_gui):
    assert batch_processing_gui.run_button.isEnabled() is True
    assert batch_processing_gui.cancel_button.isVisible() is False


def assert_buttons_in_running_state(batch_processing_gui):
    assert batch_processing_gui.run_button.isEnabled() is False
    assert batch_processing_gui.cancel_button.isVisible() is True
    assert batch_processing_gui.cancel_button.isEnabled() is True


def test_BatchProcessingGui_execution(qtbot, batch_processing_gui, role_names, filenames):
    assert batch_processing_gui.count() == len(role_names)
    assert_buttons_in_init_state(batch_processing_gui)

    with mock.patch("ilastik.applets.batchProcessing.batchProcessingGui.Request", new=RequestMock):
        qtbot.mouseClick(batch_processing_gui.run_button, Qt.LeftButton, delay=1)
        assert len(RequestMock._instances) == 0

        # add some data
        batch_processing_gui._data_role_widgets[role_names[0]].list_widget.addItems(filenames)

        qtbot.mouseClick(batch_processing_gui.run_button, Qt.LeftButton, delay=1)
        assert len(RequestMock._instances) == 1
        assert_buttons_in_running_state(batch_processing_gui)

        # pretend we were successful:
        req = RequestMock._instances[0]
        success_args, success_kwargs = req.notify_finished.call_args
        assert len(success_args) == 1
        success_args[0]()

        assert_buttons_in_init_state(batch_processing_gui)

        qtbot.mouseClick(batch_processing_gui.run_button, Qt.LeftButton, delay=1)
        assert len(RequestMock._instances) == 2
        assert_buttons_in_running_state(batch_processing_gui)

        # cancel:
        qtbot.mouseClick(batch_processing_gui.cancel_button, Qt.LeftButton, delay=1)
        req = RequestMock._instances[1]
        req.cancel.assert_called_once()
        cancel_args, cancel_kwargs = req.notify_cancelled.call_args
        assert len(cancel_args) == 1

        info_messagebox = mock.Mock()
        with mock.patch(
            "ilastik.applets.batchProcessing.batchProcessingGui.QMessageBox.information", new=info_messagebox
        ):
            cancel_args[0]()
            info_messagebox.assert_called_once()

        assert_buttons_in_init_state(batch_processing_gui)

        # failure:
        qtbot.mouseClick(batch_processing_gui.run_button, Qt.LeftButton, delay=1)
        assert len(RequestMock._instances) == 3
        assert_buttons_in_running_state(batch_processing_gui)

        req = RequestMock._instances[2]
        failed_args, failed_kwargs = req.notify_failed.call_args
        assert len(failed_args) == 1

        critical_messagebox = mock.Mock()
        with mock.patch(
            "ilastik.applets.batchProcessing.batchProcessingGui.QMessageBox.critical", new=critical_messagebox
        ):
            failed_args[0](mock.MagicMock(Exception), None)
            critical_messagebox.assert_called_once()

        assert_buttons_in_init_state(batch_processing_gui)


def test_BatchProcessingGui_clear(qtbot, batch_processing_gui, role_names, filenames):
    for role_name in role_names:
        current_data_role_widget = batch_processing_gui._data_role_widgets[role_name]
        current_data_role_widget.list_widget.addItems(filenames)
        assert current_data_role_widget.list_widget.count() == len(filenames)

    for role_name in role_names:
        current_data_role_widget = batch_processing_gui._data_role_widgets[role_name]
        qtbot.mouseClick(current_data_role_widget.clear_button, Qt.LeftButton, delay=1)
        assert current_data_role_widget.list_widget.count() == 0


@pytest.mark.parametrize(
    "secondary_files",
    [tuple(), ("sec1",), ("sec1", "sec2"), ("sec1", "sec2", "sec3"), ("sec1", "sec2", "sec3", "sec4")],
)
def test_BatchProcessingGui_nonmatching_raises(qtbot, batch_processing_gui, role_names, filenames, secondary_files):
    batch_processing_gui._data_role_widgets[role_names[0]].list_widget.addItems(filenames)
    secondary_data_role = batch_processing_gui._data_role_widgets[role_names[1]]
    with mock.patch("ilastik.applets.batchProcessing.batchProcessingGui.Request", new=RequestMock):
        secondary_data_role.list_widget.addItems(secondary_files)
        if len(secondary_files) > 0 and (len(secondary_files) != len(filenames)):
            with qtbot.capture_exceptions() as exceptions:
                qtbot.mouseClick(batch_processing_gui.run_button, Qt.LeftButton, delay=1)
            assert len(exceptions) == 1
            exc_class, exc_instance, exc_traceback = exceptions[0]
            assert exc_class == BatchProcessingDataConstraintException
        else:
            qtbot.mouseClick(batch_processing_gui.run_button, Qt.LeftButton, delay=1)
