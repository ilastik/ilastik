import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel

from ilastik.widgets.collapsibleWidget import CollapsibleWidget


@pytest.fixture
def widget(qtbot):
    w = QLabel("Test 42")
    qtbot.addWidget(w)
    return w


def test_state_change(qtbot, widget):
    w = CollapsibleWidget(widget, animation_duration=0)

    qtbot.addWidget(w)
    w.show()
    with qtbot.waitExposed(w):
        # start off collapsed
        assert widget.visibleRegion().isEmpty()

        # expand
        qtbot.mouseClick(w._toggleButton, Qt.MouseButton.LeftButton)
        qtbot.wait(50)  # wait for change to settle, since we're querying gui state

        assert not widget.visibleRegion().isEmpty()

        # collapse again
        qtbot.mouseClick(w._toggleButton, Qt.MouseButton.LeftButton)
        qtbot.wait(50)  # wait for change to settle, since we're querying gui state

        assert widget.visibleRegion().isEmpty()
