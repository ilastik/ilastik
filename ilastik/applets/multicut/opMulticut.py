import numpy as np

import skimage.segmentation

import opengm
import vigra.graphs

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.operators import OpCompressedCache

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
        assert self.Probabilities.meta.getAxisKeys()[-1] == 'c'
        assert self.Superpixels.meta.getAxisKeys()[-1] == 'c'
    
    def execute(self, slot, subindex, roi, result):
        sp_req = self.Superpixels[:]
        
        # Since result has same shape/dtype as superpixels,
        # we can use it as temporary storage here to save RAM.
        sp_req.writeInto(result)
        superpixels = sp_req.wait()[...,0] # Drop channel
        
        # Apparently we must ensure that the superpixel values are contiguous
        if superpixels.max() != len(np.unique(superpixels)):
            relabeled, fwd, rev = skimage.segmentation.relabel_sequential(superpixels)
            superpixels = relabeled.astype(np.uint32)
        
        # FIXME: Does vigra.graphs.regionAdjacencyGraph require superpixels starting at 0?
        superpixels -= 1 # start at 0??

        gridGraph = vigra.graphs.gridGraph(superpixels.shape)
        rag = vigra.graphs.regionAdjacencyGraph(gridGraph, superpixels) # TODO: This is expensive.  Would it be worthwhile to cache it?

        probabilities = self.Probabilities[:].wait()
        edge_features = self.compute_edge_features(rag, probabilities)
        edge_probabilities = self.compute_edge_probabilities(edge_features)
        
        agglomerated_labels = self.agglomerate_with_multicut(rag, edge_probabilities, self.Beta.value)
        result[:] = agglomerated_labels[...,None]
        result[:] += 1 # RAG labels are 0-based, but we want 1-based

    @classmethod
    def compute_edge_features(cls, rag, voxel_data):
        """
        voxel_data: Must include a channel axis, which must be the last axis
        
        For now this function doesn't do anything except accumulate the channels of the voxel data.
        """
        # First, transpose so that channel comes first.
        voxel_channels = voxel_data.transpose(-1, *range(voxel_data.ndim-1))

        edge_features = []
        gridGraph = vigra.graphs.gridGraph(voxel_channels[0].shape)

        # Iterate over channels
        for channel_data in voxel_channels:
            gridGraphEdgeIndicator = vigra.graphs.edgeFeaturesFromImage(gridGraph, channel_data)
            assert gridGraphEdgeIndicator.shape == channel_data.shape + (channel_data.ndim,)
            accumulated_edges = rag.accumulateEdgeFeatures(gridGraphEdgeIndicator)
            edge_features.append(accumulated_edges)

        return edge_features

    @classmethod
    def compute_edge_probabilities(cls, edge_features):
        # This function is just a stand-in for now.
        # It is just returns the first edge feature, so ideally it should just be a probability on it's own.
        assert len(edge_features) == 1, "This is just a stand-in"
        edge_probabilities = edge_features[0]
        return edge_probabilities
        
    @classmethod
    def agglomerate_with_multicut(cls, rag, edge_probabilities, beta):
        """
        rag: from vigra.graphs.regionAdjacencyGraph()
        edge_probabilities: Same format as from rag.accumulateEdgeFeatures(gridGraphEdgeIndicator)
                            That is, an array (rag.edgeNum,), in the same order as rag.uvIds()
                            Should indicate probability of each edge being ON.
        beta: The multicut 'beta' parameter (0.0 < beta < 1.0)
        
        Returns: A label image of the same shape as rag.labels, type uint32
        """
        p1 = edge_probabilities # Edge ON
        p1 = np.clip(p1, 0.001, 0.999)
        p0 = 1.0 - p1 # Edge OFF
        assert p0.shape == p1.shape == (rag.edgeNum,)

        nVar = rag.nodeNum
        gm = opengm.gm( np.ones(nVar)*nVar )

        uvIds = rag.uvIds()
        assert uvIds.shape == (rag.edgeNum, 2)
        uvIds = np.sort( uvIds, axis=1 )
        
        w = np.log(p0/p1) + np.log( (1-beta)/(beta) )
        pf = opengm.pottsFunctions( [nVar,nVar], np.array([0]), w )
        fids = gm.addFunctions( pf )
        gm.addFactors( fids, uvIds )

        inf = opengm.inference.Multicut( gm )
        ret = inf.infer( inf.verboseVisitor() )
        arg = inf.arg().astype('uint32')
        agglomerated_labels = rag.projectLabelsToGridGraph(arg)
        assert agglomerated_labels.shape == rag.labels.shape
        return agglomerated_labels

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
