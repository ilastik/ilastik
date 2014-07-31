from lazyflow.graph import Operator, InputSlot, OutputSlot

import vigra
import numpy as np

from lazyflow.operators import OpLabelVolume, OpFilterLabels

class OpMriVolCC( Operator):
    name = "MRI Connected Components"
    Input = InputSlot()
    RawInput = InputSlot()
    Output = OutputSlot()

    Threshold = InputSlot(stype='int', value=0)
    MinSize = 0

    def __init__(self, *args, **kwargs):
        super(OpMriVolCC, self).__init__(*args, **kwargs)

        # in object classification OpPixelOperator is called initially, 
        # necessary ?
        # computes CCs
        self._opLabeler = OpLabelVolume( parent=self )
        self._opLabeler.Input.connect(self.Input)
        
        # Filters CCs
        self._opFilter = OpFilterLabels( parent=self )
        self._opFilter.Input.connect(self._opLabeler.CachedOutput )
        self._opFilter.MinLabelSize.setValue( self.MinSize )
        self._opFilter.MaxLabelSize.connect( self.Threshold )
        self._opFilter.BinaryOut.setValue(False)

        self.Output.connect( self._opFilter.Output ) 

    def execute(self, slot, subindex, roi, destination):
        assert False, "Shouldn't get here."
        
    def propagateDirty(self, inputSlot, subindex, roi):
        if inputSlot is self.Input:
             self.Output.setDirty(roi)
        if inputSlot is self.Threshold:
            self.Output.setDirty(slice(None))


class OpConnectedComponents( Operator ):
    name = 'Connected Components'
    
