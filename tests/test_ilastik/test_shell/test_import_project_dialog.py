from pathlib import Path
from unittest.mock import patch

import h5py
import pytest
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QApplication

from ilastik.shell.gui.importProjectDialog import ImportProjectDialog


@pytest.fixture
def workflow_list() -> list[str]:
    return ["workflow 1", "workflow 2"]


@pytest.fixture
def base_path(tmp_path: Path) -> Path:
    p = tmp_path / "base_path"
    p.mkdir()
    return p


@pytest.fixture
def valid_ilp(base_path: Path) -> Path:
    fout = base_path / "valid_ilp.ilp"
    with h5py.File(fout, "w") as f:
        f.create_dataset("workflowName", data=b"Pixel Classification")
    return fout


@pytest.fixture
def invalid_ilp(base_path: Path) -> Path:
    fout = base_path / "invalid_ilp.ilp"
    with h5py.File(fout, "w") as f:
        f.create_dataset("some_other_h5", data=b"blah")
    return fout


@pytest.fixture
def dialog(qtbot, workflow_list: list[str], base_path: Path):
    dlg = ImportProjectDialog(workflow_list=workflow_list, base_path=base_path)
    qtbot.addWidget(dlg)
    dlg.show()
    qtbot.waitExposed(dlg)
    return dlg


def test_construct(qtbot, workflow_list: list[str], base_path: Path):
    dlg = ImportProjectDialog(workflow_list=workflow_list, base_path=base_path)
    qtbot.addWidget(dlg)

    assert not dlg.isVisible()


def test_initial_state(dialog: ImportProjectDialog):
    assert dialog.src_edit.text() == ""
    assert dialog.dst_edit.text() == ""
    assert not dialog.combo.isEnabled()
    assert not dialog.ok_button.isEnabled()


@patch("qtpy.QtWidgets.QFileDialog.getOpenFileName", new=lambda *_, **__: ("test.ilp", None))
def test_add_src_button(qtbot, dialog: ImportProjectDialog):
    qtbot.mouseClick(dialog.src_button, Qt.MouseButton.LeftButton)
    assert dialog.src_edit.text() == "test.ilp"


@patch("qtpy.QtWidgets.QFileDialog.getOpenFileName", new=lambda *_, **__: ("", None))
def test_add_src_button_cancel(qtbot, dialog: ImportProjectDialog):
    dialog.src_edit.setText("some_file.ilp")
    qtbot.mouseClick(dialog.src_button, Qt.MouseButton.LeftButton)
    assert dialog.src_edit.text() == "some_file.ilp"


@patch("qtpy.QtWidgets.QFileDialog.getSaveFileName", new=lambda *_, directory, **__: (directory, None))
def test_add_dst_button_empty_src(qtbot, dialog: ImportProjectDialog, base_path: Path):
    qtbot.mouseClick(dialog.dst_button, Qt.MouseButton.LeftButton)
    assert dialog.dst_edit.text() == str(base_path / "imported.ilp")


@patch("qtpy.QtWidgets.QFileDialog.getSaveFileName", new=lambda *_, directory, **__: (directory, None))
def test_add_dst_button_with_src(qtbot, dialog: ImportProjectDialog, base_path: Path):
    dialog.src_edit.setText(str(base_path / "inner" / "some_file.ilp"))
    qtbot.mouseClick(dialog.dst_button, Qt.MouseButton.LeftButton)
    assert dialog.dst_edit.text() == str(base_path / "inner" / "some_file_imported.ilp")


@patch("qtpy.QtWidgets.QFileDialog.getSaveFileName", new=lambda *_, **__: (None, None))
def test_add_dst_button_cancel(qtbot, dialog: ImportProjectDialog):
    dialog.dst_edit.setText("test.ilp")
    qtbot.mouseClick(dialog.dst_button, Qt.MouseButton.LeftButton)
    assert dialog.dst_edit.text() == "test.ilp"


def test_valid_src(dialog: ImportProjectDialog, valid_ilp: Path):
    dialog.src_edit.setText(str(valid_ilp))
    assert dialog.src_hint_label.text() == ImportProjectDialog.Messages.IMPORTING_TO.format(
        workflow_name="Pixel Classification"
    )


@pytest.mark.parametrize("fname", ["some_file_pretending_to_be.ilp", "not_ilp.txt"])
def test_invalid_src_no_h5(dialog: ImportProjectDialog, base_path: Path, fname: str):
    ilp = base_path / fname
    ilp.touch()
    dialog.src_edit.setText(str(ilp))
    assert dialog.src_hint_label.text() == ImportProjectDialog.Messages.INVALID_SRC_ILP


def test_invalid_src_h5(dialog: ImportProjectDialog, invalid_ilp: Path):
    dialog.src_edit.setText(str(invalid_ilp))
    assert dialog.src_hint_label.text() == ImportProjectDialog.Messages.INVALID_SRC_ILP


@pytest.mark.parametrize("fname", ["some-file-no-ext", "not_ilp.txt"])
def test_invalid_dst(dialog: ImportProjectDialog, base_path: Path, fname: str):
    ilp = base_path / fname
    dialog.dst_edit.setText(str(ilp))
    assert dialog.dst_hint_label.text() == ImportProjectDialog.Messages.INVALID_DEST_NAME


def test_same_src_and_dest(dialog: ImportProjectDialog, valid_ilp: Path):
    dialog.src_edit.setText(str(valid_ilp))
    dialog.dst_edit.setText(str(valid_ilp))
    assert dialog.dst_hint_label.text() == ImportProjectDialog.Messages.SRC_DEST_EQ


def test_get_values(dialog: ImportProjectDialog, base_path: Path, valid_ilp: Path):
    dialog.src_edit.setText(str(valid_ilp))
    dialog.dst_edit.setText(str(base_path / "good_import.ilp"))
    dialog.combo.setCurrentIndex(2)

    src_path, dst_path, workflow_name = dialog.get_values()
    assert src_path == valid_ilp
    assert dst_path == base_path / "good_import.ilp"
    assert workflow_name == "workflow 2"
