from lazyflow.graph import Operator, InputSlot, OutputSlot

import vigra
import numpy as np

from lazyflow.operators import OpLabelVolume, OpFilterLabels, \
    OperatorWrapper,  OpCompressedCache
from lazyflow.stype import Opaque

from opCostVolumeFilter import OpFanIn

class OpMriVolCC( Operator):
    name = "MRI Connected Components"
    Input = InputSlot(level=1)
    RawInput = InputSlot()

    FanInOutput = OutputSlot()
    Output = OutputSlot(level=1)
    CachedOutput = OutputSlot(level=1)    

    Threshold = InputSlot(level=1, stype='int', value=0)
    CurOperator = InputSlot(stype='int', value=0)

    LabelNames = InputSlot(stype=Opaque)

    def __init__(self, *args, **kwargs):
        super(OpMriVolCC, self).__init__(*args, **kwargs)

        # in object classification OpPixelOperator is called initially, 
        # necessary ?
        # computes CCs
        self._opLabeler = OperatorWrapper( OpLabelVolume, parent=self )
        self._opLabeler.Input.connect(self.Input)

        self._cache = OperatorWrapper( OpCompressedCache , 
                                       broadcastingSlotNames=['BlockShape'], 
                                       parent=self )
        self._cache.name = "OpMriVol.OutputCache"

        # Filters CCs
        self._opFilter = OperatorWrapper( OpFilterLabels, parent=self )
        self._opFilter.Input.connect(self._opLabeler.CachedOutput )
        self._opFilter.MinLabelSize.connect( self.Threshold )
        # all CCs from one channel belong to the same class        
        self._opFilter.BinaryOut.setValue(True)

        # What to use for Input for the cache? _opFilter.Output?
        self._cache.Input.connect(self._opFilter.Output) 
        self.CachedOutput.connect(self._cache.Output)
        self.Output.connect( self.CachedOutput )

        # Combining channels to a level=0 label image
        self._opFanIn = OpFanIn(parent=self)
        self.FanInOutput.connect(self._opFanIn.Output)
        self._opFanIn.Input.connect(self.CachedOutput)
        
        
    def setupOutputs(self):
        # set cache chunk shape to the whole spatial volume
        tagged_shape = self.Input[0].meta.getTaggedShape()
        tagged_shape['t'] = 1
        tagged_shape['c'] = 1
        blockshape = map(lambda k: tagged_shape[k],
                         ''.join(tagged_shape.keys()))
        self._cache.BlockShape.setValue(tuple(blockshape))
        self.Threshold.resize(len(self.Input))


    def execute(self, slot, subindex, roi, destination):
        assert False, "Shouldn't get here."
        
    def propagateDirty(self, inputSlot, subindex, roi):
        if inputSlot is self.Input:
            for slot in self.Output:
                slot.setDirty(roi)
        if inputSlot is self.Threshold:
            self.Output.setDirty(roi)

'''
# Alternativ Implementation extends OpFilterLabels with cache
class OpMriFilterLabels( OpFilterLabels ):
    CachedOutput = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpMriFilterLabels, self).__init__(*args, **kwargs)
        self._cache = OpCompressedCache(parent=self )
        self._cache.name = "OpMriFilterLabels.OutputCache"
        self._cache.Input.connect(self.Output) 
        self.CachedOutput.connect(self._cache.Output)

    def setupOutputs(self):
        self.Output.meta.assignFrom(self.Input.meta)

        tagged_shape = self.Input.meta.getTaggedShape()
        tagged_shape['t'] = 1
        tagged_shape['c'] = 1
        blockshape = map(lambda k: tagged_shape[k],
                         ''.join(tagged_shape.keys()))
        self._cache.BlockShape.setValue(tuple(blockshape))
'''
