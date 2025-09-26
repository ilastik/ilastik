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
from typing import Iterator, Tuple
from unittest.mock import patch

import numpy
import pytest
import vigra

from ilastik.applets.labeling.connectBlockedLabels import Neighbourhood
from ilastik.applets.labeling.labelExplorer import LabelExplorerWidget
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
def label_explorer_blocked(qtbot, label_pipeline_blocked) -> Tuple[InputSlot, LabelExplorerWidget]:
    ex = LabelExplorerWidget(label_pipeline_blocked.nonzeroBlocks, label_pipeline_blocked.Output)
    qtbot.addWidget(ex)
    return label_pipeline_blocked.Input, ex


@pytest.fixture
def label_explorer_non_blocked(
    qtbot, label_pipeline_non_blocked: OpDenseLabelArray
) -> Tuple[InputSlot, LabelExplorerWidget]:
    ex = LabelExplorerWidget(label_pipeline_non_blocked.NonzeroBlocks, label_pipeline_non_blocked.Output)
    qtbot.addWidget(ex)
    return label_pipeline_non_blocked.LabelSinkInput, ex


@pytest.mark.parametrize(
    "gui_variant, expected_neighbourhood",
    [
        pytest.param("label_explorer_blocked", Neighbourhood.SINGLE, id="blocked"),
        pytest.param("label_explorer_non_blocked", Neighbourhood.NONE, id="non-blocked"),
    ],
)
def test_construct(qtbot, gui_variant, expected_neighbourhood, request):
    label_explorer: LabelExplorerWidget
    _islot, label_explorer = request.getfixturevalue(gui_variant)
    with patch.object(
        label_explorer, "initialize_table", wraps=label_explorer.initialize_table
    ) as wrapped_initialize_table:

        # widget not shown - should prevent table initialization
        wrapped_initialize_table.assert_not_called()
        label_explorer.show()
        qtbot.waitExposed(label_explorer)
        assert label_explorer._neighbourhood == expected_neighbourhood
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
    gui_variant,
    request,
    expected_n_blocks: int,
):
    islot = InputSlot
    label_explorer: LabelExplorerWidget
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
def test_no_update_on_update_when_not_shown(qtbot, gui_variant: str, expected_n_blocks: int, request):
    islot = InputSlot
    label_explorer: LabelExplorerWidget
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
    label_explorer_non_blocked: Tuple[InputSlot, LabelExplorerWidget],
):
    label_explorer: LabelExplorerWidget
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
    label_explorer_blocked: Tuple[InputSlot, LabelExplorerWidget],
):
    label_explorer: LabelExplorerWidget
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

        # delete labels of val 2
        label_pipeline_blocked.clearLabel(2)
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
    gui_variant: str,
    request,
):
    islot: InputSlot
    label_explorer: LabelExplorerWidget
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
