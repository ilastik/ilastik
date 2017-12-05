from builtins import range

from functools import partial

import numpy as np
import pandas as pd
import networkx as nx
import vigra

import ilastikrag

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.roi import roiToSlice
from lazyflow.operators import OpValueCache, OpBlockedArrayCache
from lazyflow.classifiers import ParallelVigraRfLazyflowClassifierFactory

from ilastik.applets.base.applet import DatasetConstraintError
from ilastik.utility.operatorSubView import OperatorSubView
from ilastik.utility import OpMultiLaneWrapper

import logging
logger = logging.getLogger(__name__)

class OpEdgeTraining(Operator):
    # Shared across lanes
    DEFAULT_FEATURES = { "Grayscale": ['standard_edge_mean'] }
    FeatureNames = InputSlot(value=DEFAULT_FEATURES)
    FreezeClassifier = InputSlot(value=True)

    # Lane-wise
    EdgeLabelsDict = InputSlot(level=1, value={})
    VoxelData = InputSlot(level=1)
    Superpixels = InputSlot(level=1)
    GroundtruthSegmentation = InputSlot(level=1, optional=True)
    RawData = InputSlot(level=1, optional=True) # Used by the GUI for display only
    
    Rag = OutputSlot(level=1)
    EdgeProbabilities = OutputSlot(level=1)
    EdgeProbabilitiesDict = OutputSlot(level=1) # A dict of id_pair -> probabilities
    NaiveSegmentation = OutputSlot(level=1)

    def __init__(self, *args, **kwargs):
        super( OpEdgeTraining, self ).__init__(*args, **kwargs)

        self.opCreateRag = OpMultiLaneWrapper( OpCreateRag, parent=self )
        self.opCreateRag.Superpixels.connect( self.Superpixels )
        
        self.opRagCache = OpMultiLaneWrapper( OpValueCache, parent=self, broadcastingSlotNames=['fixAtCurrent'] )
        self.opRagCache.Input.connect( self.opCreateRag.Rag )
        self.opRagCache.name = 'opRagCache'
        
        self.opComputeEdgeFeatures = OpMultiLaneWrapper( OpComputeEdgeFeatures, parent=self, broadcastingSlotNames=['FeatureNames'] )
        self.opComputeEdgeFeatures.FeatureNames.connect( self.FeatureNames )
        self.opComputeEdgeFeatures.VoxelData.connect( self.VoxelData )
        self.opComputeEdgeFeatures.Rag.connect( self.opRagCache.Output )
        
        self.opEdgeFeaturesCache = OpMultiLaneWrapper( OpValueCache, parent=self, broadcastingSlotNames=['fixAtCurrent'] )
        self.opEdgeFeaturesCache.Input.connect( self.opComputeEdgeFeatures.EdgeFeaturesDataFrame )
        self.opEdgeFeaturesCache.name = 'opEdgeFeaturesCache'

        self.opTrainEdgeClassifier = OpTrainEdgeClassifier( parent=self )
        self.opTrainEdgeClassifier.EdgeLabelsDict.connect( self.EdgeLabelsDict )
        self.opTrainEdgeClassifier.EdgeFeaturesDataFrame.connect( self.opEdgeFeaturesCache.Output )
        
        # classifier cache input is set after training.
        self.opClassifierCache = OpValueCache(parent=self)
        self.opClassifierCache.Input.connect( self.opTrainEdgeClassifier.EdgeClassifier )
        self.opClassifierCache.fixAtCurrent.connect( self.FreezeClassifier )
        self.opClassifierCache.name = 'opClassifierCache'
        
        self.opPredictEdgeProbabilities = OpMultiLaneWrapper( OpPredictEdgeProbabilities, parent=self, broadcastingSlotNames=['EdgeClassifier'] )
        self.opPredictEdgeProbabilities.EdgeClassifier.connect( self.opClassifierCache.Output )
        self.opPredictEdgeProbabilities.EdgeFeaturesDataFrame.connect( self.opEdgeFeaturesCache.Output )
        
        self.opEdgeProbabilitiesCache = OpMultiLaneWrapper( OpValueCache, parent=self, broadcastingSlotNames=['fixAtCurrent'] )
        self.opEdgeProbabilitiesCache.Input.connect( self.opPredictEdgeProbabilities.EdgeProbabilities )
        self.opEdgeProbabilitiesCache.name = 'opEdgeProbabilitiesCache'
        self.opEdgeProbabilitiesCache.fixAtCurrent.connect( self.FreezeClassifier )

        self.opEdgeProbabilitiesDict = OpMultiLaneWrapper( OpEdgeProbabilitiesDict, parent=self )
        self.opEdgeProbabilitiesDict.Rag.connect( self.opRagCache.Output )
        self.opEdgeProbabilitiesDict.EdgeProbabilities.connect( self.opEdgeProbabilitiesCache.Output )
        
        self.opEdgeProbabilitiesDictCache = OpMultiLaneWrapper( OpValueCache, parent=self, broadcastingSlotNames=['fixAtCurrent'] )
        self.opEdgeProbabilitiesDictCache.Input.connect( self.opEdgeProbabilitiesDict.EdgeProbabilitiesDict )
        self.opEdgeProbabilitiesDictCache.name = 'opEdgeProbabilitiesDictCache'

        self.opNaiveSegmentation = OpMultiLaneWrapper( OpNaiveSegmentation, parent=self )
        self.opNaiveSegmentation.Superpixels.connect( self.Superpixels )
        self.opNaiveSegmentation.Rag.connect( self.opRagCache.Output )
        self.opNaiveSegmentation.EdgeProbabilities.connect( self.opEdgeProbabilitiesCache.Output )

        self.opNaiveSegmentationCache = OpMultiLaneWrapper( OpBlockedArrayCache, parent=self, broadcastingSlotNames=['CompressionEnabled', 'fixAtCurrent', 'BypassModeEnabled'] )
        self.opNaiveSegmentationCache.CompressionEnabled.setValue(True)
        self.opNaiveSegmentationCache.Input.connect( self.opNaiveSegmentation.Output )
        self.opNaiveSegmentationCache.name = 'opNaiveSegmentationCache'

        self.Rag.connect( self.opRagCache.Output )
        self.EdgeProbabilities.connect( self.opEdgeProbabilitiesCache.Output )
        self.EdgeProbabilitiesDict.connect( self.opEdgeProbabilitiesDictCache.Output )
        self.NaiveSegmentation.connect( self.opNaiveSegmentationCache.Output )

        # All input multi-slots should be kept in sync
        # Output multi-slots will auto-sync via the graph
        multiInputs = [s for s in list(self.inputs.values()) if s.level >= 1]
        for s1 in multiInputs:
            for s2 in multiInputs:
                if s1 != s2:
                    def insertSlot( a, b, position, finalsize ):
                        a.insertSlot(position, finalsize)
                    s1.notifyInserted( partial(insertSlot, s2 ) )
                    
                    def removeSlot( a, b, position, finalsize ):
                        a.removeSlot(position, finalsize)
                    s1.notifyRemoved( partial(removeSlot, s2 ) )

        # If superpixels change, we have to delete our edge labels.
        # Since we're dealing with multi-lane slot, setting up dirty handlers is a two-stage process.
        # (1) React to lane insertion by subscribing to dirty signals for the new lane.
        # (2) React to each lane's dirty signal by deleting the labels for that lane.

        def subscribe_to_dirty_sp(slot, position, finalsize):
            # A new lane was added.  Subscribe to it's dirty signal.
            assert slot is self.Superpixels
            self.Superpixels[position].notifyDirty(self.handle_dirty_superpixels)
            self.Superpixels[position].notifyReady(self.handle_dirty_superpixels)
            self.Superpixels[position].notifyUnready(self.handle_dirty_superpixels)

        # When a new lane is added, set up the listener for dirtyness.
        self.Superpixels.notifyInserted(subscribe_to_dirty_sp)

    def handle_dirty_superpixels(self, subslot, *args):
        """
        Discards the labels for a given lane.
        NOTE: In addition to callers in this file, this function is also called from multicutWorkflow.py
        """
        # Determine which lane triggered this and delete it's labels
        lane_index = self.Superpixels.index(subslot)
        old_labels = self.EdgeLabelsDict[lane_index].value
        if old_labels:
            logger.warning( "Superpixels changed.  Deleting all labels in lane {}.".format( lane_index ) )
            logger.info( "Old labels were: {}".format( old_labels ) )
            self.EdgeLabelsDict[lane_index].setValue({})

    def setupOutputs(self):
        for sp_slot, seg_cache_blockshape_slot in zip(self.Superpixels, self.opNaiveSegmentationCache.BlockShape):
            assert sp_slot.meta.dtype == np.uint32
            assert sp_slot.meta.getAxisKeys()[-1] == 'c'
            seg_cache_blockshape_slot.setValue( sp_slot.meta.shape )

    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here, but requesting slot: {}".format( slot )

    def propagateDirty(self, slot, subindex, roi):
        pass

    def setEdgeLabelsFromGroundtruth(self, lane_index):
        """
        For the given lane, read the ground truth volume and
        automatically determine edge label values.
        """
        op_view = self.getLane(lane_index)
        
        if not op_view.GroundtruthSegmentation.ready():
            raise RuntimeError("There is no Ground Truth data available for lane: {}".format( lane_index ))

        logger.info("Loading groundtruth for lane {}...".format(lane_index))
        gt_vol = op_view.GroundtruthSegmentation[:].wait()
        gt_vol = vigra.taggedView(gt_vol, op_view.GroundtruthSegmentation.meta.axistags)
        gt_vol = gt_vol.withAxes(''.join(tag.key for tag in op_view.Superpixels.meta.axistags))
        gt_vol = gt_vol.dropChannelAxis()

        rag = op_view.opRagCache.Output.value

        logger.info("Computing edge decisions from groundtruth...")
        decisions = rag.edge_decisions_from_groundtruth(gt_vol, asdict=False)
        edge_labels = decisions.view(np.uint8) + 1
        edge_ids = list(map(tuple, rag.edge_ids))
        edge_labels_dict = dict( list(zip(edge_ids, edge_labels)) )
        op_view.EdgeLabelsDict.setValue( edge_labels_dict )

    def addLane(self, laneIndex):
        numLanes = len(self.VoxelData)
        assert numLanes == laneIndex, "Image lanes must be appended."        
        self.VoxelData.resize(numLanes+1)
        
    def removeLane(self, laneIndex, finalLength):
        self.VoxelData.removeSlot(laneIndex, finalLength)

    def getLane(self, laneIndex):
        return OperatorSubView(self, laneIndex)


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

def decodeToStringIfBytes(s):
    if isinstance(s, bytes):
        return s.decode()
    else:
        return s

class OpComputeEdgeFeatures(Operator):
    FeatureNames = InputSlot()
    VoxelData = InputSlot()
    Rag = InputSlot()
    EdgeFeaturesDataFrame = OutputSlot() # Includes columns 'sp1' and 'sp2'
     
    def setupOutputs(self):
        assert self.VoxelData.meta.getAxisKeys()[-1] == 'c'
        self.EdgeFeaturesDataFrame.meta.shape = (1,)
        self.EdgeFeaturesDataFrame.meta.dtype = object
         
    def execute(self, slot, subindex, roi, result):
        rag = self.Rag.value
        channel_feature_names = self.FeatureNames.value

        edge_feature_dfs =[]
        for c in range( self.VoxelData.meta.shape[-1] ):
            channel_name = self.VoxelData.meta.channel_names[c]
            if channel_name not in channel_feature_names:
                continue
            
            feature_names = [decodeToStringIfBytes(f) for f in channel_feature_names[channel_name]]
            if not feature_names:
                # No features selected for this channel
                continue

            voxel_data = self.VoxelData[...,c:c+1].wait()
            voxel_data = vigra.taggedView(voxel_data, self.VoxelData.meta.axistags)
            voxel_data = voxel_data[...,0] # drop channel
            edge_features_df = rag.compute_features(voxel_data, feature_names)

            #if np.isnan(edge_features_df.values).any():
            #    raise RuntimeError("Whoa, why are there NaN values in the feature matrix?")
            
            edge_features_df = edge_features_df.iloc[:, 2:] # Discard columns [sp1, sp2]
            
            # Prefix all column names with the channel name, to guarantee uniqueness
            # (Generally a nice feature, but also required for serialization.)
            edge_features_df.columns = [channel_name + ' ' + feature_name for feature_name in edge_features_df.columns.values]
            edge_feature_dfs.append(edge_features_df)

        # Could use join() or merge() here, but we know the rows are already in the right order, and concat() should be faster.
        all_edge_features_df = pd.DataFrame( rag.edge_ids, columns=['sp1', 'sp2'] )
        all_edge_features_df = pd.concat([all_edge_features_df] + edge_feature_dfs, axis=1, copy=False)
        result[0] = all_edge_features_df
 
    def propagateDirty(self, slot, subindex, roi):
        self.EdgeFeaturesDataFrame.setDirty()
     

class OpTrainEdgeClassifier(Operator):
    EdgeLabelsDict = InputSlot(level=1)
    EdgeFeaturesDataFrame = InputSlot(level=1)
    
    EdgeClassifier = OutputSlot()

    def setupOutputs(self):
        self.EdgeClassifier.meta.shape = (1,)
        self.EdgeClassifier.meta.dtype = object
        
    def execute(self, slot, subindex, roi, result):
        all_features_and_labels_df = None

        for lane_index, (labels_dict_slot, features_slot) in \
                enumerate( zip(self.EdgeLabelsDict, self.EdgeFeaturesDataFrame) ):
            logger.info("Retrieving features for lane {}...".format(lane_index))

            labels_dict = labels_dict_slot.value.copy() # Copy now to avoid threading issues.
            if not labels_dict:
                continue

            sp_columns = np.array(list(labels_dict.keys()))
            edge_features_df = features_slot.value
            assert list(edge_features_df.columns[0:2]) == ['sp1', 'sp2']

            labels_df = pd.DataFrame(sp_columns, columns=['sp1', 'sp2'])
            labels_df['label'] = list(labels_dict.values())

            # Drop zero labels
            labels_df = labels_df[labels_df['label'] != 0]
            
            # Merge in features
            features_and_labels_df = pd.merge(edge_features_df, labels_df, how='right', on=['sp1', 'sp2'])
            if all_features_and_labels_df is not None:
                all_features_and_labels_df = all_features_and_labels_df.append(features_and_labels_df)
            else:
                all_features_and_labels_df = features_and_labels_df

        if all_features_and_labels_df is None:
            # No labels yet.
            result[0] = None
            return

        assert list(all_features_and_labels_df.columns[0:2]) == ['sp1', 'sp2']
        assert all_features_and_labels_df.columns[-1] == 'label'

        feature_matrix = all_features_and_labels_df.iloc[:, 2:-1].values # Omit 'sp1', 'sp2', and 'label'
        labels = all_features_and_labels_df.iloc[:, -1].values

        logger.info("Training classifier with {} labels...".format( len(labels) ))
        # TODO: Allow factory to be configured via an input slot
        classifier_factory = ParallelVigraRfLazyflowClassifierFactory()
        classifier = classifier_factory.create_and_train( feature_matrix,
                                                          labels,
                                                          feature_names=all_features_and_labels_df.columns[2:-1].values )
        assert set(classifier.known_classes).issubset(set([1,2]))
        result[0] = classifier

    def propagateDirty(self, slot, subindex, roi):
        self.EdgeClassifier.setDirty()

class OpPredictEdgeProbabilities(Operator):
    EdgeClassifier = InputSlot()
    EdgeFeaturesDataFrame = InputSlot()
    EdgeProbabilities = OutputSlot() # A 1D array of probabilities, in same order as EdgeFeaturesDataFrame
    
    def setupOutputs(self):
        self.EdgeProbabilities.meta.shape = (1,)
        self.EdgeProbabilities.meta.dtype = object

    def execute(self, slot, subindex, roi, result):
        edge_features_df = self.EdgeFeaturesDataFrame.value
        classifier = self.EdgeClassifier.value
        
        # Classifier can be None if no labels have been selected
        if classifier is None or len(classifier.known_classes) < 2:
            result[0] = np.zeros( (len(edge_features_df),), dtype=np.float32 )
            return
        
        logger.info("Predicting edge probabilities...")
        feature_matrix = edge_features_df.iloc[:, 2:].values # Discard [sp1, sp2]
        assert feature_matrix.dtype == np.float32, "Unexpected feature dtype: {}".format( feature_matrix.dtype )
        probabilities = classifier.predict_probabilities(feature_matrix)[:,1]
        assert len(probabilities) == len(edge_features_df)
        result[0] = probabilities
    
    def propagateDirty(self, slot, subindex, roi):
        self.EdgeProbabilities.setDirty()

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
        logger.info("Converting edge probabilities to dict...")
        rag = self.Rag.value
        edge_probabilities = self.EdgeProbabilities.value
        if edge_probabilities is None:
            # Edge probabilities are 'None' if they haven't been loaded into the cache yet.
            # Just return 0.0 for all probabilities
            result[0] = { tuple(edge_id) : 0.0 for edge_id in rag.edge_ids }
        else:
            result[0] = dict(zip(map(tuple, rag.edge_ids), edge_probabilities))
            
        logger.info("...done")

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

