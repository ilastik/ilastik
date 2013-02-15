from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.operators import OpLabelImage, OpCompressedCache

class OpCachedLabelImage(Operator):
    """
    Combines OpLabelImage with OpCompressedCache, and provides a default block shape.
    """
    Input = InputSlot()

    BackgroundLabels = InputSlot(optional=True) # Optional. See OpLabelImage for details.
    BlockShape = InputSlot(optional=True)   # If not provided, blockshape is 1 time slice, 1 channel slice, 
                                            #  and the entire volume in xyz.
    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpCachedLabelImage, self).__init__(*args, **kwargs)
        
        # Hook up the labeler
        self._opLabelImage = OpLabelImage( parent=self )
        self._opLabelImage.Input.connect( self.Input )
        self._opLabelImage.BackgroundLabels.connect( self.BackgroundLabels )

        # Hook up the cache
        self._opCache = OpCompressedCache( parent=self )
        self._opCache.Input.connect( self._opLabelImage.Output )
        
        # Hook up our output slot
        self.Output.connect( self._opCache.Output )
    
    def setupOutputs(self):
        if self.BlockShape.ready():
            self._opCache.BlockShape.setValue( self.BlockShape.value )
        else:
            # By default, block shape is the same as the entire image shape,
            #  but only 1 time slice and 1 channel slice
            taggedBlockShape = self.Input.meta.getTaggedShape()
            taggedBlockShape['t'] = 1
            taggedBlockShape['c'] = 1
            self._opCache.BlockShape.setValue( tuple( taggedBlockShape.values() ) )

    def execute(self, slot, subindex, roi, destination):
        assert False, "Shouldn't get here."
    
    def propagateDirty(self, slot, subindex, roi):
        pass # Nothing to do...
