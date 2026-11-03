import numpy as np
import vigra

from lazyflow.graph import Graph
from lazyflow.operators.generic import OpMultiChannelSelector
from ilastik.widgets.channelSelectionWidget import ChannelSelectionWidget


def test_channel_control(qtbot, graph: Graph):
    op = OpMultiChannelSelector(graph=graph)
    widget = ChannelSelectionWidget(op.Input, op.SelectedChannels)
    qtbot.addWidget(widget)
    try:
        assert widget.isHidden()
        op.Input.setValue(vigra.taggedView(np.zeros((10, 10, 1)), "yxc"))
        assert widget.isHidden()
        assert op.Output.meta.shape == (10, 10, 1)
        op.Input.setValue(vigra.taggedView(np.zeros((10, 10, 3)), "yxc"))
        assert not widget.isHidden()
        assert [c.isChecked() for c in widget._checkboxes] == [True, False, False]
        widget._checkboxes[1].click()
        assert op.SelectedChannels.value == (0, 1)
        widget._checkboxes[1].click()
        assert op.SelectedChannels.value == (0,)
        assert widget._checkboxes[0].isChecked()

        # Not selecting any checkbox in the gui should result in non-ready output
        widget._checkboxes[0].click()
        assert [c.isChecked() for c in widget._checkboxes] == [False, False, False]
        assert not op.Output.ready()
        assert op.SelectedChannels.ready()
        assert op.SelectedChannels.value == ()

        op.SelectedChannels.setValue((0, 2))
        assert [c.isChecked() for c in widget._checkboxes] == [True, False, True]
        widget._checkboxes[1].click()
        assert op.SelectedChannels.value == (0, 1, 2)
        assert [c.isChecked() for c in widget._checkboxes] == [True, True, True]
        op.Input.disconnect()
        assert widget.isHidden()
    finally:
        widget.cleanUp()
        op.cleanUp()
