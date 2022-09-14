from unittest import mock

import pytest
from PyQt5.QtCore import Qt

from ilastik.widgets.featureTableWidget import FeatureTableWidget, FeatureEntry


@pytest.fixture
def widget(qtbot):
    w = FeatureTableWidget(
        None,
        (
            ("Color", [FeatureEntry("Banana", minimum_scale=0.3)]),
            ("Edge", [FeatureEntry("Mango"), FeatureEntry("Cherry")]),
        ),
        [0.3, 0.7, 1, 1.6, 3.5, 5.0, 10.0],
        computeIn2d=[True, False, True, True, True, False, False],
    )
    qtbot.addWidget(w)
    w.show()

    qtbot.waitExposed(w)

    return w


def test_ctrl_a_shortcut_should_select_everything(qtbot, widget: FeatureTableWidget):
    assert widget.featureMatrix == [
        [False, False, False, False, False, False, False],
        [False, False, False, False, False, False, False],
        [False, False, False, False, False, False, False],
    ]
    assert widget.computeIn2d == [True, False, True, True, True, False, False]

    qtbot.keyPress(widget, Qt.Key_A, Qt.ControlModifier)

    assert widget.computeIn2d == [True, False, True, True, True, False, False]
    assert widget.featureMatrix == [
        [True, True, True, True, True, True, True],
        [False, True, True, True, True, True, True],
        [False, True, True, True, True, True, True],
    ]
