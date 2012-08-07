from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.stype import Opaque
from lazyflow.rtype import Everything

class OpObjectExtraction( Operator ):
    name = "Object Extraction"

    LabelImage = InputSlot()
    FeatureNames = InputSlot( stype=Opaque )
    Output = OutputSlot( stype=Opaque, rtype=Everything)

    def __init__( self, parent = None, graph = None, register = True ):
        super(OpObjectExtraction, self).__init__(parent=parent,graph=graph,register=register)
    
    def setupOutputs(self):
        pass
    
    def execute(self, slot, roi, result):
        pass

    def propagateDirty(self, inputSlot, roi):
        pass

