from unittest.mock import patch

import numpy
import pytest

from ilastik.applets.objectExtraction.objectExtractionSerializer import (
    ObjectExtractionSerializer,
    UnsatisfyableObjectFeaturesError,
)
from lazyflow.utility.testing import SlotDesc, build_multi_output_mock_op


@pytest.fixture
def mock_op(graph):
    slot_data = {
        "LabelImage": SlotDesc(typ_="output", level=1, dtype=numpy.uint32, shape=(5, 6, 1), axistags="yxc"),
        "LabelImageCacheInput": SlotDesc(typ_="input", level=1, dtype=numpy.uint32, shape=(5, 6, 1), axistags="yxc"),
        "CleanLabelBlocks": SlotDesc(typ_="output", level=1, dtype=object, shape=(1,)),
        "Features": SlotDesc(typ_="input", level=0, dtype=object, shape=(1,)),
        "BlockwiseRegionFeatures": SlotDesc(typ_="output", level=1),
        "RegionFeaturesCacheInput": SlotDesc(typ_="input", level=1),
        "RegionFeaturesCleanBlocks": SlotDesc(typ_="output", level=1),
    }
    return build_multi_output_mock_op(slot_data, graph, n_lanes=2)


@pytest.fixture
def project_group_name():
    return "ObjectExtraction"


@pytest.fixture
def serializer(mock_op, project_group_name):
    serializer = ObjectExtractionSerializer(mock_op, project_group_name)
    return serializer


@patch("ilastik.plugins.manager.pluginManager.getPluginByName")
def test_deserializeFromHdf5_missing_feature_plugin(
    mocked_plugin_fct, serializer, project_group_name, empty_in_memory_project_file
):
    mocked_plugin_fct.return_value = False

    empty_in_memory_project_file.create_dataset(f"/{project_group_name}/StorageVersion", data=b"1.0")
    empty_in_memory_project_file.create_dataset(
        f"/{project_group_name}/Features/SomeNoneExistingPlugin/SomeNoneExistingFeature", data=numpy.void(b"test")
    )
    with pytest.raises(UnsatisfyableObjectFeaturesError):
        serializer.deserializeFromHdf5(empty_in_memory_project_file, empty_in_memory_project_file.name)


@patch("ilastik.plugins.manager.pluginManager.getPluginByName")
def test_deserializeFromHdf5_no_missing_feature_plugin(
    mocked_plugin_fct, mock_op, serializer, project_group_name, empty_in_memory_project_file
):
    mocked_plugin_fct.return_value = True

    empty_in_memory_project_file.create_dataset(f"/{project_group_name}/StorageVersion", data=b"1.0")
    empty_in_memory_project_file.create_dataset(
        f"/{project_group_name}/Features/SomeExistingPlugin/SomeExistingFeature", data=b"test"
    )

    serializer.deserializeFromHdf5(empty_in_memory_project_file, empty_in_memory_project_file.name)

    assert mock_op.Features[()].wait() == [{"SomeExistingPlugin": {"SomeExistingFeature": "test"}}]
