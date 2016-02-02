import numpy as np

import skimage.segmentation

import opengm
import vigra.graphs

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.roi import roiToSlice
from lazyflow.operators import OpCompressedCache, OpValueCache

class OpMulticut(Operator):
    Beta = InputSlot(value=0.1)
    VoxelData = InputSlot()
    InputSuperpixels = InputSlot()
    RawData = InputSlot(optional=True) # Used by the GUI for display only
    
    Output = OutputSlot() # Pixelwise output (not RAG, etc.)
    EdgeProbabilitiesDict = OutputSlot() # A dict of id_pair -> probabilities

    RagSuperpixels = OutputSlot() # Rag can't necessarily use the input superpixels,
                                  # since it needs consecutive IDs, starting at 0,
                                  # so it relabels the superpixels.  This is the relabeled version.
    
    def __init__(self, *args, **kwargs):
        super( OpMulticut, self ).__init__(*args, **kwargs)

        self.opCreateRag = OpCreateRag(parent=self)
        self.opCreateRag.InputSuperpixels.connect( self.InputSuperpixels )
        
        self.opRagCache = OpValueCache(parent=self)
        self.opRagCache.Input.connect( self.opCreateRag.Rag )

        self.opComputeEdgeFeatures = OpComputeEdgeFeatures(parent=self)
        self.opComputeEdgeFeatures.VoxelData.connect( self.VoxelData )
        self.opComputeEdgeFeatures.Rag.connect( self.opRagCache.Output )
        
        self.opEdgeFeaturesCache = OpValueCache(parent=self)
        self.opEdgeFeaturesCache.Input.connect( self.opComputeEdgeFeatures.EdgeFeatures )
        
        self.opComputeEdgeProbabilities = OpComputeEdgeProbabilities(parent=self)
        self.opComputeEdgeProbabilities.EdgeFeatures.connect( self.opEdgeFeaturesCache.Output )
        
        self.opEdgeProbabilitiesCache = OpValueCache(parent=self)
        self.opEdgeProbabilitiesCache.Input.connect( self.opComputeEdgeProbabilities.EdgeProbabilities )
        
        self.opMulticutAgglomerator = OpMulticutAgglomerator(parent=self)
        self.opMulticutAgglomerator.InputSuperpixels.connect( self.InputSuperpixels )
        self.opMulticutAgglomerator.Beta.connect( self.Beta )
        self.opMulticutAgglomerator.Rag.connect( self.opRagCache.Output )
        self.opMulticutAgglomerator.EdgeProbabilities.connect( self.opEdgeProbabilitiesCache.Output )

        self.opSegmentationCache = OpCompressedCache(parent=self)
        self.opSegmentationCache.Input.connect( self.opMulticutAgglomerator.Output )
        self.Output.connect( self.opSegmentationCache.Output )
        
        self.opEdgeProbabilitiesDict = OpEdgeProbabilitiesDict(parent=self)
        self.opEdgeProbabilitiesDict.Rag.connect( self.opRagCache.Output )
        self.opEdgeProbabilitiesDict.EdgeProbabilities.connect( self.opEdgeProbabilitiesCache.Output )
        
        self.opEdgeProbabilitiesDictCache = OpValueCache(parent=self)
        self.opEdgeProbabilitiesDictCache.Input.connect( self.opEdgeProbabilitiesDict.EdgeProbabilitiesDict )
        
        self.EdgeProbabilitiesDict.connect( self.opEdgeProbabilitiesDictCache.Output )
    
    def setupOutputs(self):
        assert self.InputSuperpixels.meta.dtype == np.uint32
        assert self.InputSuperpixels.meta.getAxisKeys()[-1] == 'c'

        self.RagSuperpixels.meta.assignFrom(self.InputSuperpixels.meta)
        self.RagSuperpixels.meta.display_mode = 'random-colortable'
        
    def execute(self, slot, subindex, roi, result):
        if slot == self.RagSuperpixels:
            self._executeRagSuperpixels(roi, result)
        else:
            assert False, "Unknown output slot: {}".format( slot )

    def _executeRagSuperpixels(self, roi, result):
        rag = self.opRagCache.Output.value
        result[:] = rag.labels[...,None][roiToSlice(roi.start, roi.stop)]
        
    def propagateDirty(self, slot, subindex, roi):
        pass

class OpCreateRag(Operator):
    InputSuperpixels = InputSlot()
    Rag = OutputSlot()
    
    def setupOutputs(self):
        assert self.InputSuperpixels.meta.dtype == np.uint32
        assert self.InputSuperpixels.meta.getAxisKeys()[-1] == 'c'
        self.Rag.meta.shape = (1,)
        self.Rag.meta.dtype = object
    
    def execute(self, slot, subindex, roi, result):
        superpixels = self.InputSuperpixels[:].wait()[...,0] # Drop channel
        
        # Apparently we must ensure that the superpixel values are contiguous
        if superpixels.max() != len(np.unique(superpixels)):
            relabeled, fwd, rev = skimage.segmentation.relabel_sequential(superpixels)
            superpixels = relabeled.astype(np.uint32)
        
        # FIXME: Does vigra.graphs.regionAdjacencyGraph require superpixels starting at 0?
        superpixels -= 1 # start at 0??

        gridGraph = vigra.graphs.gridGraph(superpixels.shape)
        rag = vigra.graphs.regionAdjacencyGraph(gridGraph, superpixels)
        result[0] = rag

    def propagateDirty(self, slot, subindex, roi):
        self.Rag.setDirty()

class OpComputeEdgeFeatures(Operator):
    VoxelData = InputSlot()
    Rag = InputSlot()
    EdgeFeatures = OutputSlot()
    
    def setupOutputs(self):
        assert self.VoxelData.meta.getAxisKeys()[-1] == 'c'
        self.EdgeFeatures.meta.shape = (1,)
        self.EdgeFeatures.meta.dtype = object
        
    def execute(self, slot, subindex, roi, result):
        voxel_req = self.VoxelData[:]
        voxel_req.submit()

        rag = self.Rag.value
        voxel_data = voxel_req.wait()

        edge_features = self.compute_edge_features(rag, voxel_data)
        result[0] = edge_features

    def propagateDirty(self, slot, subindex, roi):
        self.EdgeFeatures.setDirty()
    
    @classmethod
    def compute_edge_features(cls, rag, voxel_data):
        """
        voxel_data: Must include a channel axis, which must be the last axis
        
        For now this function doesn't do anything except accumulate the channels of the voxel data.
        """
        # First, transpose so that channel comes first.
        voxel_channels = voxel_data.transpose(voxel_data.ndim-1, *range(voxel_data.ndim-1))

        edge_features = []
        gridGraph = vigra.graphs.gridGraph(voxel_channels[0].shape)

        # Iterate over channels
        for channel_data in voxel_channels:
            gridGraphEdgeIndicator = vigra.graphs.edgeFeaturesFromImage(gridGraph, channel_data)
            assert gridGraphEdgeIndicator.shape == channel_data.shape + (channel_data.ndim,)
            accumulated_edges = rag.accumulateEdgeFeatures(gridGraphEdgeIndicator)
            edge_features.append(accumulated_edges)

        return edge_features

class OpComputeEdgeProbabilities(Operator):
    EdgeFeatures = InputSlot()
    EdgeProbabilities = OutputSlot()
    
    def setupOutputs(self):
        self.EdgeProbabilities.meta.shape = (1,)
        self.EdgeProbabilities.meta.dtype = object

    def execute(self, slot, subindex, roi, result):
        edge_features = self.EdgeFeatures.value
        result[0] = self.compute_edge_probabilities(edge_features)
    
    def propagateDirty(self, slot, subindex, roi):
        self.EdgeProbabilities.setDirty()

    @classmethod
    def compute_edge_probabilities(cls, edge_features):
        # This function is just a stand-in for now.
        # It is just returns the first edge feature, so ideally it should just be a probability on it's own.
        edge_probabilities = edge_features[0]
        return edge_probabilities

class OpMulticutAgglomerator(Operator):
    InputSuperpixels = InputSlot() # Just needed for slot metadata
    Beta = InputSlot()
    Rag = InputSlot()
    EdgeProbabilities = InputSlot()
    Output = OutputSlot()
    
    def setupOutputs(self):
        self.Output.meta.assignFrom(self.InputSuperpixels.meta)
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

class OpEdgeProbabilitiesDict(Operator):
    """
    A little utility operator to combine a RAG's uvIds
    with an array of edge probabilities into a dict of id_pair -> probability 
    """
    Rag = InputSlot()
    EdgeProbabilities = InputSlot()
    EdgeProbabilitiesDict = OutputSlot()
    
    def setupOutputs(self):
        self.EdgeProbabilitiesDict.meta.shape = (1,)
        self.EdgeProbabilitiesDict.meta.dtype = object

    def execute(self, slot, subindex, roi, result):
        edge_probabilities = self.EdgeProbabilities.value
        rag = self.Rag.value
        uvIds = rag.uvIds()
        assert uvIds.shape == (rag.edgeNum, 2)
        uvIds = np.sort( uvIds, axis=1 )

        id_pairs = map(tuple, uvIds)
        result[0] = dict(zip(id_pairs, edge_probabilities))

    def propagateDirty(self, slot, subindex, roi):
        self.EdgeProbabilitiesDict.setDirty()

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
