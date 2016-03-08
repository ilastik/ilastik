from itertools import izip, imap
from functools import partial
import numpy as np

import networkx as nx
import skimage.segmentation

import vigra

import ilastikrag

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.roi import roiToSlice
from lazyflow.operators import OpValueCache, OpBlockedArrayCache
from lazyflow.classifiers import ParallelVigraRfLazyflowClassifierFactory

from ilastik.applets.base.applet import DatasetConstraintError
from ilastik.utility.operatorSubView import OperatorSubView
from ilastik.utility import OpMultiLaneWrapper

from ilastik.applets.edgeTraining.util import edge_decisions, relabel_volume_from_edge_decisions

import logging
logger = logging.getLogger(__name__)

class OpEdgeTraining(Operator):
    VoxelData = InputSlot(level=1)
    Superpixels = InputSlot(level=1)
    GroundtruthSegmentation = InputSlot(level=1, optional=True)
    #EdgeLabels = InputSlot(optional=True)
    RawData = InputSlot(level=1, optional=True) # Used by the GUI for display only
    
    EdgeProbabilities = OutputSlot(level=1)
    EdgeProbabilitiesDict = OutputSlot(level=1) # A dict of id_pair -> probabilities

    Rag = OutputSlot(level=1)

    NaiveSegmentation = OutputSlot(level=1)

    def __init__(self, *args, **kwargs):
        super( OpEdgeTraining, self ).__init__(*args, **kwargs)

        self.opCreateRag = OpMultiLaneWrapper( OpCreateRag, parent=self )
        self.opCreateRag.Superpixels.connect( self.Superpixels )
        
        self.opRagCache = OpMultiLaneWrapper( OpValueCache, parent=self )
        self.opRagCache.Input.connect( self.opCreateRag.Rag )
        
        self.opComputeEdgeFeatures = OpMultiLaneWrapper( OpComputeEdgeFeatures, parent=self )
        self.opComputeEdgeFeatures.VoxelData.connect( self.VoxelData )
        self.opComputeEdgeFeatures.Rag.connect( self.opRagCache.Output )
        
        self.opEdgeFeaturesCache = OpMultiLaneWrapper( OpValueCache, parent=self )
        self.opEdgeFeaturesCache.Input.connect( self.opComputeEdgeFeatures.EdgeFeatures )

        # classifier cache input is set after training.
        self.opClassifierCache = OpValueCache(parent=self)
        
        self.opPredictEdgeProbabilities = OpMultiLaneWrapper( OpPredictEdgeProbabilities, parent=self )
        self.opPredictEdgeProbabilities.EdgeClassifier.connect( self.opClassifierCache.Output )
        self.opPredictEdgeProbabilities.EdgeFeatures.connect( self.opEdgeFeaturesCache.Output )
        
        self.opEdgeProbabilitiesCache = OpMultiLaneWrapper( OpValueCache, parent=self )
        self.opEdgeProbabilitiesCache.Input.connect( self.opPredictEdgeProbabilities.EdgeProbabilities )

        self.opEdgeProbabilitiesDict = OpMultiLaneWrapper( OpEdgeProbabilitiesDict, parent=self )
        self.opEdgeProbabilitiesDict.Rag.connect( self.opRagCache.Output )
        self.opEdgeProbabilitiesDict.EdgeProbabilities.connect( self.opEdgeProbabilitiesCache.Output )
        
        self.opEdgeProbabilitiesDictCache = OpMultiLaneWrapper( OpValueCache, parent=self )
        self.opEdgeProbabilitiesDictCache.Input.connect( self.opEdgeProbabilitiesDict.EdgeProbabilitiesDict )

        self.opNaiveSegmentation = OpMultiLaneWrapper( OpNaiveSegmentation, parent=self )
        self.opNaiveSegmentation.Superpixels.connect( self.Superpixels )
        self.opNaiveSegmentation.Rag.connect( self.opRagCache.Output )
        self.opNaiveSegmentation.EdgeProbabilities.connect( self.opEdgeProbabilitiesCache.Output )

        self.opNaiveSegmentationCache = OpMultiLaneWrapper( OpBlockedArrayCache, parent=self, broadcastingSlotNames=['CompressionEnabled'] )
        self.opNaiveSegmentationCache.CompressionEnabled.setValue(True)
        self.opNaiveSegmentationCache.Input.connect( self.opNaiveSegmentation.Output )

        self.Rag.connect( self.opRagCache.Output )
        self.EdgeProbabilities.connect( self.opEdgeProbabilitiesCache.Output )
        self.EdgeProbabilitiesDict.connect( self.opEdgeProbabilitiesDictCache.Output )
        self.NaiveSegmentation.connect( self.opNaiveSegmentationCache.Output )

        # All input multi-slots should be kept in sync
        # Output multi-slots will auto-sync via the graph
        multiInputs = filter( lambda s: s.level >= 1, self.inputs.values() )
        for s1 in multiInputs:
            for s2 in multiInputs:
                if s1 != s2:
                    def insertSlot( a, b, position, finalsize ):
                        a.insertSlot(position, finalsize)
                    s1.notifyInserted( partial(insertSlot, s2 ) )
                    
                    def removeSlot( a, b, position, finalsize ):
                        a.removeSlot(position, finalsize)
                    s1.notifyRemoved( partial(removeSlot, s2 ) )

    def setupOutputs(self):
        for sp_slot, seg_cache_blockshape_slot in zip(self.Superpixels, self.opNaiveSegmentationCache.outerBlockShape):
            assert sp_slot.meta.dtype == np.uint32
            assert sp_slot.meta.getAxisKeys()[-1] == 'c'
            seg_cache_blockshape_slot.setValue( sp_slot.meta.shape )

    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here, but requesting slot: {}".format( slot )

    def propagateDirty(self, slot, subindex, roi):
        pass
    
    def trainFromGroundtruth(self):
        all_edge_features = []
        all_edge_decisions = []

        for lane_index in range( len(self.GroundtruthSegmentation) ):
            logger.info("Loading groundtruth...")
            gt_vol = self.GroundtruthSegmentation[lane_index][:].wait()
            gt_vol = vigra.taggedView(gt_vol, self.GroundtruthSegmentation.meta.axistags)
            gt_vol = gt_vol.dropChannelAxis()
    
            rag = self.opRagCache.Output[lane_index].value
            edge_features = self.opEdgeFeaturesCache.Output[lane_index].value
    
            logger.info("Computing edge decisions from groundtruth...")
            decisions = rag.edge_decisions_from_groundtruth(gt_vol, asdict=False)
            assert len(edge_features) == len(decisions)

            all_edge_features.append(edge_features)
            all_edge_decisions.append(decisions)
            
        logger.info( "Training edge classifier with {} features and {} labels..."
                     .format( edge_features.shape[-1], len(decisions) ) )

        combined_features = np.concatenate(all_edge_features)
        combined_decisions = np.concatenate(all_edge_decisions)

        classifier_factory = ParallelVigraRfLazyflowClassifierFactory()
        classifier = classifier_factory.create_and_train( combined_features, combined_decisions )
        self.opClassifierCache.Input.setValue( classifier )

    def addLane(self, laneIndex):
        numLanes = len(self.VoxelData)
        assert numLanes == laneIndex, "Image lanes must be appended."        
        self.VoxelData.resize(numLanes+1)
        
    def removeLane(self, laneIndex, finalLength):
        self.VoxelData.removeSlot(laneIndex, finalLength)

    def getLane(self, laneIndex):
        return OperatorSubView(self, laneIndex)


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
    Superpixels = InputSlot()
    Rag = OutputSlot()
    
    def setupOutputs(self):
        assert self.Superpixels.meta.dtype == np.uint32
        assert self.Superpixels.meta.getAxisKeys()[-1] == 'c'
        self.Rag.meta.shape = (1,)
        self.Rag.meta.dtype = object
    
    def execute(self, slot, subindex, roi, result):
        superpixels = self.Superpixels[:].wait()
        superpixels = vigra.taggedView( superpixels,
                                        self.Superpixels.meta.axistags )
        superpixels = superpixels.dropChannelAxis()

        logger.info("Creating RAG...")
        result[0] = ilastikrag.Rag(superpixels)

    def propagateDirty(self, slot, subindex, roi):
        self.Rag.setDirty()


class OpComputeEdgeFeatures(Operator):
    DEFAULT_FEATURES = ['standard_edge_count',
                        'standard_edge_sum',
                        'standard_edge_mean',
                        'standard_edge_variance',
                        'standard_edge_quantiles_10',
                        'standard_edge_quantiles_25',
                        'standard_edge_quantiles_50',
                        'standard_edge_quantiles_75',
                        'standard_edge_quantiles_90',
                        'standard_sp_count']
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
            edge_features_df = rag.compute_features(voxel_data, feature_names)
            del edge_features_df['sp1']
            del edge_features_df['sp2']
            
            feature_array = edge_features_df.values
            feature_data.append( feature_array )

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
    Superpixels = InputSlot() # Just needed for slot metadata; our superpixels are taken from rag.
    Rag = InputSlot()
    EdgeProbabilities = InputSlot()
    Output = OutputSlot()

    def setupOutputs(self):
        self.Output.meta.assignFrom(self.Superpixels.meta)
        self.Output.meta.display_mode = 'random-colortable'
        
    def execute(self, slot, subindex, roi, result):
        assert slot is self.Output
        edge_predictions = self.EdgeProbabilities.value
        rag = self.Rag.value
        sp_vol = rag.label_img[...,None][roiToSlice(roi.start, roi.stop)]
        sp_vol = vigra.taggedView(sp_vol, self.Superpixels.meta.axistags)
        edge_decisions = (edge_predictions > 0.5)
        
        result = vigra.taggedView(result, self.Output.meta.axistags)
        rag.naive_segmentation_from_edge_decisions(edge_decisions, out=result[...,0])

    def propagateDirty(self, slot, subindex, roi):
        self.Output.setDirty()

