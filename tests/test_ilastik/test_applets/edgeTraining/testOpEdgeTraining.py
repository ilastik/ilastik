import numpy as np
import pandas as pd

from ilastikrag.util import generate_random_voronoi

from lazyflow.graph import Graph
from ilastik.applets.edgeTraining import OpEdgeTraining

import logging
logger = logging.getLogger("tests.test_applets.edgeTraining")

class TestOpEdgeTraining(object):
    
    def testBasic(self):
        superpixels = generate_random_voronoi( (100,100,100), 100 )
        superpixels = superpixels.insertChannelAxis()
        
        voxel_data = superpixels.astype(np.float32)
                
        graph = Graph()
        multilane_op = OpEdgeTraining(graph=graph)
        multilane_op.VoxelData.resize(1) # resizes all level-1 slots.
        op_view = multilane_op.getLane(0)
        
        op_view.VoxelData.setValue( voxel_data, extra_meta={'channel_names': ['Grayscale']} )
        op_view.Superpixels.setValue( superpixels )
        
        multilane_op.FeatureNames.setValue( { "Grayscale": ['standard_edge_mean', 'standard_edge_count'] } )
        
        assert op_view.Rag.ready()

        # Pick some edges to label
        rag = op_view.Rag.value
        edge_A = tuple(rag.edge_ids[0])
        edge_B = tuple(rag.edge_ids[1])
        edge_C = tuple(rag.edge_ids[2])
        edge_D = tuple(rag.edge_ids[3])

        labels = { edge_A : 1, # OFF
                   edge_B : 1,
                   edge_C : 2, # ON
                   edge_D : 2 }

        op_view.EdgeLabelsDict.setValue( labels )
        op_view.FreezeClassifier.setValue(False)
        
        assert op_view.EdgeProbabilities.ready()
        assert op_view.EdgeProbabilitiesDict.ready()
        assert op_view.NaiveSegmentation.ready()

        edge_prob_dict = op_view.EdgeProbabilitiesDict.value
        
        # OFF
        assert edge_prob_dict[edge_A] < 0.5, "Expected < 0.5, got {}".format(edge_prob_dict[edge_A])
        assert edge_prob_dict[edge_B] < 0.5, "Expected < 0.5, got {}".format(edge_prob_dict[edge_B])
        
        # ON
        assert edge_prob_dict[edge_C] > 0.5, "Expected > 0.5, got {}".format(edge_prob_dict[edge_C])
        assert edge_prob_dict[edge_D] > 0.5, "Expected > 0.5, got {}".format(edge_prob_dict[edge_D])
