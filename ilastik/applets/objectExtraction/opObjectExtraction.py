from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.stype import Opaque
from lazyflow.rtype import Everything
import numpy

class OpObjectExtraction( Operator ):
    name = "Object Extraction"

    RawData = InputSlot()
    Segmentation = InputSlot()
    FeatureNames = InputSlot( stype=Opaque )

    LabelImage = OutputSlot()
    Output = OutputSlot( stype=Opaque )

    def __init__( self, parent = None, graph = None, register = True ):
        super(OpObjectExtraction, self).__init__(parent=parent,graph=graph,register=register)
    
    def setupOutputs(self):
        pass
    
    def execute(self, slot, roi, result):
        res = {}
        if slot is self.Output:
            for t in range( roi.start[0]. roi.stop[0] ):
               res[t] = numpy.asarray( [[ 100, 100, 20], [100,10, 39]], dtype=numpy.float32 ) 


    def propagateDirty(self, inputSlot, roi):
        pass

