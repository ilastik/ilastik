from pathlib import Path
from typing import Annotated
from unittest import mock

import pytest
from annotated_types import Ge, Le
from pydantic import BaseModel

from ilastik.config import Increment
from ilastik.shell.gui.preferencesDialog import ADVANCED, PreferencesDialog, PreferencesModel


class Section1(BaseModel):
    numerical: Annotated[int, Ge(-10), Le(123), Increment(5)] = 1
    """docstring for numerical"""

    stringy: str = "section1-test-text"
    """docstring for string"""

    booly: bool = False
    """docstring for bool"""


class Section2(BaseModel):
    numerical: Annotated[int, Ge(-10), Le(123), Increment(5)] = 1
    """docstring for numerical"""

    booly: bool = False
    """docstring for bool"""

    bool_advanced: Annotated[bool, ADVANCED] = False


class ConfigBase(BaseModel):
    section1: Section1 = Section1()
    section2: Section2 = Section2()


@pytest.fixture
def config():
    return ConfigBase()


@pytest.fixture
def patch_config(tmp_path):
    f = tmp_path / "testconfig.ini"
    with mock.patch("ilastik.config.cfg_path", new=f):
        yield f


@pytest.fixture
def dlg(qtbot, config, patch_config) -> PreferencesDialog:
    model = PreferencesModel(config)
    dlg = PreferencesDialog(parent=None, model=model)
    dlg.show()
    qtbot.addWidget(dlg)
    qtbot.waitExposed(dlg)
    return dlg


def test_construct(dlg: PreferencesDialog):
    assert dlg.isVisible()


@pytest.mark.parametrize(
    "checkstates",
    [
        (("section1", "booly", False), ("section1", "booly", False)),
        (("section1", "booly", True), ("section2", "booly", False)),
        (("section1", "booly", False), ("section2", "booly", True)),
        (("section1", "booly", True), ("section2", "booly", True)),
    ],
)
def test_bool_options(dlg: PreferencesDialog, checkstates):
    for section_name, option_name, value in checkstates:
        dlg.model.setValue(section_name, option_name, value)

    for section_name, option_name, value in checkstates:
        assert dlg.options2widgets[(section_name, option_name)].isChecked() == value


@pytest.mark.parametrize(
    "textstates",
    [
        (("section1", "stringy", ""),),
        (("section1", "stringy", "abc"),),
        (("section1", "stringy", "12345"),),
    ],
)
def test_text_options(dlg: PreferencesDialog, textstates):
    for section_name, option_name, value in textstates:
        dlg.model.setValue(section_name, option_name, value)

    for section_name, option_name, value in textstates:
        assert dlg.options2widgets[(section_name, option_name)].text() == value


@pytest.mark.parametrize(
    "numstates",
    [
        (("section1", "numerical", 10), ("section2", "numerical", 12)),
        (("section1", "numerical", 10), ("section2", "numerical", 0)),
        (("section1", "numerical", -1), ("section2", "numerical", 123)),
    ],
)
def test_num_options(dlg: PreferencesDialog, numstates):
    for section_name, option_name, value in numstates:
        dlg.model.setValue(section_name, option_name, value)

    for section_name, option_name, value in numstates:
        assert dlg.options2widgets[(section_name, option_name)].value() == value


def test_reset_to_defaults(dlg: PreferencesDialog):
    dlg.options2widgets[("section1", "stringy")].setText("changed!")
    dlg.options2widgets[("section2", "booly")].setChecked(True)

    assert dlg.model.getValue("section1", "stringy") == "changed!"
    assert dlg.model.getValue("section2", "booly")

    dlg.resetButton.click()

    assert dlg.model.getValue("section1", "stringy") == "section1-test-text"
    assert not dlg.model.getValue("section2", "booly")


def test_save_defaults(patch_config: Path, dlg: PreferencesDialog):
    dlg.model.saveConfig()
    assert patch_config.exists()
    assert patch_config.read_text() == ""


def test_save_only_changed_values(patch_config: Path, dlg: PreferencesDialog):
    dlg.options2widgets[("section1", "stringy")].setText("changed!")
    dlg.options2widgets[("section2", "numerical")].setValue(42)
    dlg.model.saveConfig()
    assert patch_config.exists()
    assert patch_config.read_text() == "[section1]\nstringy = changed!\n\n[section2]\nnumerical = 42\n\n"


def test_show_hide_advanced_opts(dlg: PreferencesDialog):
    assert not dlg.options2widgets["section2", "bool_advanced"].isVisible()
    dlg._adv_checkbox.setChecked(True)
    assert dlg.options2widgets["section2", "bool_advanced"].isVisible()
