import os
import platform
from unittest import mock

import pytest
from qtpy.QtCore import Qt

from ilastik.applets.dataSelection import multiscaleDatasetBrowser

WIN = platform.system() == "Windows"


def get_dlg(qtbot):
    dlg = multiscaleDatasetBrowser.MultiscaleDatasetBrowser()
    qtbot.addWidget(dlg)
    dlg.show()
    qtbot.waitExposed(dlg)
    return dlg


def test_combo_default_width_does_not_follow_long_history(qtbot, monkeypatch):
    monkeypatch.setattr(multiscaleDatasetBrowser, "line_height", lambda: 11)
    long_uri = "https://example.com/" + "long/" * 200 + "data.zarr"

    dlg = multiscaleDatasetBrowser.MultiscaleDatasetBrowser(history=[long_uri])
    qtbot.addWidget(dlg)
    dlg.show()
    qtbot.waitExposed(dlg)

    assert dlg.combo.sizeHint().width() == 24 * 11
    assert dlg.combo.sizePolicy().horizontalPolicy() == multiscaleDatasetBrowser.QSizePolicy.Expanding
    assert dlg.sizeHint().width() < 1000
    assert dlg.width() < 1000


@pytest.mark.parametrize(
    "text_input,expected",
    [
        ("https://example.com/data.zarr", "https://example.com/data.zarr"),
        ("precomputed://https://example.com", "precomputed://https://example.com"),
        ("https://example.com/p?q%20#a", "https://example.com/p?q%20#a"),
    ],
)
def test_validate_uri(text_input, expected):
    assert multiscaleDatasetBrowser._validate_uri(text_input) == expected


@pytest.mark.parametrize(
    "invalid_input",
    [
        "",
        "example.com",  # Missing protocol
    ],
)
def test_validate_uri_raises(invalid_input):
    with pytest.raises(ValueError):
        multiscaleDatasetBrowser._validate_uri(invalid_input)


@pytest.mark.skipif(WIN, reason="Can't test unix paths on Windows")
@pytest.mark.parametrize(
    "text_input,expected",
    [
        ("/", "file:///"),
        ("file:///home/", "file:///home/"),
        # Actually malformed (missing empty host). Maps to //home/, which
        # "may be interpreted in an implementation-defined manner".
        # Seems to correctly resolve to /home/ on common systems though.
        ("file://home/", "file://home/"),
    ],
)
def test_validate_uri_from_posix_path(text_input, expected):
    assert multiscaleDatasetBrowser._validate_uri(text_input) == expected


@pytest.mark.skipif(WIN, reason="Can't test unix paths on Windows")
@pytest.mark.parametrize(
    "invalid_input",
    [
        "/gibberish_123/",  # Path does not exist
    ],
)
def test_validate_uri_from_posix_path_raises(invalid_input):
    with pytest.raises(ValueError):
        multiscaleDatasetBrowser._validate_uri(invalid_input)


@pytest.mark.skipif(not WIN, reason="Windows paths can only be tested on Windows")
@pytest.mark.parametrize(
    "text_input,expected",
    [
        ("C:\\", "file:///C:/"),
        ("C:/", "file:///C:/"),
        ("file:///C:\\", "file:///C:\\"),  # User manually added protocol
        ("file:///C:/", "file:///C:/"),
    ],
)
def test_validate_uri_from_Windows_path(text_input, expected):
    assert multiscaleDatasetBrowser._validate_uri(text_input) == expected


@pytest.mark.skipif(not WIN, reason="Windows paths can only be tested on Windows")
@pytest.mark.parametrize(
    "dir_name",
    [
        "dirname with space",
        "dirname%20with%percent",
    ],
)
def test_validate_uri_from_existing_Windows_path_with_special_characters(tmp_path, dir_name):
    full_path = tmp_path / dir_name
    os.mkdir(full_path)
    text_input = str(full_path)
    expected = full_path.as_uri()
    try:
        assert multiscaleDatasetBrowser._validate_uri(text_input) == expected
    finally:
        os.rmdir(full_path)


@pytest.mark.skipif(not WIN, reason="Windows paths can only be tested on Windows")
@pytest.mark.parametrize(
    "invalid_input",
    [
        "C:\\gibberish_123",  # Path does not exist
        "file:///C:\\gibberish_123",  # Path does not exist
        "file://C:\\",  # Missing empty host
    ],
)
def test_validate_uri_from_Windows_path_raises(invalid_input):
    with pytest.raises(ValueError):
        multiscaleDatasetBrowser._validate_uri(invalid_input)


def test_browse_button_selects_directory_and_checks(qtbot, tmp_path):
    selected_directory = tmp_path / "dataset.ome.zarr"
    selected_directory.mkdir()

    with mock.patch.object(multiscaleDatasetBrowser.preferences, "get", return_value=tmp_path):
        with mock.patch.object(multiscaleDatasetBrowser.preferences, "set"):
            with mock.patch.object(
                multiscaleDatasetBrowser.QFileDialog, "getExistingDirectory", return_value=str(selected_directory)
            ) as select_directory:
                dialog = get_dlg(qtbot)
                with mock.patch.object(dialog, "_validate_text_input") as validate:
                    qtbot.mouseClick(dialog.browse_button, Qt.MouseButton.LeftButton)

    select_directory.assert_called_once()
    validate.assert_called_once_with()
    assert dialog.combo.lineEdit().text() == str(selected_directory)


def test_browse_button_cancel_keeps_current_text(qtbot, tmp_path):
    with mock.patch.object(multiscaleDatasetBrowser.preferences, "get", return_value=tmp_path):
        with mock.patch.object(multiscaleDatasetBrowser.preferences, "set"):
            with mock.patch.object(multiscaleDatasetBrowser.QFileDialog, "getExistingDirectory", return_value=""):
                dialog = get_dlg(qtbot)
                dialog.combo.lineEdit().setText("https://example.com/data.zarr")

                with mock.patch.object(dialog.check_button, "click") as check_button_click:
                    qtbot.mouseClick(dialog.browse_button, Qt.MouseButton.LeftButton)

    check_button_click.assert_not_called()
    assert dialog.combo.lineEdit().text() == "https://example.com/data.zarr"


def test_browse_button_reads_recent_starting_path_from_preferences(qtbot, tmp_path):
    recent_directory = tmp_path / "recent.ome.zarr"
    recent_directory.mkdir()

    with mock.patch.object(multiscaleDatasetBrowser.preferences, "get", return_value=recent_directory) as pref_get:
        with mock.patch.object(
            multiscaleDatasetBrowser.QFileDialog, "getExistingDirectory", return_value=""
        ) as select_directory:
            dialog = get_dlg(qtbot)
            qtbot.mouseClick(dialog.browse_button, Qt.MouseButton.LeftButton)

    pref_get.assert_called_once_with(dialog.PREFERENCES_GROUP, dialog.PREFERENCES_SETTING, mock.ANY)
    select_directory.assert_called_once()
    args, _kwargs = select_directory.call_args
    assert args[2] == str(recent_directory)


def test_browse_button_writes_accepted_path_to_preferences(qtbot, tmp_path):
    selected_directory = tmp_path / "selected.ome.zarr"
    selected_directory.mkdir()

    with mock.patch.object(multiscaleDatasetBrowser.preferences, "get", return_value=tmp_path):
        with mock.patch.object(
            multiscaleDatasetBrowser.QFileDialog, "getExistingDirectory", return_value=str(selected_directory)
        ):
            dialog = get_dlg(qtbot)
            with mock.patch.object(multiscaleDatasetBrowser.preferences, "set") as pref_set:
                with mock.patch.object(dialog.check_button, "click"):
                    qtbot.mouseClick(dialog.browse_button, Qt.MouseButton.LeftButton)

    pref_set.assert_called_once_with(
        dialog.PREFERENCES_GROUP,
        dialog.PREFERENCES_SETTING,
        selected_directory.as_posix(),
    )


def test_browse_button_does_not_write_path_to_preferences_on_cancel(qtbot, tmp_path):
    with mock.patch.object(multiscaleDatasetBrowser.preferences, "get", return_value=tmp_path):
        with mock.patch.object(multiscaleDatasetBrowser.QFileDialog, "getExistingDirectory", return_value=""):
            dialog = get_dlg(qtbot)
            with mock.patch.object(multiscaleDatasetBrowser.preferences, "set") as pref_set:
                qtbot.mouseClick(dialog.browse_button, Qt.MouseButton.LeftButton)

    pref_set.assert_not_called()


def test_browse_button_uses_existing_input_as_starting_path(qtbot, tmp_path):
    recent_directory = tmp_path / "recent.ome.zarr"
    recent_directory.mkdir()
    input_directory = tmp_path / "input.ome.zarr"
    input_directory.mkdir()

    with mock.patch.object(multiscaleDatasetBrowser.preferences, "get", return_value=recent_directory):
        with mock.patch.object(
            multiscaleDatasetBrowser.QFileDialog, "getExistingDirectory", return_value=""
        ) as select_directory:
            dialog = get_dlg(qtbot)
            dialog.combo.lineEdit().setText(str(input_directory))
            qtbot.mouseClick(dialog.browse_button, Qt.MouseButton.LeftButton)

    select_directory.assert_called_once()
    args, _kwargs = select_directory.call_args
    assert args[2] == str(input_directory)


def test_browse_button_cancel_does_not_check(qtbot, tmp_path):
    with mock.patch.object(multiscaleDatasetBrowser.preferences, "get", return_value=tmp_path):
        with mock.patch.object(multiscaleDatasetBrowser.QFileDialog, "getExistingDirectory", return_value=""):
            dialog = get_dlg(qtbot)
            with mock.patch.object(dialog, "_validate_text_input") as validate:
                qtbot.mouseClick(dialog.browse_button, Qt.MouseButton.LeftButton)

    validate.assert_not_called()
