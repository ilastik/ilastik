import numpy
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
    op.Image.setValue(numpy.array([[1, 1], [1, 1]]))
    op.Output.meta.axistags = vigra.defaultAxistags("xy")
    return op


def test_layer_update_respects_2d_default():
    # This test relies on the default implementation of LayerViewerGui.setupLayers provided in the base class.
    op = make_simple_op()
    op.Output.meta.prefer_2d = True
    gui = LayerViewerGui(None, op)
    assert gui.volumeEditorWidget.quadview.dock1_ofSplitHorizontal1._isMaximized
    assert not gui.volumeEditorWidget.quadview.dock2_ofSplitHorizontal1._isMaximized
    assert not gui.volumeEditorWidget.quadview.dock1_ofSplitHorizontal2._isMaximized


def test_layer_update_does_not_update_viewer_with_unready_layers(monkeypatch):
    """
    This reproduces a complex race condition encountered when switching scales in the dev-version OME implementation.
    * LayerViewerGui.updateAllLayers detects shape change, sets self.editor.dataShape = newShape
    * Qt triggers drawBackground on the editor's imageScenes (I think this happens after `dataShape.setter` exits)
    * _refreshTile calls `LazyflowSource.request` (tileprovider.py:277 `ims_req = ims.request(dataRect, stack_id[1])`)
    * dispatches the req to the threadpool (tileprovider.py:287 `fetch_fn = partial(self._fetch_layer_tile, ...)`)
    * `ims.request` calls op.Output[] and catches SlotNotReadyErrors, but at this time the slot is still ready
    * the delayed _fetch_layer_tile awaits the request, but now the slot is not ready anymore
    * _fetch_layer_tile does not catch SlotNotReadyErrors, so it crashes

    Reproducing the exact problem is difficult, but in general volumina should be able to expect layers to be ready
    whenever it is asked to draw them.
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
