import os
from unittest import mock

from PyQt5.QtCore import Qt
from pytest import fixture

from ilastik.shell.gui.licenseDialog import LicenseDialog


@fixture
def get_dlg(qtbot):
    dlg = LicenseDialog()
    qtbot.addWidget(dlg)
    qtbot.waitExposed(dlg)
    return dlg


@fixture
def mock_license(tmp_path):
    mock_text = "this is just a test license - 42"
    f = tmp_path / "LICENSE"
    f.write_text(mock_text)
    return f, mock_text


def test_license_dlg_construct(qtbot):
    dlg = get_dlg(qtbot)
    assert dlg.isVisible()


def test_license_dlg_default_license(qtbot, tmp_path):
    with mock.patch("ilastik.__file__", new=str(tmp_path / "ilastik" / "__init__.py")):
        dlg = get_dlg(qtbot)

    license_path = tmp_path / "LICENSE"
    license_path.touch()
    mock_open = mock.Mock()
    mock_error_msg = mock.Mock()
    with mock.patch("webbrowser.open", mock_open):
        with mock.patch("PyQt5.QtWidgets.QMessageBox.warning", mock_error_msg):
            qtbot.mouseClick(dlg._show_details_btn, Qt.MouseButton.LeftButton)

    mock_open.assert_called_once_with(license_path.as_uri())
    mock_error_msg.assert_not_called()


def test_license_dlg_license(qtbot, mock_license):
    license_path, license_text = mock_license
    with mock.patch.dict(os.environ, {"ILASTIK_LICENSE_PATH": str(license_path)}):
        dlg = get_dlg(qtbot)

    mock_open = mock.Mock()
    mock_error_msg = mock.Mock()
    with mock.patch("webbrowser.open", mock_open):
        with mock.patch("PyQt5.QtWidgets.QMessageBox.warning", mock_error_msg):
            qtbot.mouseClick(dlg._show_details_btn, Qt.MouseButton.LeftButton)

    mock_open.assert_called_once_with(license_path.as_uri())
    mock_error_msg.assert_not_called()


def test_license_dlg_license_notfound(qtbot):
    with mock.patch.dict(os.environ, {"ILASTIK_LICENSE_PATH": "_some_bogus_nonexistant_path_42_"}):
        dlg = get_dlg(qtbot)

    mock_open = mock.Mock()
    mock_error_msg = mock.Mock()
    with mock.patch("webbrowser.open", mock_open):
        with mock.patch("PyQt5.QtWidgets.QMessageBox.warning", mock_error_msg):
            qtbot.mouseClick(dlg._show_details_btn, Qt.MouseButton.LeftButton)

    mock_open.assert_not_called()
    mock_error_msg.assert_called_once_with(dlg, "License file not found!", LicenseDialog.LICENSE_ERROR)


def test_license_dlg_3rdp_license(qtbot, mock_license):
    license_path, license_text = mock_license
    with mock.patch.dict(os.environ, {"ILASTIK_LICENSE_3RD_PARTY_PATH": str(license_path)}):
        dlg = get_dlg(qtbot)

    mock_open = mock.Mock()
    mock_error_msg = mock.Mock()
    with mock.patch("webbrowser.open", mock_open):
        with mock.patch("PyQt5.QtWidgets.QMessageBox.warning", mock_error_msg):
            qtbot.mouseClick(dlg._show_3rd_party_btn, Qt.MouseButton.LeftButton)

    mock_open.assert_called_once_with(license_path.as_uri())
    mock_error_msg.assert_not_called()


def test_license_dlg_3rdp_license_notfound(qtbot, mock_license):
    license_path, license_text = mock_license
    with mock.patch.dict(os.environ, {"ILASTIK_LICENSE_3RD_PARTY_PATH": "_some_bogus_nonexistant_path_42_"}):
        dlg = get_dlg(qtbot)

    mock_open = mock.Mock()
    mock_error_msg = mock.Mock()
    with mock.patch("webbrowser.open", mock_open):
        with mock.patch("PyQt5.QtWidgets.QMessageBox.warning", mock_error_msg):
            qtbot.mouseClick(dlg._show_3rd_party_btn, Qt.MouseButton.LeftButton)

    mock_open.assert_not_called()
    mock_error_msg.assert_called_once_with(dlg, "License file not found!", LicenseDialog.LICENSE_3RD_PARTY_ERROR)
