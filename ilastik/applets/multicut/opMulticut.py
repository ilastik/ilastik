import numpy as np

import skimage.segmentation

import opengm
import vigra.graphs

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.operators import OpCompressedCache

PROBABILITY_EDGE_CHANNEL = 0

class OpMulticut(Operator):
    Beta = InputSlot(value=0.1)
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
        pmap_req = self.Probabilities[..., PROBABILITY_EDGE_CHANNEL]
        sp_req = self.Superpixels[:]

        pmap_req.submit()
        sp_req.submit()
        
        probabilities = pmap_req.wait()[...,0]
        assert probabilities.shape == self.Probabilities.meta.shape[:-1]

        superpixels = sp_req.wait()[...,0]
        
        # Apparently we must ensure that the superpixel values are contiguous
        if superpixels.max() != len(np.unique(superpixels)):
            relabeled, fwd, rev = skimage.segmentation.relabel_sequential(superpixels)
            superpixels = relabeled.astype(np.uint32)
        
        # FIXME: Does vigra.graphs.regionAdjacencyGraph require superpixels starting at 0?
        superpixels -= 1 # start at 0??

        gridGraph = vigra.graphs.gridGraph(probabilities.shape)

        # get region adjacency graph from super-pixel labels
        rag = vigra.graphs.regionAdjacencyGraph(gridGraph, superpixels)
        gridGraphEdgeIndicator = vigra.graphs.edgeFeaturesFromImage(gridGraph, probabilities)

        p0 = rag.accumulateEdgeFeatures(gridGraphEdgeIndicator) / 255.0
        p0 = np.clip(p0, 0.001, 0.999)
        p1 = 1.0 - p0

        nVar = rag.nodeNum
        gm = opengm.gm( np.ones(nVar)*nVar )

        uvIds = rag.uvIds()
        uvIds = np.sort( uvIds, axis=1 )
        
        beta = self.Beta.value
        w = np.log(p0/p1) + np.log( (1-beta)/(beta) )
        pf = opengm.pottsFunctions( [nVar,nVar], np.array([0]), w )
        fids = gm.addFunctions( pf )
        gm.addFactors( fids, uvIds )

        inf = opengm.inference.Multicut( gm )
        ret = inf.infer( inf.verboseVisitor() )
        arg = inf.arg().astype('uint32')
        result[:] = rag.projectLabelsToGridGraph(arg)[...,None] + 1 # RAG labels are 0-based, but we want 1-based

    def propagateDirty(self, slot, subindex, roi):
        # Everything is dirty...
        self.Output.setDirty()

class OpCachedMulticut(Operator):
    """
    A drop-in replacement for OpMulticut, except that the output is cached,
    and therefore the entire output is always requested at once.
    (It would be a mistake to ask OpMulticut for a single slice of output.)
    """
    Beta = InputSlot(value=0.1)
    RawData = InputSlot(optional=True) # Used by the GUI for display only
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
        self._opMulticut.Beta.connect( self.Beta )
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
    
    assert result.min() == 1
    
    print "DONE."
