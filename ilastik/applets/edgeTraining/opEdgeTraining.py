from itertools import izip, imap
import numpy as np

import networkx as nx
import skimage.segmentation

import vigra

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.roi import roiToSlice
from lazyflow.operators import OpCompressedCache, OpValueCache, OpBlockedArrayCache
from lazyflow.classifiers import ParallelVigraRfLazyflowClassifierFactory

from lazyflow.utility import edge_features
from lazyflow.utility.edge_features import compute_highlevel_edge_features

from ilastik.applets.edgeTraining.util import edge_decisions, relabel_volume_from_edge_decisions

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

    NaiveSegmentation = OutputSlot()

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

        self.opNaiveSegmentation = OpNaiveSegmentation(parent=self)
        self.opNaiveSegmentation.InputSuperpixels.connect( self.InputSuperpixels )
        self.opNaiveSegmentation.Rag.connect( self.opRagCache.Output )
        self.opNaiveSegmentation.EdgeProbabilities.connect( self.opEdgeProbabilitiesCache.Output )

        self.opNaiveSegmentationCache = OpBlockedArrayCache(parent=self)
        self.opNaiveSegmentationCache.CompressionEnabled.setValue(True)
        self.opNaiveSegmentationCache.Input.connect( self.opNaiveSegmentation.Output )

        self.Rag.connect( self.opRagCache.Output )
        self.EdgeProbabilities.connect( self.opEdgeProbabilitiesCache.Output )        
        self.EdgeProbabilitiesDict.connect( self.opEdgeProbabilitiesDictCache.Output )
        self.NaiveSegmentation.connect( self.opNaiveSegmentationCache.Output )

    def setupOutputs(self):
        assert self.InputSuperpixels.meta.dtype == np.uint32
        assert self.InputSuperpixels.meta.getAxisKeys()[-1] == 'c'

        self.RagSuperpixels.meta.assignFrom(self.InputSuperpixels.meta)
        self.RagSuperpixels.meta.display_mode = 'random-colortable'

        self.opNaiveSegmentationCache.outerBlockShape.setValue( self.InputSuperpixels.meta.shape )


    def execute(self, slot, subindex, roi, result):
        if slot is self.RagSuperpixels:
            self._executeRagSuperpixels(roi, result)
        else:
            assert False, "Unknown output slot: {}".format( slot )

    def _executeRagSuperpixels(self, roi, result):
        rag = self.opRagCache.Output.value
        result[:] = rag.label_img[...,None][roiToSlice(roi.start, roi.stop)]
        
    def propagateDirty(self, slot, subindex, roi):
        pass
    
    def trainFromGroundtruth(self):
        logger.info("Loading groundtruth...")
        gt_vol = self.GroundtruthSegmentation[:].wait()

        rag = self.opRagCache.Output.value
        edge_features = self.opEdgeFeaturesCache.Output.value

        logger.info("Computing edge decisions from groundtruth...")
        decisions = rag.edge_decisions_from_groundtruth(gt_vol, asdict=False)
        assert len(edge_features) == len(decisions)
        
        logger.info( "Training edge classifier with {} features and {} labels..."
                     .format( edge_features.shape[-1], len(decisions) ) )
        classifier_factory = ParallelVigraRfLazyflowClassifierFactory()
        classifier = classifier_factory.create_and_train( edge_features, decisions )
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
        superpixels = self.InputSuperpixels[:].wait()
        superpixels = vigra.taggedView( superpixels,
                                        self.InputSuperpixels.meta.axistags )
        superpixels = superpixels[...,0] # Drop channel
        

        logger.info("Creating RAG...")
        result[0] = edge_features.Rag(superpixels)

    def propagateDirty(self, slot, subindex, roi):
        self.Rag.setDirty()


class OpComputeEdgeFeatures(Operator):
    DEFAULT_FEATURES = ['edge_count', 'edge_sum', 'edge_mean', 'edge_variance',
                        'edge_quantiles_10', 'edge_quantiles_25', 'edge_quantiles_50', 'edge_quantiles_75', 'edge_quantiles_90',
                        'sp_count']
    FeatureNames = InputSlot(value=DEFAULT_FEATURES)
    VoxelData = InputSlot()
    Rag = InputSlot()
    EdgeFeatures = OutputSlot()
     
    def setupOutputs(self):
        assert self.VoxelData.meta.getAxisKeys()[-1] == 'c'
        self.EdgeFeatures.meta.shape = (1,)
        self.EdgeFeatures.meta.dtype = object
         
    def execute(self, slot, subindex, roi, result):
        rag = self.Rag.value
        feature_names = self.FeatureNames.value

        feature_data = []
        for c in range( self.VoxelData.meta.shape[-1] ):
            voxel_data = self.VoxelData[...,c:c+1].wait()
            voxel_data = vigra.taggedView(voxel_data, self.VoxelData.meta.axistags)
            voxel_data = voxel_data[...,0] # drop channel
            edge_features_df = rag.compute_highlevel_features(voxel_data, feature_names)
            del edge_features_df['id1']
            del edge_features_df['id2']
            feature_data.append( edge_features_df.values )

        # Concatenate features from all channels
        feature_data_array = np.concatenate(feature_data, axis=-1)
        result[0] = feature_data_array
 
    def propagateDirty(self, slot, subindex, roi):
        self.EdgeFeatures.setDirty()
     
class OpEdgeProbabilitiesDict(Operator):
    """
    A little utility operator to combine a RAG's edge_ids
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
        edge_ids = rag.edge_ids()
        result[0] = dict(izip(imap(tuple, edge_ids), edge_probabilities))

    def propagateDirty(self, slot, subindex, roi):
        self.EdgeProbabilitiesDict.setDirty()

class OpNaiveSegmentation(Operator):
    InputSuperpixels = InputSlot() # Just needed for slot metadata; our superpixels are taken from rag.
    Rag = InputSlot()
    EdgeProbabilities = InputSlot()
    Output = OutputSlot()

    def setupOutputs(self):
        self.Output.meta.assignFrom(self.InputSuperpixels.meta)
        self.Output.meta.display_mode = 'random-colortable'
        
    def execute(self, slot, subindex, roi, result):
        assert slot is self.Output
        edge_predictions = self.EdgeProbabilities.value
        rag = self.Rag.value
        sp_vol = rag.label_img[...,None][roiToSlice(roi.start, roi.stop)]
        sp_vol = vigra.taggedView(sp_vol, self.InputSuperpixels.meta.axistags)
        edge_labels = (edge_predictions > 0.5)
        
        result = vigra.taggedView(result, self.Output.meta.axistags)
        relabel_volume_from_edge_decisions(sp_vol[...,0], rag.edge_ids(), edge_labels, out=result[...,0])

    def propagateDirty(self, slot, subindex, roi):
        self.Output.setDirty()

