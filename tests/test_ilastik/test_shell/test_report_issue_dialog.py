from unittest import mock

import pytest

from ilastik.shell.gui.reportIssueDialog import _mask_file_paths, FILE_PATH_MASK, ReportIssueDialog, FORUM_URI


@pytest.mark.parametrize(
    "input_log, masked_log",
    [
        ("", ""),
        ("some text/home/me/dir/file.tif", f"some text{FILE_PATH_MASK}"),
        ("some/slash\nand/another", "some/slash\nand/another"),
        ("some/slash and/another", "some/slash and/another"),
        ("backslashes C:\\\\might\\\\be\\\\doubled", f"backslashes {FILE_PATH_MASK}"),
        ("textC:\\dir with space\\", f"text{FILE_PATH_MASK}"),
        ("textC:\\space in file.tif", f"text{FILE_PATH_MASK} in file.tif"),  # don't think we can catch this
        ("textC:/Users/me/file.tif", f"text{FILE_PATH_MASK}"),
        ("textC:/dir with space/", f"text{FILE_PATH_MASK}"),
        ("C:/dir actually\nsome other text with slash/", f"{FILE_PATH_MASK} actually\nsome other text with slash/"),
        ("textC:/file with space.tif", f"text{FILE_PATH_MASK} with space.tif"),  # don't think we can catch this
        (f"some text{FILE_PATH_MASK}", f"some text{FILE_PATH_MASK}"),
        ("some-text/home-not a path", "some-text/home-not a path"),
        ("text with https://url.com/should/ be replaced", f"text with https:/{FILE_PATH_MASK} be replaced"),
        ("text with file:///C:/url/should/be replaced", f"text with file://{FILE_PATH_MASK} replaced"),
    ],
)
def test_mask_file_paths(input_log, masked_log):
    assert _mask_file_paths(input_log) == masked_log


@pytest.fixture
def dialog(qtbot):
    dlg = ReportIssueDialog()
    dlg.show()
    qtbot.addWidget(dlg)
    qtbot.waitExposed(dlg)
    return dlg


@pytest.fixture
def mock_webbrowser(monkeypatch):
    patch = mock.Mock()
    monkeypatch.setattr("webbrowser.open", patch)
    return patch


def test_dialog_runs(dialog):
    assert dialog.isVisible()


def test_link_to_forum(dialog, mock_webbrowser):
    dialog.copy_and_go_to_forum()
    mock_webbrowser.assert_called_once_with(FORUM_URI)


def test_link_to_mail(dialog, mock_webbrowser):
    dialog.open_in_email_app()
    mock_webbrowser.assert_called_once()
    assert mock_webbrowser.call_args.args[0].startswith("mailto:")
