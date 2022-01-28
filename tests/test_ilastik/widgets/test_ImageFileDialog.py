import json
import pathlib
from pathlib import Path
import platform

import pytest
from ilastik.widgets.ImageFileDialog import ImageFileDialog
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication
from volumina.utility import preferences


@pytest.fixture(autouse=True)
def tmp_preferences(tmp_path) -> pathlib.Path:
    old = preferences.get_path()
    new = tmp_path / "tmp_preferences"
    preferences.set_path(new)
    yield new
    preferences.set_path(old)


@pytest.fixture
def image(tmp_path) -> Path:
    image_path = Path(tmp_path) / "some_picture.png"
    image_path.touch()
    return image_path


def test_default_image_directory_is_home_with_blank_preferences_file():
    dialog = ImageFileDialog(None)
    assert dialog.directory().absolutePath() == Path.home().as_posix()


@pytest.mark.skipif(platform.system() == "Darwin", reason="This test hangs on osx.")
def test_picking_file_updates_default_image_directory_to_previously_used(image: Path, tmp_preferences):
    dialog = ImageFileDialog(None)
    dialog.selectFile(image.as_posix())

    def handle_dialog():
        while not dialog.isVisible():
            QApplication.processEvents()

        dialog.accept()

    QTimer.singleShot(0, handle_dialog)
    assert dialog.getSelectedPaths() == [image]

    with open(tmp_preferences, "r") as f:
        assert json.load(f) == {"DataSelection": {"recent image": image.as_posix()}}


@pytest.mark.skipif(platform.system() == "Darwin", reason="This test hangs on osx.")
def test_picking_n5_json_file_returns_directory_path(tmp_n5_file: Path):
    dialog = ImageFileDialog(None)
    dialog.setDirectory(str(tmp_n5_file))
    dialog.selectFile("attributes.json")

    def handle_dialog():
        while not dialog.isVisible():
            QApplication.processEvents()

        dialog.accept()

    QTimer.singleShot(0, handle_dialog)

    assert dialog.getSelectedPaths() == [tmp_n5_file]
