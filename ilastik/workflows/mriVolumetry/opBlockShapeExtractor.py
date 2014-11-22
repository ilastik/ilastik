
from lazyflow.operator import Operator, InputSlot, OutputSlot

class OpBlockShapeExtractor(Operator):
    '''
    Provides block shape as 
      * single time slice
      * single channel slice
      * full spatial volume
    needed because we cannot set the blockshape in setupOutputs
    if we want to deserialize the cache.
    See https://github.com/JensNRAD/ilastik/issues/37 for details.
    '''
    Input = InputSlot()
    BlockShape = OutputSlot()

    def setupOutputs(self):
        # set cache chunk shape to the whole spatial volume
        ts = self.Input.meta.getTaggedShape()
        ts['c'] = 1
        ts['t'] = 1
        self._bs = tuple(ts[k] for k in ts)
        self.BlockShape.meta.dtype = int
        self.BlockShape.meta.shape = (len(self._bs),)

    def execute(self, slot, subindex, roi, result):
        assert roi.start[0] == 0
        assert roi.stop[0] == len(self._bs)
        result[:] = self._bs

    def propagateDirty(self, *args):
        # dirtiness does not change block shapes
        pass
        
