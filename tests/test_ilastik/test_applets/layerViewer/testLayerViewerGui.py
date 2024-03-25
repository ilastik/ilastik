import numpy
import pytest
import vigra

from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui
from lazyflow.graph import Graph
from lazyflow.operator import Operator
from lazyflow.slot import OutputSlot, InputSlot


class OpPassthrough(Operator):
    """Op with a slot for LayerViewerGui to put in self.observedSlots"""

    Image = InputSlot()
    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.Output.connect(self.Image)

    def propagateDirty(self, slot, subindex, roi):
        pass


def make_simple_op():
    op = OpPassthrough(parent=Operator(graph=Graph()))
    op.Image.setValue(numpy.array([[[1, 1], [1, 1]], [[1, 1], [1, 1]]]))
    op.Output.meta.axistags = vigra.defaultAxistags("xyz")
    return op


@pytest.mark.parametrize("prefer_2d", [True, False])
def test_layer_update_respects_2d_default(prefer_2d):
    # This test relies on the default implementation of LayerViewerGui.setupLayers provided in the base class.
    op = make_simple_op()
    if prefer_2d:  # False case here corresponds to prefer_2d being undefined in prod
        op.Output.meta.prefer_2d = True
    gui = LayerViewerGui(None, op)
    assert prefer_2d == gui.volumeEditorWidget.quadview.dock1_ofSplitHorizontal1._isMaximized
    assert not gui.volumeEditorWidget.quadview.dock2_ofSplitHorizontal1._isMaximized
    assert not gui.volumeEditorWidget.quadview.dock1_ofSplitHorizontal2._isMaximized


def test_layer_update_does_not_update_viewer_with_unready_layers(monkeypatch):
    """
    Prevents regression to a race condition where volumina.tileprovier can crash
    because a layer's data source slot is ready when _refreshTile creates a request,
    but becomes unready by the time the request is executed (_fetch_layer_tile).
    Reproducing the exact problem is difficult (see PR on GitHub), but in general
    volumina should be able to expect layers to be ready whenever it is asked to draw them.
    """
    gui = LayerViewerGui(None, make_simple_op())
    first_op = make_simple_op()
    layer_with_op_to_be_dropped = gui.createStandardLayerFromSlot(first_op.Output)
    layer_with_ready_op = gui.createStandardLayerFromSlot(make_simple_op().Output)

    # Feed first layer to the gui, then clean it up and prepare a new (ready) layer
    monkeypatch.setattr(gui, "setupLayers", lambda: [layer_with_op_to_be_dropped])
    monkeypatch.setattr(gui, "determineDatashape", lambda: (1, 5, 5, 5, 1))
    gui.updateAllLayers()
    first_op.cleanUp()
    monkeypatch.setattr(gui, "setupLayers", lambda: [layer_with_ready_op])
    monkeypatch.setattr(gui, "determineDatashape", lambda: (1, 6, 6, 6, 1))

    # Ensure the gui only feeds the shape update to the viewer after it has dropped the obsolete layer
    def assert_gui_layers_ready():
        for layer in gui.layerstack:
            msg = f"updateAllLayers should not update dataShape={gui.editor.dataShape} while holding obsolete {layer=}."
            assert layer.datasources[0].dataSlot.ready(), msg

    gui.editor.shapeChanged.connect(assert_gui_layers_ready)
    gui.updateAllLayers()
