###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2026, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#          http://ilastik.org/license.html
###############################################################################
from contextlib import nullcontext as does_not_raise
from functools import partial
from types import SimpleNamespace
from unittest.mock import patch

import numpy
import pytest
import vigra
from qtpy.QtCore import QPoint, QTimer, Qt
from qtpy.QtGui import QContextMenuEvent
from qtpy.QtWidgets import QApplication, QMenu, QUndoStack

from ilastik.applets.objectClassification.objectClassificationGui import ObjectClassificationGui
from ilastik.applets.objectClassification.objectLabelExplorer import ObjectLabelExplorerWidget
from ilastik.applets.objectExtraction.opObjectExtraction import default_features_key, OpAdaptTimeListRoi
from lazyflow.graph import InputSlot, Operator
from lazyflow.operators.opArrayPiper import OpArrayPiper
from lazyflow.rtype import List
from lazyflow.stype import Opaque


class OpObjectLabelStore(Operator):
    """Holds object labels in a slot of the same type as object classification's LabelInputs"""

    Labels = InputSlot(stype=Opaque, rtype=List)

    def setupOutputs(self):
        pass

    def propagateDirty(self, slot, subindex, roi):
        pass


@pytest.fixture
def label_op(graph) -> OpArrayPiper:
    labels = {0: numpy.array([0.0, 0.0, 0.0])}
    op_annotations = OpArrayPiper(graph=graph)
    op_annotations.Input.setValue(labels)
    return op_annotations


@pytest.fixture
def feature_op_2d(graph) -> OpAdaptTimeListRoi:
    features = numpy.array(
        [{default_features_key: {"RegionCenter": numpy.array([[0.0, 0.0], [1.0, 2.0], [3.0, 4.0]])}}]
    )
    op_features = OpArrayPiper(graph=graph)
    op_features.Input.setValue(vigra.taggedView(features, axistags="t"))
    op_features_adapt = OpAdaptTimeListRoi(graph=graph)
    op_features_adapt.Input.connect(op_features.Output)
    return op_features_adapt


@pytest.fixture
def feature_op_3d(graph) -> OpAdaptTimeListRoi:
    features = numpy.array(
        [{default_features_key: {"RegionCenter": numpy.array([[0.0, 0.0, 0.0], [1.0, 2.0, 3.0], [6.0, 5.0, 4.0]])}}]
    )
    op_features = OpArrayPiper(graph=graph)
    op_features.Input.setValue(vigra.taggedView(features, axistags="t"))
    op_features_adapt = OpAdaptTimeListRoi(graph=graph)
    op_features_adapt.Input.connect(op_features.Output)
    return op_features_adapt


@pytest.fixture
def label_explorer_2d(qtbot, label_op: OpArrayPiper, feature_op_2d: OpAdaptTimeListRoi) -> ObjectLabelExplorerWidget:
    ex = ObjectLabelExplorerWidget(features_slot=feature_op_2d.Output, label_slot=label_op.Output, axiskeys=["y", "x"])
    qtbot.addWidget(ex)
    return ex


@pytest.fixture
def label_explorer_3d(qtbot, label_op: OpArrayPiper, feature_op_3d: OpAdaptTimeListRoi) -> ObjectLabelExplorerWidget:
    ex = ObjectLabelExplorerWidget(
        features_slot=feature_op_3d.Output, label_slot=label_op.Output, axiskeys=["z", "y", "x"]
    )
    qtbot.addWidget(ex)
    return ex


@pytest.mark.parametrize(
    "gui_variant",
    [
        pytest.param("label_explorer_2d", id="2d"),
        pytest.param("label_explorer_3d", id="3d"),
    ],
)
class TestObjectLabelExplorer:
    def test_construct(self, qtbot, gui_variant, request):
        label_explorer = request.getfixturevalue(gui_variant)
        with patch.object(
            label_explorer, "initialize_table", wraps=label_explorer.initialize_table
        ) as wrapped_initialize_table:
            label_explorer.show()
            qtbot.waitExposed(label_explorer)
            assert label_explorer.tableWidget.rowCount() == 0
            wrapped_initialize_table.assert_called_once()

    def test_update_on_update(
        self,
        qtbot,
        gui_variant,
        label_op: OpArrayPiper,
        request,
    ):
        label_explorer = request.getfixturevalue(gui_variant)
        with patch.object(
            label_explorer, "initialize_table", wraps=label_explorer.initialize_table
        ) as wrapped_initialize_table:
            label_explorer.show()
            qtbot.waitExposed(label_explorer)
            assert label_explorer.tableWidget.rowCount() == 0

            label_op.Input.setValue({0: numpy.array([0.0, 1.0])})
            wrapped_initialize_table.assert_called_once()
            assert label_explorer.tableWidget.rowCount() == 1

    def test_no_update_on_update_when_not_shown(
        self,
        qtbot,
        gui_variant,
        label_op: OpArrayPiper,
        request,
    ):
        label_explorer = request.getfixturevalue(gui_variant)
        with patch.object(
            label_explorer, "_populate_table", wraps=label_explorer._populate_table
        ) as wrapped_populate_table:
            label_op.Input.setValue({0: numpy.array([0.0, 1.0, 2.0])})
            wrapped_populate_table.assert_not_called()

            label_explorer.show()
            qtbot.waitExposed(label_explorer)
            wrapped_populate_table.assert_called_once()
            assert label_explorer.tableWidget.rowCount() == 2

    def test_delete_labels_empty_table_blocked(
        self,
        qtbot,
        gui_variant,
        label_op: OpArrayPiper,
        request,
    ):
        label_explorer = request.getfixturevalue(gui_variant)
        with patch.object(
            label_explorer, "_populate_table", wraps=label_explorer._populate_table
        ) as wrapped_populate_table:
            assert wrapped_populate_table.call_count == 0
            label_explorer.show()
            qtbot.waitExposed(label_explorer)
            assert wrapped_populate_table.call_count == 1
            label_op.Input.setValue({0: numpy.array([0.0, 1.0])})
            # Update while shown
            assert label_explorer.tableWidget.rowCount() == 1

            label_op.Input.setValue({0: numpy.array([0.0, 1.0, 2.0])})
            # Update while shown
            assert label_explorer.tableWidget.rowCount() == 2
            assert wrapped_populate_table.call_count == 3

            # remove one annotation
            label_op.Input.setValue({0: numpy.array([0.0, 1.0])})
            assert label_explorer.tableWidget.rowCount() == 1
            assert wrapped_populate_table.call_count == 4

            # remove the last annotations
            label_op.Input.setValue({0: numpy.array([0.0, 0.0])})
            assert label_explorer.tableWidget.rowCount() == 0
            assert wrapped_populate_table.call_count == 5


@pytest.mark.parametrize(
    "gui_variant, expected_positions",
    [
        pytest.param(
            "label_explorer_2d",
            [{"t": 0.0, "x": 3.0, "y": 4.0, "z": 0.0}, {"t": 0.0, "x": 1.0, "y": 2.0, "z": 0.0}],
            id="2d",
        ),
        pytest.param(
            "label_explorer_3d",
            [{"t": 0.0, "x": 6.0, "y": 5.0, "z": 4.0}, {"t": 0.0, "x": 1.0, "y": 2.0, "z": 3.0}],
            id="3d",
        ),
    ],
)
def test_sync_position(
    qtbot,
    gui_variant,
    expected_positions,
    label_op: OpArrayPiper,
    request,
):
    label_explorer = request.getfixturevalue(gui_variant)
    positions = []
    label_explorer.positionRequested.connect(positions.append)
    label_explorer.show()
    qtbot.waitExposed(label_explorer)

    label_op.Input.setValue({0: numpy.array([0.0, 1.0, 2.0])})

    assert positions == []
    assert label_explorer.tableWidget.rowCount() == 2

    label_explorer.tableWidget.selectRow(1)
    assert positions == expected_positions[0:1]

    label_explorer.tableWidget.selectRow(0)
    assert positions == expected_positions


@pytest.mark.parametrize(
    "center_dimensions, expectation",
    [
        (1, pytest.raises(ValueError)),
        (2, does_not_raise()),
        (3, does_not_raise()),
        (4, pytest.raises(ValueError)),
        (5, pytest.raises(ValueError)),
    ],
)
def test_populate_raises_for_unexpected_object_center_dimension(
    qtbot, graph, center_dimensions, expectation, label_op: OpArrayPiper
):
    n_centers = 42
    region_centers = numpy.random.randint(0, 2**32, (n_centers, center_dimensions), dtype="uint64").astype("float64")
    features = numpy.array([{"Default features": {"RegionCenter": region_centers}}])
    op_features = OpArrayPiper(graph=graph)
    op_features.Input.setValue(vigra.taggedView(features, axistags="t"))
    op_features_adapt = OpAdaptTimeListRoi(graph=graph)
    op_features_adapt.Input.connect(op_features.Output)
    label_explorer = ObjectLabelExplorerWidget(
        features_slot=op_features.Output, label_slot=label_op.Output, axiskeys="xyztc"[0:center_dimensions]
    )
    qtbot.addWidget(label_explorer)

    label_explorer.show()
    qtbot.waitExposed(label_explorer)
    with expectation:
        label_op.Input.setValue({0: numpy.array([0.0, 1.0, 2.0])})


@pytest.mark.parametrize("feature_variant", ["feature_op_2d", "feature_op_3d"])
def test_delete_selected_objects_undo_redo(qtbot, request, feature_variant, graph):
    store = OpObjectLabelStore(graph=graph)
    features = request.getfixturevalue(feature_variant)
    explorer = ObjectLabelExplorerWidget(features.Output, store.Labels, axiskeys=["x", "y"])
    qtbot.addWidget(explorer)
    store.Labels.setValue({0: numpy.array([0.0, 1.0, 1.0])})
    explorer.show()
    qtbot.waitExposed(explorer)
    stack = QUndoStack(explorer)
    gui = SimpleNamespace(_undoStack=stack, op=SimpleNamespace(LabelInputs=store.Labels))
    explorer.deleteRequested.connect(partial(ObjectClassificationGui._delete_explorer_annotations, gui))
    explorer.tableWidget.sortItems(0, Qt.DescendingOrder)
    # The object center need not be inside the object; use the stored object ID.
    selected = explorer.tableWidget.item(0, 0).data(Qt.UserRole + 1).identifier[1]
    explorer.tableWidget.selectRow(0)
    explorer._delete_selected()
    expected = numpy.array([0.0, 1.0, 1.0])
    expected[selected] = 0
    numpy.testing.assert_array_equal(store.Labels.value[0], expected)
    assert explorer.tableWidget.rowCount() == 1
    stack.undo()
    numpy.testing.assert_array_equal(store.Labels.value[0], [0, 1, 1])
    stack.redo()
    numpy.testing.assert_array_equal(store.Labels.value[0], expected)
    stack.undo()
    explorer.tableWidget.selectAll()
    explorer._delete_selected()
    numpy.testing.assert_array_equal(store.Labels.value[0], [0, 0, 0])
    assert explorer.tableWidget.rowCount() == 0
    stack.undo()
    numpy.testing.assert_array_equal(store.Labels.value[0], [0, 1, 1])
    explorer.cleanup()


@pytest.mark.parametrize("gui_variant", ["label_explorer_2d", "label_explorer_3d"])
@pytest.mark.parametrize("selected_row", [True, False], ids=["keep-selection", "select-clicked-row"])
@pytest.mark.parametrize("delete", [True, False], ids=["delete", "cancel"])
def test_context_menu_delete(qtbot, request, label_op, gui_variant, selected_row, delete):
    explorer = request.getfixturevalue(gui_variant)
    label_op.Input.setValue({0: numpy.array([0.0, 1.0, 2.0])})
    explorer.show()
    qtbot.waitExposed(explorer)
    table = explorer.tableWidget
    table.sortItems(0, Qt.DescendingOrder)
    if selected_row:
        table.selectAll()
    else:
        table.selectRow(0)
    expected = [table.item(row, 0).data(Qt.UserRole + 1) for row in (range(table.rowCount()) if selected_row else [1])]
    requests = []
    explorer.deleteRequested.connect(requests.append)

    global_position = QPoint(250, 200)

    def handle_menu():
        menu = QApplication.activePopupWidget()
        try:
            assert isinstance(menu, QMenu)
            assert menu.pos() == global_position
            # A window manager may center the popup after mapping it.
            menu.move(global_position + QPoint(100, 100))
            assert menu.pos() == global_position
            assert [action.text() for action in menu.actions()] == ["Delete selected annotations"]
            if delete:
                menu.actions()[0].trigger()
        finally:
            if menu is not None:
                menu.close()

    QTimer.singleShot(0, handle_menu)
    position = table.visualItemRect(table.item(1, 0)).center()
    # The event's screen coordinate is authoritative; do not recalculate it
    # from widget geometry, which may change while selecting/navigating a row.
    event = QContextMenuEvent(QContextMenuEvent.Mouse, position, global_position)
    QApplication.sendEvent(table.viewport(), event)
    assert requests == ([expected] if delete else [])
    assert {index.row() for index in table.selectionModel().selectedRows()} == ({0, 1} if selected_row else {1})
    explorer.cleanup()


@pytest.mark.parametrize("gui_variant", ["label_explorer_2d", "label_explorer_3d"])
def test_context_menu_ignores_empty_space(qtbot, request, label_op, gui_variant):
    explorer = request.getfixturevalue(gui_variant)
    label_op.Input.setValue({0: numpy.array([0.0, 1.0])})
    explorer.show()
    qtbot.waitExposed(explorer)
    table = explorer.tableWidget
    table.selectRow(0)
    position = QPoint(5, table.viewport().height() - 1)
    assert table.itemAt(position) is None
    with patch("ilastik.widgets.labelExplorer.QMenu") as menu:
        event = QContextMenuEvent(QContextMenuEvent.Mouse, position, table.viewport().mapToGlobal(position))
        QApplication.sendEvent(table.viewport(), event)
        menu.assert_not_called()
    assert {index.row() for index in table.selectionModel().selectedRows()} == {0}
    explorer.cleanup()


@pytest.mark.parametrize("gui_variant", ["label_explorer_2d", "label_explorer_3d"])
def test_context_menu_stays_on_screen(qtbot, request, label_op, gui_variant):
    explorer = request.getfixturevalue(gui_variant)
    label_op.Input.setValue({0: numpy.array([0.0, 1.0])})
    explorer.show()
    qtbot.waitExposed(explorer)
    table = explorer.tableWidget
    available = explorer.screen().availableGeometry()
    global_position = available.bottomRight() - QPoint(1, 1)

    def handle_menu():
        menu = QApplication.activePopupWidget()
        try:
            assert isinstance(menu, QMenu)
            # Popup menus may cover the taskbar on some platforms (e.g. Windows), but not leave the screen.
            assert explorer.screen().geometry().contains(menu.frameGeometry())
            # Qt shifts a menu opened in the screen corner so that it fits; keep that placement.
            placed = menu.pos()
            assert placed != global_position
            menu.move(available.topLeft() - QPoint(50, 50))
            assert menu.pos() == placed
        finally:
            if menu is not None:
                menu.close()

    QTimer.singleShot(0, handle_menu)
    position = table.visualItemRect(table.item(0, 0)).center()
    event = QContextMenuEvent(QContextMenuEvent.Mouse, position, global_position)
    QApplication.sendEvent(table.viewport(), event)
    explorer.cleanup()
