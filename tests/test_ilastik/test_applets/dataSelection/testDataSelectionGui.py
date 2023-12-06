# Data selection is already covered in workflow tests (e.g. testPixelClassificationGui.py)
# Additional tests here should be workflow-agnostic.
from unittest import mock

import pytest
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QComboBox, QMessageBox

from ilastik.applets.dataSelection.datasetDetailedInfoTableModel import DatasetColumn
from ilastik.applets.dataSelection.datasetDetailedInfoTableView import DatasetDetailedInfoTableView


def prepare_widget(qtbot, widget):
    qtbot.addWidget(widget)
    widget.show()
    qtbot.waitExposed(widget)
    return widget


@pytest.fixture
def intercept_info_popup(monkeypatch):
    info_mock = mock.Mock()
    monkeypatch.setattr(QMessageBox, "information", lambda *args: info_mock(*args))
    return info_mock


@pytest.fixture
def dataset_table(qtbot) -> DatasetDetailedInfoTableView:
    def mock_DatasetDetailedInfoTableModel():
        m = QStandardItemModel()
        m.isEmptyRow = lambda _row: False
        m.get_scale_options = lambda _row: ["100, 100, 10", "50, 50, 10"] if _row > 0 else []
        m.is_scale_locked = lambda _row: _row == 2
        data_rows = [
            ["image", "/usr/root/image.png", "", "zyx", "(1,10,10)", "", ""],
            ["image", "precomputed://http://localhost:8000", "", "zyx", "(1,10,10)", "100, 100, 10", ""],
            ["image", "precomputed://http://localhost:8000", "", "zyx", "(1,10,10)", "50, 50, 10", ""],
            [],  # Empty row because the custom setModel replaces the model's last row with an AddFileButton
        ]
        for i, row in enumerate(data_rows):
            m.insertRow(i, [QStandardItem(d) for d in row])
        return m

    table_view = DatasetDetailedInfoTableView(None)
    model = mock_DatasetDetailedInfoTableModel()
    table_view.setModel(model)
    # Make sure qtbot window is big enough to `paint` also the Scale column
    table_view.resize(1200, 300)
    return prepare_widget(qtbot, table_view)


@pytest.fixture
def mock_gui():
    dataSelectionGui = mock.Mock()
    dataSelectionGui.handleScaleSelected = mock.Mock()
    return dataSelectionGui


def test_scale_select_exists_and_triggers_gui_event(dataset_table, mock_gui):
    dataset_table.scaleSelected.connect(mock_gui.handleScaleSelected)
    scale_cell_single_scale = dataset_table.model().index(0, DatasetColumn.Scale)
    scale_cell_multiscale = dataset_table.model().index(1, DatasetColumn.Scale)

    assert not dataset_table.isPersistentEditorOpen(scale_cell_single_scale)
    assert dataset_table.isPersistentEditorOpen(scale_cell_multiscale)

    editor = dataset_table.indexWidget(scale_cell_multiscale)
    assert isinstance(editor, QComboBox)
    assert editor.count() == 2

    editor.setCurrentIndex(1)
    assert mock_gui.handleScaleSelected.called_once_with(1, 1)


def test_locked_scale_select_does_not_trigger_gui_and_informs_user(dataset_table, mock_gui, intercept_info_popup):
    dataset_table.scaleSelected.connect(mock_gui.handleScaleSelected)
    scale_cell_multiscale_locked = dataset_table.model().index(2, DatasetColumn.Scale)
    editor_locked = dataset_table.indexWidget(scale_cell_multiscale_locked)

    editor_locked.setCurrentIndex(0)
    intercept_info_popup.assert_called_once()
    assert 0 == mock_gui.handleScaleSelected.call_count
