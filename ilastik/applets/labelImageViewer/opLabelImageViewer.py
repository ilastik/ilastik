from lazyflow.graph import Operator, InputSlot

class OpLabelImageViewer( Operator ):
    RawImage = InputSlot()
    LabelImage = InputSlot()
