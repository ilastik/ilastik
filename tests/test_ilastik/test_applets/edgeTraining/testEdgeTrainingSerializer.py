import h5py
import numpy
import pandas
import pytest
import vigra
from ilastikrag import Rag

from ilastik.applets.edgeTraining import OpEdgeTraining
from ilastik.applets.edgeTraining.edgeTrainingSerializer import EdgeTrainingSerializer
from lazyflow.utility.testing import SlotDesc, build_multi_output_mock_op


@pytest.fixture
def superpixels():
    # superpixels needed for creation and deserialization of the rag
    data = numpy.zeros((5, 6, 1), dtype="uint32")
    data[0:2, ...] = 1
    data[2:, ...] = 2
    return data


@pytest.fixture
def rag(superpixels):
    return Rag(vigra.taggedView(superpixels, axistags="yxc").withAxes("yx"))


@pytest.fixture
def inputs(graph, superpixels):
    slot_data = {
        "WatershedSelectedInput": SlotDesc(level=1, dtype=numpy.float32, shape=(5, 6, 1), axistags="yxc"),
        "VoxelData": SlotDesc(level=1, dtype=numpy.float32, shape=(5, 6, 1), axistags="yxc"),
        "Superpixels": SlotDesc(
            level=1,
            dtype=numpy.uint32,
            shape=(5, 6, 1),
            axistags="yxc",
            data=[superpixels, superpixels],
        ),
    }
    return build_multi_output_mock_op(slot_data, graph, n_lanes=2)


@pytest.mark.parametrize("content_lane,empty_lane", [(0, 1), (1, 0)])
def test_serializer_roundtrip(graph, inputs, empty_in_memory_project_file, superpixels, rag, content_lane, empty_lane):
    op = OpEdgeTraining(graph=graph)
    op.VoxelData.connect(inputs.VoxelData)
    op.Superpixels.connect(inputs.Superpixels)
    op.WatershedSelectedInput.connect(inputs.WatershedSelectedInput)

    # set level0 slots
    op.FeatureNames.setValue({"test0": [b"test_feature_0", b"test_feature_1"]})
    op.TrainRandomForest.setValue(True)

    # set level1 slots
    laneop = op.getLane(content_lane)
    edge_features_reference = pandas.DataFrame({"col1": [1, 2], "col2": [3, 4]})
    laneop.opEdgeFeaturesCache.forceValue(edge_features_reference, set_dirty=False)

    edge_labels_reference = {(0, 1): 0, (0, 2): 1, (1, 2): 0}
    laneop.EdgeLabelsDict.setValue(edge_labels_reference)

    laneop.opRagCache.forceValue(rag, set_dirty=False)

    serializer = EdgeTrainingSerializer(op, "EdgeTraining")
    serializer.serializeToHdf5(empty_in_memory_project_file, empty_in_memory_project_file.name)

    # round trip
    op_load = OpEdgeTraining(graph=graph)

    op_load.VoxelData.connect(inputs.VoxelData)
    op_load.Superpixels.connect(inputs.Superpixels)
    op_load.WatershedSelectedInput.connect(inputs.WatershedSelectedInput)

    deserializer = EdgeTrainingSerializer(op_load, "EdgeTraining")
    deserializer.deserializeFromHdf5(empty_in_memory_project_file, empty_in_memory_project_file.name)

    # check level0 slots
    assert op_load.TrainRandomForest.value
    assert all(a == b for a, b in zip(op_load.FeatureNames.value["test0"], [b"test_feature_0", b"test_feature_1"]))

    # check level1 slots
    # empty lane
    op_load_empty_lane = op_load.getLane(empty_lane)
    assert op_load_empty_lane.opRagCache._value is None
    assert op_load_empty_lane.EdgeLabelsDict.value == {}
    assert op_load_empty_lane.opEdgeFeaturesCache._value is None

    # lane w content
    op_load_content_lane = op_load.getLane(content_lane)
    edge_features_loaded = op_load_content_lane.opEdgeFeaturesCache.Output.value
    assert edge_features_loaded.equals(edge_features_reference)

    assert op_load_content_lane.EdgeLabelsDict.value == edge_labels_reference

    assert op_load_content_lane.opRagCache._value is not None


@pytest.mark.parametrize(
    "serializer_version,train_rf,expect_cached_features",
    [("0.1", False, False), ("0.2", False, True), ("0.1", True, True), ("0.2", True, True)],
)
def test_serializer_01_02(
    graph, inputs, empty_in_memory_project_file, serializer_version, train_rf, expect_cached_features
):
    op = OpEdgeTraining(graph=graph)
    op.VoxelData.connect(inputs.VoxelData)
    op.Superpixels.connect(inputs.Superpixels)
    op.WatershedSelectedInput.connect(inputs.WatershedSelectedInput)
    # need to set _something_ to make operator "ready"
    # this is necessary since the removal of the default value here
    op.FeatureNames.setValue({"test0": [b"test_feature_0", b"test_feature_1"]})
    op.TrainRandomForest.setValue(train_rf)

    laneop = op.getLane(0)
    edge_features_reference = pandas.DataFrame({"col1": [1, 2], "col2": [3, 4]})
    laneop.opEdgeFeaturesCache.forceValue(edge_features_reference, set_dirty=False)

    serializer = EdgeTrainingSerializer(op, "EdgeTraining")
    serializer.version = serializer_version
    serializer.serializeToHdf5(empty_in_memory_project_file, empty_in_memory_project_file.name)

    op_load = OpEdgeTraining(graph=graph)
    op_load.VoxelData.connect(inputs.VoxelData)
    op_load.Superpixels.connect(inputs.Superpixels)
    op_load.WatershedSelectedInput.connect(inputs.WatershedSelectedInput)
    deserializer = EdgeTrainingSerializer(op_load, "EdgeTraining")
    deserializer.deserializeFromHdf5(empty_in_memory_project_file, empty_in_memory_project_file.name)

    op_load_lane0 = op_load.getLane(0)
    assert (op_load_lane0.opEdgeFeaturesCache._value is not None) == expect_cached_features
