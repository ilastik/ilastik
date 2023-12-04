# Data selection is already covered in workflow tests (e.g. testPixelClassificationGui.py)
# Additional tests here should be workflow-agnostic.
from unittest import mock

import pytest
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QComboBox

from ilastik.applets.dataSelection.datasetDetailedInfoTableModel import DatasetColumn
from ilastik.applets.dataSelection.datasetDetailedInfoTableView import DatasetDetailedInfoTableView


def prepare_widget(qtbot, widget):
    qtbot.addWidget(widget)
    widget.show()
    qtbot.waitExposed(widget)
    return widget


@pytest.fixture
def dataset_table(qtbot) -> DatasetDetailedInfoTableView:
    def mock_DatasetDetailedInfoTableModel():
        empty_model = QStandardItemModel()
        empty_model.isEmptyRow = lambda _row: False
        empty_model.get_scale_options = lambda _row: ["100, 100, 10", "50, 50, 10"] if _row == 1 else []
        return empty_model

    data_rows = [
        ["image", "/usr/root/image.png", "", "zyx", "(1,10,10)", "", ""],
        ["image", "precomputed://http://localhost:8000", "", "zyx", "(1,10,10)", "", "100, 100, 10"],
    ]

    table_view = DatasetDetailedInfoTableView(None)
    model = mock_DatasetDetailedInfoTableModel()
    for i, row in enumerate(data_rows):
        model.insertRow(i, [QStandardItem(d) for d in row])
    table_view.setModel(model)
    return prepare_widget(qtbot, table_view)


def test_scale_select_dropdown(dataset_table):
    dataSelectionGui = mock.Mock()
    dataSelectionGui.handleScaleSelected = mock.Mock()
    dataset_table.scaleSelected.connect(dataSelectionGui.handleScaleSelected)
    scale_cell_single_scale = dataset_table.model().index(0, DatasetColumn.Scale)
    scale_cell_multiscale = dataset_table.model().index(1, DatasetColumn.Scale)

    # Would have liked to assert that `paint`ing DatasetDetailedInfoTableView triggers the editor
    # for multiscale rows, i.e. user interaction not necessary.
    # But couldn't get qtbot to actually paint ¯\_(ツ)_/¯
    dataset_table.edit(scale_cell_single_scale)  # Pretend-click the table cell instead
    dataset_table.edit(scale_cell_multiscale)

    assert not dataset_table.isPersistentEditorOpen(scale_cell_single_scale)
    assert dataset_table.isPersistentEditorOpen(scale_cell_multiscale)

    editor = dataset_table.indexWidget(scale_cell_multiscale)
    assert isinstance(editor, QComboBox)
    assert editor.count() == 2

    editor.setCurrentIndex(1)
    assert dataSelectionGui.handleScaleSelected.called_once_with(1, 1)
