# Data selection is already covered in workflow tests (e.g. testPixelClassificationGui.py)
# Additional tests here should be workflow-agnostic.
import os
from collections import namedtuple
import platform
from typing import Tuple, List
from unittest import mock

import numpy
import pytest
import vigra
from qtpy.QtGui import QStandardItemModel, QStandardItem
from qtpy.QtWidgets import QComboBox, QMessageBox

from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.dataSelection.datasetDetailedInfoTableModel import DatasetColumn
from ilastik.applets.dataSelection.datasetDetailedInfoTableView import DatasetDetailedInfoTableView
from ilastik.applets.dataSelection.opDataSelection import MultiscaleUrlDatasetInfo
from lazyflow.operator import Operator
from lazyflow.operators.opArrayPiper import OpArrayPiper

CI = os.environ.get("GITHUB_ACTIONS") or os.environ.get("APPVEYOR") or os.environ.get("ON_CIRCLE_CI")
MAC = platform.system().lower() == "darwin"


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
        m.get_common_scale_option_indices = lambda _row: [0, 1] if _row > 0 else []
        m.is_scale_locked = lambda _row: _row == 2
        data_row_t = namedtuple(
            "data_row_t", ("nickname", "location", "internalID", "taggedShape", "pixelSize", "scale", "range")
        )
        data_rows = [
            data_row_t(
                nickname="image",
                location="/usr/root/image.png",
                internalID="",
                taggedShape="z: 1, y: 10, x: 10",
                pixelSize="",
                scale="",
                range="",
            ),
            data_row_t(
                nickname="image",
                location="precomputed://http://localhost:8000",
                internalID="",
                taggedShape="z: 1, y: 10, x: 10",
                pixelSize="",
                scale="100, 100, 10",
                range="",
            ),
            data_row_t(
                nickname="image",
                location="precomputed://http://localhost:8000",
                internalID="",
                taggedShape="z: 1, y: 10, x: 10",
                pixelSize="",
                scale="50, 50, 10",
                range="",
            ),
            data_row_t(
                nickname="", location="", internalID="", taggedShape="", pixelSize="", scale="", range=""
            ),  # Empty row because the custom setModel replaces the model's last row with an AddFileButton
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
    mock_gui.handleScaleSelected.assert_called_once_with(1, "50_50_10")


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


@pytest.fixture(
    params=[  # Cases "scales in this role - scales in other role"
        "multi-single",
        "multifewer-multimore",
        "multimore-multifewer",
    ]
)
def mismatching_model(request) -> Tuple[QStandardItemModel, List[int], List[int]]:
    m = QStandardItemModel()  # mock DatasetDetailedInfoTableModel
    m.isEmptyRow = lambda _row: False
    scale_options = {  # Scale options of the currently viewed ("this") role
        "multi-single": {"0": "100, 100, 10", "1": "50, 50, 10"},
        "multifewer-multimore": {"0": "100, 100, 10", "1": "50, 50, 10"},
        "multimore-multifewer": {"0": "100, 100, 10", "1": "50, 50, 10", "2": "25, 25, 10"},
    }
    enabled_option_indices = {  # Which of the options match across all roles
        "multi-single": [0],  # Another role has a single image that matches the first scale
        "multifewer-multimore": [0, 1],  # Another role has a multiscale; current one's scales all have a match
        "multimore-multifewer": [0, 1],  # Another role has a multiscale; one of current's scales not present
    }
    disabled_option_indices = {  # Which of the options don't have a match in other roles
        "multi-single": [1],
        "multifewer-multimore": [],
        "multimore-multifewer": [2],
    }
    m.get_scale_options = lambda _row: scale_options[request.param]
    m.get_common_scale_option_indices = lambda _row: enabled_option_indices[request.param]
    m.is_scale_locked = lambda _row: False
    data_rows = [
        ["image", "precomputed://http://localhost:8000", "", "z: 1, y: 10, x: 10", "100, 100, 10", ""],
        [],  # Empty row because the custom setModel replaces the model's last row with an AddFileButton
    ]
    for i, row in enumerate(data_rows):
        m.insertRow(i, [QStandardItem(d) for d in row])
    return m, enabled_option_indices[request.param], disabled_option_indices[request.param]


@pytest.fixture
def dataset_table_with_mismatching_roles(
    qtbot, mismatching_model
) -> Tuple[DatasetDetailedInfoTableView, List[int], List[int]]:
    model, enabled, disabled = mismatching_model
    table_view = DatasetDetailedInfoTableView(None)
    table_view.setModel(model)
    # Make sure qtbot window is big enough to `paint` also the Scale column
    table_view.resize(1200, 300)
    return prepare_widget(qtbot, table_view), enabled, disabled


@pytest.mark.skipif(CI and MAC, reason="flaky assert table.isPersistentEditorOpen(scale_cell)")
def test_scale_select_disables_scale_options_not_available_in_other_roles(
    dataset_table_with_mismatching_roles: Tuple[DatasetDetailedInfoTableView, List[int], List[int]],
    mock_gui: mock.Mock,
    intercept_info_popup: mock.Mock,
):
    table, enabled_options, disabled_options = dataset_table_with_mismatching_roles
    table.scaleSelected.connect(mock_gui.handleScaleSelected)
    lane = 0
    num_options = len(table.model().get_scale_options(lane))
    assert enabled_options + disabled_options == list(range(num_options)), "you broke the test setup :)"
    scale_cell = table.model().index(lane, DatasetColumn.Scale)
    assert table.isPersistentEditorOpen(scale_cell)

    editor = table.indexWidget(scale_cell)
    assert isinstance(editor, QComboBox)
    assert editor.count() == num_options

    for disabled in disabled_options:
        editor.setCurrentIndex(disabled)
        if not CI:  # Popups are off in CI
            intercept_info_popup.assert_called_once()
        mock_gui.handleScaleSelected.assert_not_called(), f"scale option index {disabled} was supposed to be unavailable"

    for enabled in enabled_options:
        idx_before = editor.currentIndex()
        editor.setCurrentIndex(enabled)
        # callbacks are only called if index changes
        if idx_before != enabled:
            assert mock_gui.handleScaleSelected.call_args.args == (
                lane,
                str(enabled),
            ), f"scale option index {enabled} was supposed to be available"


@pytest.fixture
def data_selection_applet(tmp_path, graph):
    workflow = Operator(graph=graph)
    workflow.shell = mock.Mock()
    workflow.handleNewLanesAdded = mock.Mock()

    applet = DataSelectionApplet(workflow, "Input Data", "Input Data")
    applet.topLevelOperator.DatasetRoles.setValue(["Raw Data"])
    applet.topLevelOperator.WorkingDirectory.setValue(tmp_path)
    return applet


def test_add_files_adds_ome_zarr_as_multiscale_dataset(monkeypatch, graph, tmp_path, data_selection_applet):
    ome_zarr_path = tmp_path / "test.ome.zarr"
    ome_zarr_path.mkdir()
    truthy_mock_scales = {"scale_key": object()}

    def make_piper(*_args, parent=None, local_graph=graph, **_kwargs):
        reader = OpArrayPiper(parent=parent, graph=local_graph)
        reader.Input.setValue(numpy.zeros((3, 25, 25)))
        reader.Output.meta.axistags = vigra.defaultAxistags("zyx")
        reader.Output.meta.scales = truthy_mock_scales
        return reader

    monkeypatch.setattr("ilastik.applets.dataSelection.opDataSelection.OpInputDataReader", make_piper)
    monkeypatch.setattr(QMessageBox, "critical", lambda *args: None)

    monkeypatch.setattr(
        "ilastik.applets.dataSelection.dataSelectionGui.ImageFileDialog.getSelectedPaths",
        mock.Mock(return_value=[ome_zarr_path]),
    )

    gui = data_selection_applet.getMultiLaneGui()
    gui.addFiles(roleIndex=0)
    assert data_selection_applet.num_lanes == 1, "test setup failed - did not load dataset"

    dataset_info = data_selection_applet.get_lane(0).get_dataset_info("Raw Data")

    assert isinstance(dataset_info, MultiscaleUrlDatasetInfo), "datasets that load .scales should reroute to multiscale"
    assert dataset_info.scales == truthy_mock_scales
