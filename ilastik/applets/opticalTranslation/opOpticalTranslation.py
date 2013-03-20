import vigra
import pgmlink
import numpy
from lazyflow.graph import Operator, InputSlot, OutputSlot

class OpOpticalTranslation(Operator):
    Input = InputSlot()
    Sigmas = InputSlot( value={'x':3.5, 'y':3.5, 'z':1.0} )
    
    Output = OutputSlot()

    def setupOutputs(self):
        pass
    
    def execute(self, slot, subindex, roi, result):
        return result
        
    def propagateDirty(self, slot, subindex, roi):
        pass
