from typing import Literal

import numpy as np
import pytest
import vigra
from qtpy.QtCore import QLocale, Qt

from ilastik.applets.wsdt.opWsdt import OpCachedWsdt
from ilastik.applets.wsdt.wsdtGui import WsdtGui
from lazyflow.graph import Graph, Operator
from lazyflow.operators import OpArrayPiper


@pytest.fixture
def opwsdt(graph: Graph):
    parent = Operator(graph=graph)
    op = OpCachedWsdt(parent=parent)
    source = OpArrayPiper(parent=parent)
    source.Input.setValue(vigra.taggedView(np.zeros((10, 10, 1), dtype=np.float32), "yxc"))
    op.Input.connect(source.Output)
    yield op
    op.cleanUp()
    source.cleanUp()


@pytest.fixture
def wsdtgui(opwsdt: OpCachedWsdt, qtbot):
    gui = WsdtGui(None, opwsdt)
    qtbot.addWidget(gui)
    gui.setEnabled(True)
    yield gui
    gui.stopAndCleanUp()


@pytest.mark.parametrize("locale_name,separator", [("de_DE", ","), ("en_US", ".")])
def test_threshold_editing(
    qtbot, opwsdt: OpCachedWsdt, wsdtgui: WsdtGui, locale_name: Literal["de_DE", "en_US"], separator: Literal[",", "."]
):
    box = wsdtgui.threshold_box
    box.setLocale(QLocale(locale_name))
    box.setValue(0.1)
    wsdtgui.appletDrawer().show()
    box.setFocus()
    editor = box.lineEdit()
    editor.setCursorPosition(3)

    qtbot.keyClick(box, Qt.Key_Backspace)
    assert editor.text() == f"0{separator}0"
    assert opwsdt.Threshold.value == 0.0

    qtbot.keyClicks(box, "2")
    assert editor.text() == f"0{separator}20"
    assert opwsdt.Threshold.value == 0.2

    qtbot.keyClick(box, Qt.Key_Return)
    assert box.value() == 0.2

    opwsdt.Threshold.setValue(0.3)
    assert box.value() == 0.3


@pytest.mark.parametrize("locale_name,separator", [("de_DE", ","), ("en_US", ".")])
def test_sigma_editing(
    qtbot, opwsdt: OpCachedWsdt, wsdtgui: WsdtGui, locale_name: Literal["de_DE", "en_US"], separator: Literal[",", "."]
):
    box = wsdtgui.sigma_box
    box.setLocale(QLocale(locale_name))
    box.setValue(3.1)
    wsdtgui.appletDrawer().show()
    box.setFocus()

    assert opwsdt.Sigma.value == 3.1

    editor = box.lineEdit()
    editor.setCursorPosition(1)

    qtbot.keyClick(box, Qt.Key_Backspace)
    assert editor.text() == f"{separator}1"
    assert opwsdt.Sigma.value == 0.1

    qtbot.keyClicks(box, "1")
    assert editor.text() == f"1{separator}1"
    assert opwsdt.Sigma.value == 1.1

    qtbot.keyClick(box, Qt.Key_Return)
    assert box.value() == 1.1

    opwsdt.Sigma.setValue(4.2)
    assert box.value() == 4.2


@pytest.mark.parametrize("locale_name,separator", [("de_DE", ","), ("en_US", ".")])
def test_alpha_editing(
    qtbot, opwsdt: OpCachedWsdt, wsdtgui: WsdtGui, locale_name: Literal["de_DE", "en_US"], separator: Literal[",", "."]
):
    box = wsdtgui.alpha_box
    box.setLocale(QLocale(locale_name))
    box.setValue(4.1)
    wsdtgui.appletDrawer().show()
    box.setFocus()

    assert opwsdt.Alpha.value == 4.1

    editor = box.lineEdit()
    editor.setCursorPosition(1)

    qtbot.keyClick(box, Qt.Key_Backspace)
    assert editor.text() == f"{separator}1"
    assert opwsdt.Alpha.value == 0.1

    qtbot.keyClicks(box, "2")
    assert editor.text() == f"2{separator}1"
    assert opwsdt.Alpha.value == 2.1

    qtbot.keyClick(box, Qt.Key_Return)
    assert box.value() == 2.1

    opwsdt.Alpha.setValue(0.3)
    assert box.value() == 0.3
