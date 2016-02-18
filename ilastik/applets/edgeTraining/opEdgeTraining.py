import numpy as np

import vigra.graphs
import skimage.segmentation

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.roi import roiToSlice
from lazyflow.operators import OpCompressedCache, OpValueCache
from lazyflow.classifiers import ParallelVigraRfLazyflowClassifierFactory

from ilastik.applets.edgeTraining.util import edge_decisions

import logging
logger = logging.getLogger(__name__)

class OpEdgeTraining(Operator):
    VoxelData = InputSlot()
    InputSuperpixels = InputSlot()
    GroundtruthSegmentation = InputSlot(optional=True)
    #EdgeLabels = InputSlot(optional=True)
    RawData = InputSlot(optional=True) # Used by the GUI for display only
    
    EdgeProbabilities = OutputSlot()
    EdgeProbabilitiesDict = OutputSlot() # A dict of id_pair -> probabilities

    Rag = OutputSlot()
    RagSuperpixels = OutputSlot() # The rag can't necessarily use the input superpixels
                                  # (since it needs consecutive IDs, starting at 0),
                                  # so we relabel the superpixels.  This is the relabeled version.

    def __init__(self, *args, **kwargs):
        super( OpEdgeTraining, self ).__init__(*args, **kwargs)

        self.opCreateRag = OpCreateRag(parent=self)
        self.opCreateRag.InputSuperpixels.connect( self.InputSuperpixels )
        
        self.opRagCache = OpValueCache(parent=self)
        self.opRagCache.Input.connect( self.opCreateRag.Rag )

        self.opComputeEdgeFeatures = OpComputeEdgeFeatures(parent=self)
        self.opComputeEdgeFeatures.VoxelData.connect( self.VoxelData )
        self.opComputeEdgeFeatures.Rag.connect( self.opRagCache.Output )
        
        self.opEdgeFeaturesCache = OpValueCache(parent=self)
        self.opEdgeFeaturesCache.Input.connect( self.opComputeEdgeFeatures.EdgeFeatures )

        # classifier cache input is set after training.
        self.opClassifierCache = OpValueCache(parent=self)
        
        self.opPredictEdgeProbabilities = OpPredictEdgeProbabilities(parent=self)
        self.opPredictEdgeProbabilities.EdgeClassifier.connect( self.opClassifierCache.Output )
        self.opPredictEdgeProbabilities.EdgeFeatures.connect( self.opEdgeFeaturesCache.Output )
        
        self.opEdgeProbabilitiesCache = OpValueCache(parent=self)
        self.opEdgeProbabilitiesCache.Input.connect( self.opPredictEdgeProbabilities.EdgeProbabilities )

        self.opEdgeProbabilitiesDict = OpEdgeProbabilitiesDict(parent=self)
        self.opEdgeProbabilitiesDict.Rag.connect( self.opRagCache.Output )
        self.opEdgeProbabilitiesDict.EdgeProbabilities.connect( self.opEdgeProbabilitiesCache.Output )
        
        self.opEdgeProbabilitiesDictCache = OpValueCache(parent=self)
        self.opEdgeProbabilitiesDictCache.Input.connect( self.opEdgeProbabilitiesDict.EdgeProbabilitiesDict )

        self.Rag.connect( self.opRagCache.Output )
        self.EdgeProbabilities.connect( self.opPredictEdgeProbabilities.EdgeProbabilities )        
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
    
    def trainFromGroundtruth(self):
        logger.info("Loading groundtruth...")
        gt_vol = self.GroundtruthSegmentation[:].wait()

        logger.info("Loading superpixels...")
        sp_vol = self.RagSuperpixels[:].wait()

        logger.info("Computing edge decisions...")
        edge_label_dict = edge_decisions(sp_vol, gt_vol)

        # TODO: optimize with pandas?
        rag = self.opRagCache.Output.value
        uv_ids = rag.uvIds()
        uv_ids.sort(axis=1)
        edge_label_array = np.zeros( (uv_ids.shape[0],) )
        for i, (id1, id2) in enumerate(uv_ids):
            edge_label_array[i] = int(edge_label_dict[(id1,id2)])

        edge_features = self.opEdgeFeaturesCache.Output.value
        
        assert len(edge_features) == len(edge_label_array)
        logger.info("Training edge classifier...")
        classifier_factory = ParallelVigraRfLazyflowClassifierFactory()
        classifier = classifier_factory.create_and_train( edge_features, edge_label_array )
        self.opClassifierCache.Input.setValue( classifier )

class OpPredictEdgeProbabilities(Operator):
    EdgeClassifier = InputSlot()
    EdgeFeatures = InputSlot()
    EdgeProbabilities = OutputSlot()
    
    def setupOutputs(self):
        self.EdgeProbabilities.meta.shape = (1,)
        self.EdgeProbabilities.meta.dtype = object

    def execute(self, slot, subindex, roi, result):
        edge_features = self.EdgeFeatures.value
        classifier = self.EdgeClassifier.value
        
        logger.info("Predicting edge probabilities...")
        probabilities = classifier.predict_probabilities(edge_features)[:,1]
        assert len(probabilities) == len(edge_features)
        result[0] = probabilities
    
    def propagateDirty(self, slot, subindex, roi):
        self.EdgeProbabilities.setDirty()

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
            logger.info("Relabeling superpixels...")
            relabeled, fwd, rev = skimage.segmentation.relabel_sequential(superpixels)
            superpixels = relabeled.astype(np.uint32)
        
        # FIXME: Does vigra.graphs.regionAdjacencyGraph require superpixels starting at 0?
        superpixels -= 1 # start at 0??

        logger.info("Creating RAG...")
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

        logger.info("Computing edge features...")
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

        return np.concatenate(map(lambda a: a[:, None], edge_features), axis=1)

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

        logger.info("Converting edge probabilities to dict...")
        uvIds = rag.uvIds()
        assert uvIds.shape == (rag.edgeNum, 2)
        uvIds = np.sort( uvIds, axis=1 )

        id_pairs = map(tuple, uvIds)
        result[0] = dict(zip(id_pairs, edge_probabilities))

    def propagateDirty(self, slot, subindex, roi):
        self.EdgeProbabilitiesDict.setDirty()

