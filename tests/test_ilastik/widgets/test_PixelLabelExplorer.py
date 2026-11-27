###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2025, the ilastik developers
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
from functools import partial
from types import SimpleNamespace
from typing import Iterator, Literal, Tuple
from unittest.mock import patch

import numpy
import pytest
import vigra
from qtpy.QtCore import QItemSelectionModel, Qt
from qtpy.QtWidgets import QUndoStack
from volumina.api import LazyflowSinkSource

from ilastik.applets.labeling.connectBlockedLabels import Neighborhood
from ilastik.applets.labeling.labelingGui import LabelingGui
from ilastik.applets.labeling.pixelLabelExplorer import PixelLabelExplorerWidget
from lazyflow.operators.opArrayPiper import OpArrayPiper
from lazyflow.operators.opCompressedUserLabelArray import OpCompressedUserLabelArray
from lazyflow.operators.opDenseLabelArray import OpDenseLabelArray
from lazyflow.slot import InputSlot
from lazyflow.utility import Pipeline


@pytest.fixture
def label_pipeline_blocked(graph) -> Iterator[OpCompressedUserLabelArray]:
    """
    Label pipeline as found in pixel classification, autocontext, trainable domain adaptation
    """
    data = vigra.taggedView(numpy.zeros((10, 20, 30, 1), dtype="uint8"), axistags="zyxc")

    with Pipeline(graph=graph) as pipe_line:
        pipe_line.add(OpArrayPiper, Input=data)
        label_cache = pipe_line.add(OpCompressedUserLabelArray, blockShape=(5, 5, 5, 1), eraser=0)
        yield label_cache


@pytest.fixture
def label_pipeline_non_blocked(graph) -> Iterator[OpDenseLabelArray]:
    """
    Label pipeline as found in carving
    """
    data = vigra.taggedView(numpy.zeros((10, 20, 30, 1), dtype="uint8"), axistags="zyxc")

    with Pipeline(graph=graph) as pipe_line:
        piper = pipe_line.add(OpArrayPiper, Input=data)
        label_cache = pipe_line.add(OpDenseLabelArray, MetaInput=piper.Output)
        yield label_cache


@pytest.fixture
def label_explorer_blocked(qtbot, label_pipeline_blocked) -> Tuple[InputSlot, PixelLabelExplorerWidget]:
    ex = PixelLabelExplorerWidget(label_pipeline_blocked.nonzeroBlocks, label_pipeline_blocked.Output)
    qtbot.addWidget(ex)
    return label_pipeline_blocked.Input, ex


@pytest.fixture
def label_explorer_non_blocked(
    qtbot, label_pipeline_non_blocked: OpDenseLabelArray
) -> Tuple[InputSlot, PixelLabelExplorerWidget]:
    ex = PixelLabelExplorerWidget(label_pipeline_non_blocked.NonzeroBlocks, label_pipeline_non_blocked.Output)
    qtbot.addWidget(ex)
    return label_pipeline_non_blocked.LabelSinkInput, ex


@pytest.mark.parametrize(
    "gui_variant, expected_neighborhood",
    [
        pytest.param("label_explorer_blocked", Neighborhood.SINGLE, id="blocked"),
        pytest.param("label_explorer_non_blocked", Neighborhood.NONE, id="non-blocked"),
    ],
)
def test_construct(
    qtbot,
    gui_variant: Literal["label_explorer_blocked", "label_explorer_non_blocked"],
    expected_neighborhood: Neighborhood,
    request,
):
    label_explorer: PixelLabelExplorerWidget
    _islot, label_explorer = request.getfixturevalue(gui_variant)
    with patch.object(
        label_explorer, "initialize_table", wraps=label_explorer.initialize_table
    ) as wrapped_initialize_table:

        # widget not shown - should prevent table initialization
        wrapped_initialize_table.assert_not_called()
        label_explorer.show()
        qtbot.waitExposed(label_explorer)
        assert label_explorer._neighborhood == expected_neighborhood
        assert label_explorer._block_cache == {}
        # After being shown, method should be called
        wrapped_initialize_table.assert_called_once()


@pytest.mark.parametrize(
    "gui_variant, expected_n_blocks",
    [
        pytest.param("label_explorer_blocked", 2, id="blocked"),
        pytest.param("label_explorer_non_blocked", 1, id="non-blocked"),
    ],
)
def test_update_on_update(
    qtbot,
    gui_variant: Literal["label_explorer_blocked", "label_explorer_non_blocked"],
    expected_n_blocks: int,
    request,
):
    islot: InputSlot
    label_explorer: PixelLabelExplorerWidget
    islot, label_explorer = request.getfixturevalue(gui_variant)
    with patch.object(
        label_explorer, "initialize_table", wraps=label_explorer.initialize_table
    ) as wrapped_initialize_table:
        label_explorer.show()
        qtbot.waitExposed(label_explorer)
        assert label_explorer._block_cache == {}
        assert label_explorer.tableWidget.rowCount() == 0

        # annotation spans two blocks in the blocked case (blockshape (5, 5, 5, 1))
        islot[0:1, 0:1, 0:7, 0:1] = numpy.ones((1, 1, 7, 1), dtype="uint8")
        assert len(label_explorer._block_cache) == expected_n_blocks
        wrapped_initialize_table.assert_called_once()
        assert label_explorer.tableWidget.rowCount() == 1


@pytest.mark.parametrize(
    "gui_variant, expected_n_blocks",
    [
        pytest.param("label_explorer_blocked", 4, id="blocked"),
        pytest.param("label_explorer_non_blocked", 1, id="non-blocked"),
    ],
)
def test_no_update_on_update_when_not_shown(
    qtbot, gui_variant: Literal["label_explorer_blocked", "label_explorer_non_blocked"], expected_n_blocks: int, request
):
    islot: InputSlot
    label_explorer: PixelLabelExplorerWidget
    islot, label_explorer = request.getfixturevalue(gui_variant)
    with patch.object(
        label_explorer, "_populate_table", wraps=label_explorer._populate_table
    ) as wrapped_populate_table:

        assert label_explorer._block_cache == {}

        # annotation spans 4 blocks in the blocked case (blockshape (5, 5, 5, 1))
        islot[0:1, 5:13, 0:7, 0:1] = numpy.ones((1, 8, 7, 1), dtype="uint8")
        assert label_explorer._block_cache == {}
        wrapped_populate_table.assert_not_called()

        label_explorer.show()
        qtbot.waitExposed(label_explorer)
        assert len(label_explorer._block_cache) == expected_n_blocks
        wrapped_populate_table.assert_called_once()


def test_delete_labels_empty_table_non_blocked(
    qtbot,
    label_pipeline_non_blocked: OpDenseLabelArray,
    label_explorer_non_blocked: Tuple[InputSlot, PixelLabelExplorerWidget],
):
    label_explorer: PixelLabelExplorerWidget
    _islot, label_explorer = label_explorer_non_blocked

    with patch.object(
        label_explorer, "_populate_table", wraps=label_explorer._populate_table
    ) as wrapped_populate_table:
        # annotation spans 4 blocks in the blocked case (blockshape (5, 5, 5, 1))
        label_pipeline_non_blocked.LabelSinkInput[0:1, 5:13, 0:7, 0:1] = numpy.ones((1, 8, 7, 1), dtype="uint8")
        label_explorer.show()
        qtbot.waitExposed(label_explorer)
        assert len(label_explorer._block_cache) == 1
        wrapped_populate_table.assert_called_once()
        assert label_explorer.tableWidget.rowCount() == 1

        # delete all labels
        label_pipeline_non_blocked.DeleteLabel.setValue(1)
        label_pipeline_non_blocked.DeleteLabel.setValue(-1)

        assert wrapped_populate_table.call_count == 2
        assert len(label_explorer._block_cache) == 0
        assert label_explorer.tableWidget.rowCount() == 0


def test_delete_labels_empty_table_blocked(
    qtbot,
    label_pipeline_blocked: OpCompressedUserLabelArray,
    label_explorer_blocked: Tuple[InputSlot, PixelLabelExplorerWidget],
):
    label_explorer: PixelLabelExplorerWidget
    _islot, label_explorer = label_explorer_blocked

    with patch.object(
        label_explorer, "_populate_table", wraps=label_explorer._populate_table
    ) as wrapped_populate_table:
        # annotation spans 2 blocks in the blocked case (blockshape (5, 5, 5, 1))
        label_pipeline_blocked.Input[0:1, 5:6, 0:7, 0:1] = numpy.ones((1, 1, 7, 1), dtype="uint8")

        label_explorer.show()
        qtbot.waitExposed(label_explorer)
        # Update while shown
        # annotation spans 2 blocks in the blocked case (blockshape (5, 5, 5, 1))
        label_pipeline_blocked.Input[0:1, 6:7, 0:7, 0:1] = numpy.ones((1, 1, 7, 1), dtype="uint8") * 2
        assert len(label_explorer._block_cache) == 2
        # Call count is three here as each block that is touched by above single write triggers an update
        assert wrapped_populate_table.call_count == 3
        assert label_explorer.tableWidget.rowCount() == 2

        # delete labels of val 1
        label_pipeline_blocked.clearLabel(1)
        # again a 2 increment of the counter, as clearing touches two blocks
        assert wrapped_populate_table.call_count == 5
        assert len(label_explorer._block_cache) == 2
        assert label_explorer.tableWidget.rowCount() == 1

        # delete labels of val 2, but this time go via the slot method
        label_pipeline_blocked.deleteLabel.setValue(2)
        label_pipeline_blocked.deleteLabel.setValue(-1)
        # again a 2 increment of the counter, as clearing touches two blocks
        assert wrapped_populate_table.call_count == 7
        assert len(label_explorer._block_cache) == 0
        assert label_explorer.tableWidget.rowCount() == 0


@pytest.mark.parametrize(
    "gui_variant",
    [
        pytest.param("label_explorer_blocked", id="blocked"),
        pytest.param("label_explorer_non_blocked", id="non-blocked"),
    ],
)
def test_sync_position(
    qtbot,
    gui_variant: Literal["label_explorer_blocked", "label_explorer_non_blocked"],
    request,
):
    islot: InputSlot
    label_explorer: PixelLabelExplorerWidget
    islot, label_explorer = request.getfixturevalue(gui_variant)

    positions = []
    label_explorer.positionRequested.connect(positions.append)
    label_explorer.show()
    qtbot.waitExposed(label_explorer)

    islot[0:1, 5:6, 6:7, 0:1] = numpy.ones((1, 1, 1, 1), dtype="uint8")
    islot[4:5, 1:2, 10:11, 0:1] = numpy.ones((1, 1, 1, 1), dtype="uint8")

    assert positions == []
    assert label_explorer.tableWidget.rowCount() == 2

    label_explorer.tableWidget.selectRow(1)
    assert positions == [{"c": 0.0, "x": 10.0, "y": 1.0, "z": 4.0}]

    label_explorer.tableWidget.selectRow(0)
    assert positions == [{"c": 0.0, "x": 10.0, "y": 1.0, "z": 4.0}, {"c": 0.0, "x": 6.0, "y": 5.0, "z": 0.0}]


@pytest.mark.parametrize(
    "pipeline_variant",
    [pytest.param("label_pipeline_blocked", id="blocked"), pytest.param("label_pipeline_non_blocked", id="dense")],
)
def test_delete_selected_annotations_undo_redo(qtbot, request, pipeline_variant):
    pipeline = request.getfixturevalue(pipeline_variant)
    output = pipeline.Output
    if isinstance(pipeline, OpCompressedUserLabelArray):
        pipeline.eraser.setValue(255)
        input_slot, blocks = pipeline.Input, pipeline.nonzeroBlocks
    else:
        input_slot, blocks = pipeline.LabelSinkInput, pipeline.NonzeroBlocks
        input_slot.meta.assignFrom(output.meta)
    data = numpy.zeros(output.meta.shape, dtype="uint8")
    # A ring surrounds another annotation of the same class and one of a different class.
    data[0, 0:5, 0, 0] = data[0, 0:5, 4, 0] = 1
    data[0, 0, 0:5, 0] = data[0, 4, 0:5, 0] = 1
    data[0, 2, 2, 0] = 1
    data[0, 2, 3, 0] = 2
    # Another selected annotation spans four cache blocks, with transitive connections.
    data[4, 8, 0:18, 0] = 1
    input_slot[tuple(slice(0, size) for size in data.shape)] = data
    explorer = PixelLabelExplorerWidget(blocks, output)
    qtbot.addWidget(explorer)
    explorer.show()
    qtbot.waitExposed(explorer)
    assert explorer.tableWidget.rowCount() == 4
    stack = QUndoStack(explorer)
    sink = LazyflowSinkSource(output, input_slot, eraser_value=255)
    gui = SimpleNamespace(
        _labelingSlots=SimpleNamespace(
            labelInput=input_slot, labelOutput=output, labelEraserValue=SimpleNamespace(value=255)
        ),
        editor=SimpleNamespace(_undoStack=stack, brushingController=SimpleNamespace(_dataSink=sink)),
    )
    explorer.deleteRequested.connect(partial(LabelingGui._delete_explorer_annotations, gui, explorer))
    explorer.tableWidget.sortItems(1, Qt.DescendingOrder)
    for row in range(explorer.tableWidget.rowCount()):
        item = explorer.tableWidget.item(row, 0)
        anchor = item.data(Qt.UserRole + 1)
        if anchor.position["z"] == 4 or anchor.position["x"] in (0, 4) or anchor.position["y"] in (0, 4):
            explorer.tableWidget.selectionModel().select(
                explorer.tableWidget.model().index(row, 0), QItemSelectionModel.Select | QItemSelectionModel.Rows
            )
    # Deleting and undoing update the table once, although several blocks are written.
    with patch.object(explorer, "_populate_table", wraps=explorer._populate_table) as populate:
        explorer._delete_selected()
        populate.assert_called_once()
    expected = numpy.zeros_like(data)
    expected[0, 2, 2, 0] = 1
    expected[0, 2, 3, 0] = 2
    numpy.testing.assert_array_equal(output[:].wait(), expected)
    assert explorer.tableWidget.rowCount() == 2
    assert stack.count() == 1
    with patch.object(explorer, "_populate_table", wraps=explorer._populate_table) as populate:
        stack.undo()
        populate.assert_called_once()
    numpy.testing.assert_array_equal(output[:].wait(), data)
    assert explorer.tableWidget.rowCount() == 4
    stack.redo()
    numpy.testing.assert_array_equal(output[:].wait(), expected)
    assert explorer.tableWidget.rowCount() == 2
    stack.undo()
    # All four annotations have overlapping bounding boxes; deleting all of them leaves no labels.
    explorer.tableWidget.selectAll()
    explorer._delete_selected()
    assert not output[:].wait().any()
    assert explorer.tableWidget.rowCount() == 0
    stack.undo()
    numpy.testing.assert_array_equal(output[:].wait(), data)
    explorer.cleanup()
    sink.clean_up()


@pytest.mark.parametrize("axiskeys", ["txyzc", "tzyxc"])
def test_delete_annotation_preserves_other_timepoint(qtbot, graph, axiskeys):
    shape = tuple({"t": 2, "x": 12, "y": 10, "z": 1, "c": 1}[k] for k in axiskeys)
    data = vigra.taggedView(numpy.zeros(shape, dtype="uint8"), axiskeys)
    with Pipeline(graph=graph) as pipeline:
        pipeline.add(OpArrayPiper, Input=data)
        cache = pipeline.add(
            OpCompressedUserLabelArray,
            blockShape=tuple({"t": 1, "x": 5, "y": 5, "z": 1, "c": 1}[k] for k in axiskeys),
            eraser=255,
        )
        labels = data.copy()
        labels.withAxes("txyzc")[:, 1:9, 2:3, 0, 0] = 1
        cache.Input[tuple(slice(0, size) for size in shape)] = labels
        explorer = PixelLabelExplorerWidget(cache.nonzeroBlocks, cache.Output)
        qtbot.addWidget(explorer)
        explorer.show()
        qtbot.waitExposed(explorer)
        assert explorer.tableWidget.rowCount() == 2
        stack = QUndoStack(explorer)
        sink = LazyflowSinkSource(cache.Output, cache.Input, eraser_value=255)
        gui = SimpleNamespace(
            _labelingSlots=SimpleNamespace(
                labelInput=cache.Input, labelOutput=cache.Output, labelEraserValue=cache.eraser
            ),
            editor=SimpleNamespace(_undoStack=stack, brushingController=SimpleNamespace(_dataSink=sink)),
        )
        explorer.deleteRequested.connect(partial(LabelingGui._delete_explorer_annotations, gui, explorer))
        for row in range(explorer.tableWidget.rowCount()):
            if explorer.tableWidget.item(row, 0).data(Qt.UserRole)["t"] == 1:
                explorer.tableWidget.selectRow(row)
                break
        explorer._delete_selected()
        result = vigra.taggedView(cache.Output[:].wait(), axiskeys).withAxes("txyzc")
        assert result[0].sum() == 8
        assert not result[1].any()
        stack.undo()
        numpy.testing.assert_array_equal(cache.Output[:].wait(), labels)
        explorer.cleanup()
        sink.clean_up()
