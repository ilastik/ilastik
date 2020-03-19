import pathlib
import pickle
from pathlib import Path

import pytest
from ilastik.widgets.ImageFileDialog import ImageFileDialog
from PyQt5.QtCore import QTimer
from volumina.utility import preferences


@pytest.fixture(autouse=True)
def tmp_preferences(tmp_path) -> pathlib.Path:
    old = preferences.get_location()
    new = tmp_path / "tmp_preferences"
    preferences.set_location(new)
    yield new
    preferences.set_location(old)


@pytest.fixture
def image(tmp_path) -> Path:
    image_path = Path(tmp_path) / "some_picture.png"
    image_path.touch()
    return image_path


def test_default_image_directory_is_home_with_blank_preferences_file():
    dialog = ImageFileDialog(None)
    assert dialog.directory().absolutePath() == Path.home().as_posix()


def test_picking_file_updates_default_image_directory_to_previously_used(qtbot, image: Path, tmp_preferences):
    dialog = ImageFileDialog(None)
    qtbot.waitExposed(dialog)

    dialog.selectFile(image.as_posix())

    qtbot.waitUntil(lambda: bool(dialog.selectedFiles()))
    QTimer.singleShot(0, dialog.accept)

    assert dialog.getSelectedPaths() == [image]

    with open(tmp_preferences, "rb") as f:
        assert pickle.load(f) == {dialog.preferences_group: {dialog.preferences_setting: image.as_posix()}}


def test_picking_n5_json_file_returns_directory_path(qtbot, tmp_n5_file: Path):
    dialog = ImageFileDialog(None)
    qtbot.waitExposed(dialog)

    dialog.setDirectory(str(tmp_n5_file))
    dialog.selectFile("attributes.json")

    qtbot.waitUntil(lambda: bool(dialog.selectedFiles()))
    QTimer.singleShot(0, dialog.accept)

    assert dialog.getSelectedPaths() == [tmp_n5_file]
