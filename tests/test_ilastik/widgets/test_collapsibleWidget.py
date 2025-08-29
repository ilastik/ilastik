import pytest
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QLabel

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
        qtbot.wait(150)  # wait for change to settle, since we're querying gui state

        assert not widget.visibleRegion().isEmpty()

        # collapse again
        qtbot.mouseClick(w._toggleButton, Qt.MouseButton.LeftButton)
        qtbot.wait(150)  # wait for change to settle, since we're querying gui state

        assert widget.visibleRegion().isEmpty()
