import pytest

from ilastik.app import STARTUP_MARKER
from ilastik.shell.gui.reportIssueDialog import _get_log_since_last_startup, _mask_file_paths, FILE_PATH_MASK


@pytest.mark.parametrize(
    "full_log, expected_truncation",
    [
        ("", ""),
        (f"{STARTUP_MARKER}\nsome\ntext_after", f"{STARTUP_MARKER}\nsome\ntext_after"),
        (f"987654321{STARTUP_MARKER}", f"54321{STARTUP_MARKER}"),
    ],
)
def test_get_log_since_last_startup(monkeypatch, tmp_path, full_log, expected_truncation):
    log_path = tmp_path / "testlog.txt"
    log_path.write_text(full_log)  # This might add \r before \n (OS-dependent)
    monkeypatch.setattr("ilastik.ilastik_logging.default_config.get_logfile_path", lambda: log_path)
    adjusted_for_CR = _get_log_since_last_startup(pre_marker_padding=5).replace("\r", "")
    assert adjusted_for_CR == expected_truncation


@pytest.mark.parametrize(
    "input_log, masked_log",
    [
        ("", ""),
        ("some text/home/me/dir/file.tif", f"some text{FILE_PATH_MASK}"),
        ("some/slash\nand/another", "some/slash\nand/another"),
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
