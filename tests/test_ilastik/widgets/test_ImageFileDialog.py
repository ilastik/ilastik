import json
import pathlib
from pathlib import Path

import pytest
from ilastik.widgets.ImageFileDialog import ImageFileDialog
from qtpy.QtWidgets import QFileDialog
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
    return image_path.resolve()


def test_default_image_directory_is_home_with_blank_preferences_file():
    dialog = ImageFileDialog(None)
    assert dialog.directory().absolutePath() == Path.home().as_posix()


def test_picking_file_updates_default_image_directory_to_previously_used(monkeypatch, image: Path, tmp_preferences):
    monkeypatch.setattr(QFileDialog, "exec_", lambda _: True)
    monkeypatch.setattr(ImageFileDialog, "selectedFiles", lambda _: [image.as_posix()])
    dialog = ImageFileDialog(None)
    assert dialog.getSelectedPaths() == [image]

    with open(tmp_preferences, "r") as f:
        assert json.load(f) == {"DataSelection": {"recent image": image.as_posix()}}


def test_picking_n5_json_file_returns_directory_path(monkeypatch, tmp_n5_file: Path):
    monkeypatch.setattr(QFileDialog, "exec_", lambda _: True)
    monkeypatch.setattr(ImageFileDialog, "selectedFiles", lambda _: [str(tmp_n5_file / "attributes.json")])
    dialog = ImageFileDialog(None)
    assert dialog.getSelectedPaths() == [tmp_n5_file]
