import numpy as np
import pytest
import vigra
from qtpy.QtCore import QLocale, Qt

from ilastik.applets.wsdt.opWsdt import OpCachedWsdt
from ilastik.applets.wsdt.wsdtGui import WsdtGui
from lazyflow.graph import Operator
from lazyflow.operators import OpArrayPiper


@pytest.mark.parametrize("locale_name,separator", [("de_DE", ","), ("en_US", ".")])
def test_threshold_editing(qtbot, graph, locale_name, separator):
    op = OpCachedWsdt(parent=Operator(graph=graph))
    source = OpArrayPiper(parent=op.parent)
    source.Input.setValue(vigra.taggedView(np.zeros((10, 10, 1), dtype=np.float32), "yxc"))
    op.Input.connect(source.Output)
    gui = WsdtGui(None, op)
    qtbot.addWidget(gui)
    gui.setEnabled(True)
    try:
        box = gui.threshold_box
        box.setLocale(QLocale(locale_name))
        box.setValue(0.1)
        gui.appletDrawer().show()
        box.setFocus()
        editor = box.lineEdit()
        editor.setCursorPosition(3)

        qtbot.keyClick(box, Qt.Key_Backspace)
        assert editor.text() == f"0{separator}0"
        assert op.Threshold.value == 0.0

        qtbot.keyClicks(box, "2")
        assert editor.text() == f"0{separator}20"
        assert op.Threshold.value == 0.2

        qtbot.keyClick(box, Qt.Key_Return)
        assert box.value() == 0.2

        op.Threshold.setValue(0.3)
        assert box.value() == 0.3
    finally:
        gui.stopAndCleanUp()
        op.cleanUp()
        source.cleanUp()
