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

from typing import NamedTuple, Tuple
from unittest.mock import patch

import pytest
from qtpy.QtGui import QColor

from ilastik.widgets.labelListView import ColorDialog


class ColorTuple(NamedTuple):
    brush_color: QColor
    pmap_color: QColor


@pytest.fixture
def nonmatching_colors() -> ColorTuple:
    brush_color = QColor("red")
    pmap_color = QColor("blue")
    return ColorTuple(brush_color, pmap_color)


@pytest.fixture
def default_colors() -> ColorTuple:
    brush_color = QColor("green")
    pmap_color = QColor("green")
    return ColorTuple(brush_color, pmap_color)


@pytest.fixture
def color_dialog(qtbot, default_colors: ColorTuple) -> ColorDialog:
    brush_color, pmap_color = default_colors
    dlg = ColorDialog(brush_color, pmap_color)
    qtbot.addWidget(dlg)
    qtbot.waitExposed(dlg)

    return dlg


@pytest.fixture
def color_dialog_nonmatching(qtbot, nonmatching_colors: ColorTuple) -> ColorDialog:
    brush_color, pmap_color = nonmatching_colors
    dlg = ColorDialog(brush_color, pmap_color)
    qtbot.addWidget(dlg)
    qtbot.waitExposed(dlg)

    return dlg


def test_construct(color_dialog: ColorDialog, default_colors: ColorTuple):
    assert color_dialog.brushColor() == default_colors.brush_color
    assert color_dialog.pmapColor() == default_colors.pmap_color
    assert color_dialog.brushColor() == color_dialog.pmapColor()
    assert color_dialog.ui.linkColorCheckBox.checkState()


@patch("ilastik.widgets.labelListView.ColorDialog._getColor", lambda *x: QColor("yellow"))
def test_sync_brush_color(color_dialog: ColorDialog, default_colors: ColorTuple):
    color_dialog.onBrushColor()
    assert color_dialog.brushColor() == QColor("yellow")
    assert color_dialog.pmapColor() == QColor("yellow")


@patch("ilastik.widgets.labelListView.ColorDialog._getColor", lambda *x: QColor("rose"))
def test_sync_pmap_color(color_dialog: ColorDialog, default_colors: ColorTuple):
    color_dialog.onPmapColor()
    assert color_dialog.brushColor() == QColor("rose")
    assert color_dialog.pmapColor() == QColor("rose")


def test_construct_nonmatching(color_dialog_nonmatching: ColorDialog, nonmatching_colors: ColorTuple):
    assert color_dialog_nonmatching.brushColor() == nonmatching_colors.brush_color
    assert color_dialog_nonmatching.pmapColor() == nonmatching_colors.pmap_color
    assert not color_dialog_nonmatching.ui.linkColorCheckBox.checkState()


@patch("ilastik.widgets.labelListView.ColorDialog._getColor", lambda *x: QColor("yellow"))
def test_sync_off_brush_color(color_dialog_nonmatching: ColorDialog, nonmatching_colors: ColorTuple):
    color_dialog_nonmatching.onBrushColor()
    assert color_dialog_nonmatching.brushColor() == QColor("yellow")
    assert color_dialog_nonmatching.pmapColor() == nonmatching_colors.pmap_color


@patch("ilastik.widgets.labelListView.ColorDialog._getColor", lambda *x: QColor("rose"))
def test_sync_off_pmap_color(color_dialog_nonmatching: ColorDialog, nonmatching_colors: ColorTuple):
    color_dialog_nonmatching.onPmapColor()
    assert color_dialog_nonmatching.brushColor() == nonmatching_colors.brush_color
    assert color_dialog_nonmatching.pmapColor() == QColor("rose")


def test_sync_toggle(color_dialog: ColorDialog, default_colors: ColorTuple):
    assert color_dialog.brushColor() == default_colors.brush_color
    assert color_dialog.pmapColor() == default_colors.pmap_color

    color_dialog.ui.linkColorCheckBox.toggle()
    assert color_dialog.brushColor() == default_colors.brush_color
    assert color_dialog.pmapColor() == default_colors.brush_color


@patch("ilastik.widgets.labelListView.ColorDialog._getColor", lambda *x: None)
def test_cancel_color_selection_no_color_change(color_dialog: ColorDialog, default_colors: ColorTuple):
    assert color_dialog.brushColor() == default_colors.brush_color
    assert color_dialog.pmapColor() == default_colors.pmap_color

    color_dialog.onBrushColor()
    assert color_dialog.brushColor() == default_colors.brush_color
    assert color_dialog.pmapColor() == default_colors.brush_color
