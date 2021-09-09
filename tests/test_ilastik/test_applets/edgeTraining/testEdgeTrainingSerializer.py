import h5py
import numpy
import pandas
import pytest

from ilastikrag import Rag
from ilastik.applets.edgeTraining import OpEdgeTraining
from lazyflow.utility.testing import build_multi_output_mock_op, SlotDescription
from ilastik.applets.edgeTraining.edgeTrainingSerializer import EdgeTrainingSerializer
import vigra


@pytest.fixture
def empty_project_file():
    with h5py.File("test_project1", mode="a", driver="core", backing_store=False) as test_project:
        test_project.create_dataset("ilastikVersion", data=b"1.0.0")
        yield test_project


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
        "WatershedSelectedInput": SlotDescription(
            level=1, dtype=numpy.float32, shape=(5, 6, 1), axistags=vigra.defaultAxistags("yxc")
        ),
        "VoxelData": SlotDescription(
            level=1, dtype=numpy.float32, shape=(5, 6, 1), axistags=vigra.defaultAxistags("yxc")
        ),
        "Superpixels": SlotDescription(
            level=1,
            dtype=numpy.uint32,
            shape=(5, 6, 1),
            axistags=vigra.defaultAxistags("yxc"),
            data=[superpixels, superpixels],
        ),
    }
    return build_multi_output_mock_op(slot_data, graph, n_lanes=2)


def test_serializer_roundtrip(graph, inputs, empty_project_file, superpixels, rag):
    op = OpEdgeTraining(graph=graph)
    op.VoxelData.connect(inputs.VoxelData)
    op.Superpixels.connect(inputs.Superpixels)
    op.WatershedSelectedInput.connect(inputs.WatershedSelectedInput)

    # set level0 slots
    op.TrainRandomForest.setValue(False)
    op.FeatureNames.setValue({"test0": [b"test_feature_0", b"test_feature_1"]})

    # set level1 slots
    laneop = op.getLane(0)
    edge_features_reference = pandas.DataFrame({"col1": [1, 2], "col2": [3, 4]})
    laneop.opEdgeFeaturesCache.forceValue(edge_features_reference, set_dirty=False)

    edge_labels_reference = {(0, 1): 0, (0, 2): 1, (1, 2): 0}
    laneop.EdgeLabelsDict.setValue(edge_labels_reference)

    laneop.opRagCache.forceValue(rag, set_dirty=False)

    serializer = EdgeTrainingSerializer(op, "EdgeTraining")
    serializer.serializeToHdf5(empty_project_file, empty_project_file.name)

    # round trip
    op_load = OpEdgeTraining(graph=graph)

    op_load.VoxelData.connect(inputs.VoxelData)
    op_load.Superpixels.connect(inputs.Superpixels)
    op_load.WatershedSelectedInput.connect(inputs.WatershedSelectedInput)

    deserializer = EdgeTrainingSerializer(op_load, "EdgeTraining")
    deserializer.deserializeFromHdf5(empty_project_file, empty_project_file.name)

    # check level0 slots
    assert op_load.TrainRandomForest.value == False
    assert all(a == b for a, b in zip(op_load.FeatureNames.value["test0"], [b"test_feature_0", b"test_feature_1"]))

    # check level1 slots
    # empty lane
    op_load_lane1 = op_load.getLane(1)
    assert op_load_lane1.EdgeLabelsDict.value == {}
    assert op_load_lane1.opEdgeFeaturesCache._value is None

    # lane w content
    op_load_lane0 = op_load.getLane(0)
    edge_features_loaded = op_load_lane0.opEdgeFeaturesCache.Output.value
    assert edge_features_loaded.equals(edge_features_reference)

    assert op_load_lane0.EdgeLabelsDict.value == edge_labels_reference

    loaded_rag = op_load_lane0.opRagCache.Output.value
