# Data selection is already covered in workflow tests (e.g. testPixelClassificationGui.py)
# Additional tests here should be workflow-agnostic.
import os
from unittest import mock

import pytest
from qtpy.QtGui import QStandardItemModel, QStandardItem
from qtpy.QtWidgets import QComboBox, QMessageBox

from ilastik.applets.dataSelection.datasetDetailedInfoTableModel import DatasetColumn
from ilastik.applets.dataSelection.datasetDetailedInfoTableView import DatasetDetailedInfoTableView

CI = os.environ.get("GITHUB_ACTIONS") or os.environ.get("APPVEYOR") or os.environ.get("ON_CIRCLE_CI")


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
        m.get_scale_options = lambda _row: {"100_100_10": "100, 100, 10", "50_50_10": "50, 50, 10"} if _row > 0 else {}
        m.is_scale_locked = lambda _row: _row == 2
        data_rows = [
            ["image", "/usr/root/image.png", "", "z: 1, y: 10, x: 10", "", ""],
            ["image", "precomputed://http://localhost:8000", "", "z: 1, y: 10, x: 10", "100, 100, 10", ""],
            ["image", "precomputed://http://localhost:8000", "", "z: 1, y: 10, x: 10", "50, 50, 10", ""],
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


def test_locked_scale_select_does_not_trigger_gui_and_informs_user(
    qtbot, dataset_table, mock_gui, intercept_info_popup
):
    dataset_table.scaleSelected.connect(mock_gui.handleScaleSelected)
    scale_cell_multiscale_locked = dataset_table.model().index(2, DatasetColumn.Scale)
    # Wait needed on Mac to avoid `combobox is None` race condition
    qtbot.waitUntil(lambda: dataset_table.indexWidget(scale_cell_multiscale_locked) is not None, timeout=1500)
    combobox = dataset_table.indexWidget(scale_cell_multiscale_locked)
    index_changed_mock = mock.Mock()
    combobox.currentIndexChanged.connect(index_changed_mock)

    combobox.setCurrentIndex(0)
    if not CI:  # Popups are off in CI
        intercept_info_popup.assert_called_once()
    assert 1 == index_changed_mock.call_count
    assert 0 == mock_gui.handleScaleSelected.call_count
