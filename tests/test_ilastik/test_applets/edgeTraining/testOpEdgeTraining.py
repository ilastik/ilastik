import numpy as np
import pytest

from ilastikrag.util import generate_random_voronoi

from ilastik.applets.edgeTraining import OpEdgeTraining


@pytest.fixture
def superpixels():
    superpixels = generate_random_voronoi((100, 100, 100), 100)
    superpixels = superpixels.insertChannelAxis()
    return superpixels


class TestOpEdgeTraining:
    def testBasic(self, graph, superpixels):
        voxel_data = superpixels.astype(np.float32)

        multilane_op = OpEdgeTraining(graph=graph)
        multilane_op.VoxelData.resize(1)  # resizes all level-1 slots.
        op_view = multilane_op.getLane(0)

        op_view.VoxelData.setValue(voxel_data, extra_meta={"channel_names": ["Grayscale"]})
        op_view.Superpixels.setValue(superpixels)
        op_view.WatershedSelectedInput.setValue(voxel_data)
        op_view.TrainRandomForest.setValue(True)

        multilane_op.FeatureNames.setValue({"Grayscale": ["standard_edge_mean", "standard_edge_count"]})

        assert op_view.Rag.ready()

        # Pick some edges to label
        rag = op_view.Rag.value
        edge_A = tuple(rag.edge_ids[0])
        edge_B = tuple(rag.edge_ids[1])
        edge_C = tuple(rag.edge_ids[2])
        edge_D = tuple(rag.edge_ids[3])

        labels = {edge_A: 1, edge_B: 1, edge_C: 2, edge_D: 2}  # OFF  # ON

        op_view.EdgeLabelsDict.setValue(labels)
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

    def test_multi_lane(self, graph, superpixels):
        voxel_data = superpixels.astype(np.float32)

        multilane_op = OpEdgeTraining(graph=graph)
        multilane_op.VoxelData.resize(2)  # resizes all level-1 slots.

        op_lane0 = multilane_op.getLane(0)
        op_lane1 = multilane_op.getLane(1)
        lanes = [op_lane0, op_lane1]

        for lane_op in lanes:
            lane_op.VoxelData.setValue(voxel_data, extra_meta={"channel_names": ["Grayscale"]})
            lane_op.Superpixels.setValue(superpixels)
            lane_op.WatershedSelectedInput.setValue(voxel_data)
        multilane_op.TrainRandomForest.setValue(True)

        multilane_op.FeatureNames.setValue({"Grayscale": ["standard_edge_mean", "standard_edge_count"]})

        assert op_lane0.Rag.ready()
        assert op_lane1.Rag.ready()

        # Pick some edges to label
        rag0 = op_lane0.Rag.value
        rag1 = op_lane1.Rag.value
        edge_00 = tuple(rag0.edge_ids[0])
        edge_01 = tuple(rag0.edge_ids[1])
        edge_12 = tuple(rag1.edge_ids[2])
        edge_13 = tuple(rag1.edge_ids[3])

        labels0 = {edge_00: 1, edge_01: 1}
        labels1 = {edge_12: 2, edge_13: 2}

        op_lane0.EdgeLabelsDict.setValue(labels0)
        multilane_op.FreezeClassifier.setValue(False)

        for lane_op in lanes:
            assert lane_op.EdgeProbabilities.ready()
            assert lane_op.EdgeProbabilitiesDict.ready()
            assert lane_op.NaiveSegmentation.ready()

        op_lane1.EdgeLabelsDict.setValue(labels1)

        for lane_op in lanes:
            assert lane_op.EdgeProbabilities.ready()
            assert lane_op.EdgeProbabilitiesDict.ready()
            assert lane_op.NaiveSegmentation.ready()

        edge_prob_dict0 = op_lane0.EdgeProbabilitiesDict.value

        # OFF
        assert edge_prob_dict0[edge_00] < 0.5, "Expected < 0.5, got {}".format(edge_prob_dict0[edge_00])
        assert edge_prob_dict0[edge_01] < 0.5, "Expected < 0.5, got {}".format(edge_prob_dict0[edge_01])

        edge_prob_dict1 = op_lane1.EdgeProbabilitiesDict.value

        # ON
        assert edge_prob_dict1[edge_12] > 0.5, "Expected > 0.5, got {}".format(edge_prob_dict1[edge_12])
        assert edge_prob_dict1[edge_13] > 0.5, "Expected > 0.5, got {}".format(edge_prob_dict1[edge_13])
