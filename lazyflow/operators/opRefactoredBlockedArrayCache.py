from lazyflow.graph import Operator, InputSlot, OutputSlot

from opCacheFixer import OpCacheFixer
from opUnblockedArrayCache import OpUnblockedArrayCache
from opSplitRequestsBlockwise import OpSplitRequestsBlockwise

class OpRefactoredBlockedArrayCache(Operator):
    Input = InputSlot(allow_mask=True)
    fixAtCurrent = InputSlot(value=False)
    #BlockShape = InputSlot()
    innerBlockShape = InputSlot(optional=True)
    outerBlockShape = InputSlot()
    
    Output = OutputSlot(allow_mask=True)
    
    def __init__(self, *args, **kwargs):
        super( OpRefactoredBlockedArrayCache, self ).__init__(*args, **kwargs)
        
        # Input ---------> opCacheFixer -> opUnblockedArrayCache -> opSplitRequestsBlockwise -> Output
        #                 /                                        /
        # fixAtCurrent --                                         /
        #                                                        /
        # BlockShape --------------------------------------------
        
        self._opCacheFixer = OpCacheFixer( parent=self )
        self._opCacheFixer.Input.connect( self.Input )
        self._opCacheFixer.fixAtCurrent.connect( self.fixAtCurrent )

        self._opUnblockedArrayCache = OpUnblockedArrayCache( parent=self )
        self._opUnblockedArrayCache.Input.connect( self._opCacheFixer.Output )

        self._opSplitRequestsBlockwise = OpSplitRequestsBlockwise( always_request_full_blocks=True, parent=self )
        self._opSplitRequestsBlockwise.BlockShape.connect( self.outerBlockShape )
        self._opSplitRequestsBlockwise.Input.connect( self._opUnblockedArrayCache.Output )

        # FIXME: Connecting the output directly like this will result in RAM being allocated for zero-blocks in the cache when fixAtCurrent=True.
        #        It doesn't result in incorrect results, but it is inefficient.
        self.Output.connect( self._opSplitRequestsBlockwise.Output )
        
    def setupOutputs(self):
        pass

    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here."

    def propagateDirty(self, slot, subindex, roi):
        pass
