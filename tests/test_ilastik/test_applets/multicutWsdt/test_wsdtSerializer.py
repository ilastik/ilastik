import h5py
import pytest

from ilastik.applets.wsdt.opWsdt import OpCachedWsdt
from ilastik.applets.wsdt.wsdtSerializer import WsdtSerializer


@pytest.mark.parametrize(
    "serializer_version,serialized_value,expected_blockwise_value",
    [("0.1", None, False), ("0.2", True, True), ("0.2", False, False)],
)
def test_01_02_compat(
    graph, empty_in_memory_project_file, serializer_version, serialized_value, expected_blockwise_value
):
    """Test reading of legacy multicut projects

    with projects saved with WsdtSerializer(0.1), the BlockwiseWatershed
    was not present and not serialized. Here we want it to default to False,
    whereas in the 0.2 case, we want this slot to be correctly deserialized.
    """
    serializer_group = "wsdt"

    g = empty_in_memory_project_file.create_group(serializer_group)
    if serialized_value is not None:
        g.create_dataset("BlockwiseWatershed", data=serialized_value)
    g.create_dataset("StorageVersion", data=serializer_version)

    op = OpCachedWsdt(graph=graph)
    serializer = WsdtSerializer(op, serializer_group)
    serializer.deserializeFromHdf5(empty_in_memory_project_file, empty_in_memory_project_file.name)

    assert op.BlockwiseWatershed.value == expected_blockwise_value
