import pytest
from pathlib import Path

from PyQt5.QtCore import QTimer

from ilastik.widgets.ImageFileDialog import ImageFileDialog
from volumina.utility import PreferencesManager


@pytest.fixture
def blank_preferences_file(tmp_path) -> Path:
    return tmp_path / "my_preferences"


@pytest.fixture
def blank_preferences(blank_preferences_file: Path) -> PreferencesManager:
    return PreferencesManager(path=blank_preferences_file)


@pytest.fixture
def image(tmp_path) -> Path:
    image_path = Path(tmp_path / "some_picture.png")
    image_path.touch()
    return image_path


def test_default_image_directory_is_home_with_blank_preferences_file(blank_preferences: PreferencesManager):
    dialog = ImageFileDialog(None, preferences_manager=blank_preferences)
    assert dialog.directory().absolutePath() == Path("~").expanduser().absolute().as_posix()


def test_picking_file_updates_default_image_directory_to_previously_used(blank_preferences_file: Path, image: Path):
    dialog = ImageFileDialog(None, preferences_manager=PreferencesManager(blank_preferences_file))
    assert dialog.directory().absolutePath() == Path("~").expanduser().absolute().as_posix()
    dialog.selectFile(image.as_posix())
    QTimer.singleShot(1000, dialog.accept)
    assert dialog.getSelectedPaths() == [image]

    dialog = ImageFileDialog(None, preferences_manager=PreferencesManager(blank_preferences_file))
    assert Path(dialog.directory().absolutePath()) == blank_preferences_file.parent


def test_picking_n5_json_file_returns_directory_path(tmp_n5_file: Path, blank_preferences: PreferencesManager):
    dialog = ImageFileDialog(None, preferences_manager=blank_preferences)
    dialog.selectFile(tmp_n5_file.joinpath("attributes.json").as_posix())
    QTimer.singleShot(1000, dialog.accept)
    assert dialog.getSelectedPaths() == [tmp_n5_file]
