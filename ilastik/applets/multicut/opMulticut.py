import warnings
import numpy as np

import opengm

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.roi import roiToSlice
from lazyflow.operators import OpCompressedCache, OpValueCache

class OpMulticut(Operator):
    Beta = InputSlot(value=0.1)
    Rag = InputSlot() # value slot.  Rag object.
    Superpixels = InputSlot()
    EdgeProbabilities = InputSlot()
    EdgeProbabilitiesDict = InputSlot() # A dict of id_pair -> probabilities
    RawData = InputSlot(optional=True) # Used by the GUI for display only
    
    Output = OutputSlot() # Pixelwise output (not RAG, etc.)
    
    def __init__(self, *args, **kwargs):
        super( OpMulticut, self ).__init__(*args, **kwargs)

        self.opMulticutAgglomerator = OpMulticutAgglomerator(parent=self)
        self.opMulticutAgglomerator.Superpixels.connect( self.Superpixels )
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
        rag: lazyflow.edge_features.Rag
        
        edge_probabilities: 1D array, same order as rag.edge_ids().
                            Should indicate probability of each edge being ON.
        
        beta: The multicut 'beta' parameter (0.0 < beta < 1.0)
        
        Returns: A label image of the same shape as rag.label_img, type uint32
        """
        num_edges = rag.num_edges()
        edge_ids = rag.edge_ids()
        assert edge_ids.shape == (num_edges, 2)

        p1 = edge_probabilities # Edge ON
        p1 = np.clip(p1, 0.001, 0.999)
        p0 = 1.0 - p1 # Edge OFF
        assert p0.shape == p1.shape == (num_edges,)

        # The Rag is allowed to contain non-consecutive superpixel labels
        # But for OpenGM, we require nVar > max_id
        # Therefore, use max_sp_id(), not num_sp()
        nVar = rag.max_sp_id()+1
        if rag.num_sp() != rag.max_sp_id()+1:
            warnings.warn( "Superpixel IDs are not consective. GM will contain excess variables to fill the gaps."
                           " (num_sp = {}, max_sp_id = {})".format( rag.num_sp(), rag.max_sp_id() ) )
        
        gm = opengm.gm( np.ones(nVar)*nVar )
        
        w = np.log(p0/p1) + np.log( (1-beta)/(beta) )
        pf = opengm.pottsFunctions( [nVar,nVar], np.array([0]), w )
        fids = gm.addFunctions( pf )
        gm.addFactors( fids, edge_ids )

        inf = opengm.inference.Multicut( gm )
        ret = inf.infer( inf.verboseVisitor() )
        if ret.name != "NORMAL":
            raise RuntimeError("OpenGM inference failed with status: {}".format( ret.name ))
        mapping_index_array = inf.arg().astype(np.uint32)
        agglomerated_labels = mapping_index_array[rag.label_img]
        assert agglomerated_labels.shape == rag.label_img.shape
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
