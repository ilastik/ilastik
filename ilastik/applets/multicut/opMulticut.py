import numpy as np
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.operators import OpCompressedCache

class OpMulticut(Operator):
    Probabilities = InputSlot()
    Superpixels = InputSlot()
    
    Output = OutputSlot() # Pixelwise output (not RAG, etc.)
    
    def __init__(self, *args, **kwargs):
        super( OpMulticut, self ).__init__(*args, **kwargs)
    
    def setupOutputs(self):
        assert self.Superpixels.meta.dtype == np.uint32
        self.Output.meta.assignFrom(self.Superpixels.meta)
        self.Output.meta.display_mode = 'random-colortable'
    
    def execute(self, slot, subindex, roi, result):
        # Starting with debug: just pass the superpixels through
        self.Superpixels[:].writeInto(result).wait()        

    def propagateDirty(self, slot, subindex, roi):
        # Everything is dirty...
        self.Output.setDirty()

class OpCachedMulticut(Operator):
    """
    A drop-in replacement for OpMulticut, except that the output is cached,
    and therefore the entire output is always requested at once.
    (It would be a mistake to ask OpMulticut for a single slice of output.)
    """
    RawData = InputSlot(optional=True) # Used for display only
    Probabilities = InputSlot()
    Superpixels = InputSlot()
    
    Output = OutputSlot()
    
    def __init__(self, *args, **kwargs):
        super( OpCachedMulticut, self ).__init__(*args, **kwargs)
        
        cached_multicut_slot_names = set(map(lambda s: s.name, OpCachedMulticut.inputSlots + OpCachedMulticut.outputSlots))
        multicut_slot_names = set(map(lambda s: s.name, OpMulticut.inputSlots + OpMulticut.outputSlots))
        assert cached_multicut_slot_names.issuperset( multicut_slot_names ), \
            "OpCachedMulticut is supposed to have the same slot interface as OpMulticut. "\
            "Did you add a slot to OpMulticut?"
        
        self._opMulticut = OpMulticut(parent=self)
        self._opMulticut.Probabilities.connect( self.Probabilities )
        self._opMulticut.Superpixels.connect( self.Superpixels )
        
        self._opCache = OpCompressedCache(parent=self)
        self._opCache.Input.connect( self._opMulticut.Output )
        self.Output.connect( self._opCache.Output )

    def setupOutputs(self):
        # Sanity checks
        assert self.Probabilities.meta.getAxisKeys()[-1] == 'c'
        assert self.Superpixels.meta.getAxisKeys()[-1] == 'c'
        assert self.Probabilities.meta.shape[:-1] == self.Superpixels.meta.shape[:-1], \
            "Probability and Superpixel images must have matching shapes (except channels).\n"\
            "{} != {}".format( self.Probabilities.meta.shape, self.Superpixels.meta.shape )

        self._opCache.BlockShape.setValue( self.Superpixels.meta.shape )

    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here."
    
    def propagateDirty(self, slot, subindex, roi):
        pass # Nothing to do: input passes through child operators.

if __name__ == "__main__":
    import vigra
    
    from lazyflow.utility import blockwise_view

    # Superpixels are just (20,20,20) blocks, each with a unique value, 1-125
    superpixels = np.zeros( (100,100,100), dtype=np.uint32 )
    superpixel_block_view = blockwise_view( superpixels, (20,20,20) )
    assert superpixel_block_view.shape == (5,5,5,20,20,20)
    superpixel_block_view[:] = np.arange(1, 126).reshape( (5,5,5) )[..., None, None, None]
    
    superpixels = superpixels[...,None]
    assert superpixels.min() == 1
    assert superpixels.max() == 125

    # Make 3 random probability classes
    probabilities = np.random.random( superpixels.shape[:-1] + (3,) ).astype( np.float32 )
    probabilities = vigra.taggedView(probabilities, 'zyxc')

    superpixels = vigra.taggedView(superpixels, 'zyxc')
    
    from lazyflow.graph import Graph
    op = OpCachedMulticut(graph=Graph())
    op.Probabilities.setValue( probabilities )
    op.Superpixels.setValue( superpixels )
    assert op.Output.ready()
    result = op.Output[:].wait()
    assert (result == superpixels.view(np.ndarray)).all()
    
    print "DONE."
