import numpy as np

import skimage.segmentation

import opengm
import vigra.graphs

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.roi import roiToSlice
from lazyflow.operators import OpCompressedCache, OpValueCache

class OpMulticut(Operator):
    Beta = InputSlot(value=0.1)
    Rag = InputSlot() # value slot.  Rag object.
    RagSuperpixels = InputSlot() # Must be the superpixels used for the RAG (i.e. consecutive labels, starting at 0)
    EdgeProbabilities = InputSlot()
    EdgeProbabilitiesDict = InputSlot() # A dict of id_pair -> probabilities
    RawData = InputSlot(optional=True) # Used by the GUI for display only
    
    Output = OutputSlot() # Pixelwise output (not RAG, etc.)
    
    def __init__(self, *args, **kwargs):
        super( OpMulticut, self ).__init__(*args, **kwargs)

        self.opMulticutAgglomerator = OpMulticutAgglomerator(parent=self)
        self.opMulticutAgglomerator.Superpixels.connect( self.RagSuperpixels )
        self.opMulticutAgglomerator.Beta.connect( self.Beta )
        self.opMulticutAgglomerator.Rag.connect( self.Rag )
        self.opMulticutAgglomerator.EdgeProbabilities.connect( self.EdgeProbabilities )

        self.opSegmentationCache = OpCompressedCache(parent=self)
        self.opSegmentationCache.Input.connect( self.opMulticutAgglomerator.Output )
        self.Output.connect( self.opSegmentationCache.Output )

    def setupOutputs(self):
        pass
    
    def execute(self, slot, subindex, roi, result):
        assert False, "Unknown or unconnected output slot: {}".format( slot )

    def propagateDirty(self, slot, subindex, roi):
        pass

class OpMulticutAgglomerator(Operator):
    Superpixels = InputSlot() # Just needed for slot metadata
    Beta = InputSlot()
    Rag = InputSlot()
    EdgeProbabilities = InputSlot()
    Output = OutputSlot()
    
    def setupOutputs(self):
        self.Output.meta.assignFrom(self.Superpixels.meta)
        self.Output.meta.display_mode = 'random-colortable'

    def execute(self, slot, subindex, roi, result):
        edge_probabilities = self.EdgeProbabilities.value
        rag = self.Rag.value
        beta = self.Beta.value
        agglomerated_labels = self.agglomerate_with_multicut(rag, edge_probabilities, beta)
        result[:] = agglomerated_labels[...,None]
        
        # FIXME: Is it okay to produce 0-based supervoxels?
        #result[:] += 1 # RAG labels are 0-based, but we want 1-based

    def propagateDirty(self, slot, subindex, roi):
        self.Output.setDirty()
        
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
        uvIds.sort(axis=1)
        
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
    op = OpMulticut(graph=Graph())
    op.VoxelData.setValue( probabilities )
    op.InputSuperpixels.setValue( superpixels )
    assert op.Output.ready()
    result = op.Output[:].wait()
    
    assert result.min() == 0
    
    print "DONE."
