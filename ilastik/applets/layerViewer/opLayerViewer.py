from lazyflow.graph import Operator, InputSlot, OutputSlot

class OpLayerViewer(Operator):
    name = "OpLayerViewer"
    category = "top-level"

    RawInput = InputSlot()

