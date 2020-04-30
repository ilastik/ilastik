from unittest import mock
from contextlib import contextmanager, nullcontext

import pytest
from pytestqt.exceptions import capture_exceptions
from ilastik.applets.batchProcessing.batchProcessingGui import (
    BatchProcessingGui,
    BatchRoleWidget,
    FileListWidget,
)
from ilastik.applets.dataSelection.dataSelectionApplet import RoleMismatchException
from PyQt5.QtCore import Qt, QUrl


def prepare_widget(qtbot, widget):
    qtbot.addWidget(widget)
    widget.show()
    qtbot.waitForWindowShown(widget)
    return widget


@pytest.fixture
def file_list_widget(qtbot):
    return prepare_widget(qtbot, FileListWidget())


@pytest.fixture
def batch_role_widget(qtbot):
    return prepare_widget(qtbot, BatchRoleWidget("TestRoleName"))


@pytest.fixture()
def role_names():
    return ["testRoleName1", "testRoleName2", "testRoleName3"]


@pytest.fixture()
def parent_applet(role_names):
    parent_applet = mock.Mock()
    parent_applet.dataSelectionApplet.role_names = role_names
    parent_applet.run_export = mock.Mock()

    return parent_applet


@pytest.fixture()
def batch_processing_gui(qtbot, parent_applet):
    return prepare_widget(qtbot, BatchProcessingGui(parent_applet))


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
    assert "TestRoleName" in batch_role_widget.select_button.text()
    assert "TestRoleName" in batch_role_widget.clear_button.text()

    assert batch_role_widget.list_widget.count() == 0

    batch_role_widget.list_widget.addItems(filenames)
    assert batch_role_widget.filepaths == filenames

    qtbot.mouseClick(batch_role_widget.clear_button, Qt.LeftButton, delay=1)
    assert len(batch_role_widget.filepaths) == 0


def RequestMock(instances=None):
    if instances is None:
        instances = []

    def inner(*args, **kwargs):
        instances.append(mock.Mock())
        return instances[-1]

    return inner


def assert_gui_in_init_state(batch_processing_gui):
    gui = batch_processing_gui
    assert gui.run_button.isEnabled() and not gui.cancel_button.isVisible()


def assert_gui_in_running_state(batch_processing_gui):
    gui = batch_processing_gui
    assert not gui.run_button.isEnabled() and gui.cancel_button.isVisible() and gui.cancel_button.isEnabled()


def test_BatchProcessingGui_execution(qtbot, batch_processing_gui, role_names, filenames):
    assert batch_processing_gui.count() == len(role_names)
    assert_gui_in_init_state(batch_processing_gui)

    request_instances = []
    request_mock = RequestMock(request_instances)
    with mock.patch("ilastik.applets.batchProcessing.batchProcessingGui.Request", new=request_mock):
        qtbot.mouseClick(batch_processing_gui.run_button, Qt.LeftButton, delay=1)
        assert len(request_instances) == 0

        # add some data
        batch_processing_gui._data_role_widgets[role_names[0]].list_widget.addItems(filenames)

        qtbot.mouseClick(batch_processing_gui.run_button, Qt.LeftButton, delay=1)
        assert len(request_instances) == 1
        assert_gui_in_running_state(batch_processing_gui)

        # pretend we were successful:
        req = request_instances.pop()
        success_args, success_kwargs = req.notify_finished.call_args
        assert len(success_args) == 1
        success_args[0]()

        assert_gui_in_init_state(batch_processing_gui)

        qtbot.mouseClick(batch_processing_gui.run_button, Qt.LeftButton, delay=1)
        assert len(request_instances) == 1
        assert_gui_in_running_state(batch_processing_gui)

        # cancel:
        qtbot.mouseClick(batch_processing_gui.cancel_button, Qt.LeftButton, delay=1)
        req = request_instances.pop()
        req.cancel.assert_called_once()
        cancel_args, cancel_kwargs = req.notify_cancelled.call_args
        assert len(cancel_args) == 1

        info_messagebox = mock.Mock()
        with mock.patch(
            "ilastik.applets.batchProcessing.batchProcessingGui.QMessageBox.information", new=info_messagebox
        ):
            cancel_args[0]()
            info_messagebox.assert_called_once()

        assert_gui_in_init_state(batch_processing_gui)

        # failure:
        qtbot.mouseClick(batch_processing_gui.run_button, Qt.LeftButton, delay=1)
        assert len(request_instances) == 1
        assert_gui_in_running_state(batch_processing_gui)

        req = request_instances.pop()
        failed_args, failed_kwargs = req.notify_failed.call_args
        assert len(failed_args) == 1

        critical_messagebox = mock.Mock()
        with mock.patch(
            "ilastik.applets.batchProcessing.batchProcessingGui.QMessageBox.critical", new=critical_messagebox
        ):
            failed_args[0](mock.MagicMock(Exception), None)
            critical_messagebox.assert_called_once()

        assert_gui_in_init_state(batch_processing_gui)


def test_BatchProcessingGui_clear(qtbot, batch_processing_gui, role_names, filenames):
    for role_name in role_names:
        current_data_role_widget = batch_processing_gui._data_role_widgets[role_name]
        current_data_role_widget.list_widget.addItems(filenames)
        assert current_data_role_widget.list_widget.count() == len(filenames)

    for role_name in role_names:
        current_data_role_widget = batch_processing_gui._data_role_widgets[role_name]
        qtbot.mouseClick(current_data_role_widget.clear_button, Qt.LeftButton, delay=1)
        assert current_data_role_widget.list_widget.count() == 0


does_not_raise = nullcontext()


@contextmanager
def assert_raises(exception_type):
    with capture_exceptions() as exp:
        yield
        if not exp:
            raise AssertionError("No exception raised")
        elif issubclass(exp[0][0], exception_type):
            return
        else:
            raise AssertionError(f"Assertion type {exp[0][0]} does not match expected type {exception_type}")


@pytest.mark.parametrize(
    "secondary_files,expectation",
    [
        (tuple(), does_not_raise),
        (("sec1",), does_not_raise),
        (("sec1", "sec2"), does_not_raise),
        #(("sec1", "sec2", "sec3"), assert_raises(RoleMismatchException)), # needs a real DataSelectionApplet
        #(("sec1", "sec2", "sec3", "sec4"), assert_raises(RoleMismatchException)), # needs a real DataSelectionApplet
    ],
)
def test_BatchProcessingGui_nonmatching_raises(
    qtbot, batch_processing_gui, role_names, filenames, secondary_files, expectation
):
    batch_processing_gui._data_role_widgets[role_names[0]].list_widget.addItems(filenames)
    secondary_data_role = batch_processing_gui._data_role_widgets[role_names[1]]
    with mock.patch("ilastik.applets.batchProcessing.batchProcessingGui.Request", new=RequestMock()):
        secondary_data_role.list_widget.addItems(secondary_files)
        with expectation:
            qtbot.mouseClick(batch_processing_gui.run_button, Qt.LeftButton, delay=1)
