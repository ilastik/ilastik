import numpy

from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui
from lazyflow.operator import Operator
from lazyflow.slot import OutputSlot, InputSlot


class OpPassthrough(Operator):
    Image = InputSlot()
    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.Output.connect(self.Image)

    def propagateDirty(self, slot, subindex, roi):
        pass


def test_layer_update_respects_2d_default(graph):
    op = OpPassthrough(parent=Operator(graph=graph))
    op.Image.setValue(numpy.random.rand(5, 5, 5))
    op.Output.meta.prefer_2d = True
    gui = LayerViewerGui(None, op)
    assert gui.volumeEditorWidget.quadview.dock1_ofSplitHorizontal1._isMaximized
    assert not gui.volumeEditorWidget.quadview.dock2_ofSplitHorizontal1._isMaximized
    assert not gui.volumeEditorWidget.quadview.dock1_ofSplitHorizontal2._isMaximized
