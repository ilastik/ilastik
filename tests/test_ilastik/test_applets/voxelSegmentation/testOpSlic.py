import numpy as np
import pytest
import vigra

from ilastik.workflows.voxelSegmentation.opSlic import OpSlic
from lazyflow.operators.opArrayPiper import OpArrayPiper
from lazyflow.utility import Pipeline


@pytest.fixture
def input_data():
    # almost a cube with 8 segments
    img = np.zeros((20, 23, 25, 1))
    img[:10, :11, :13, 0] = 0.11
    img[:10, :11, 13:, 0] = 0.22
    img[:10, 11:, :13, 0] = 0.33
    img[:10, 11:, 13:, 0] = 0.44
    img[10:, :11, :13, 0] = 0.55
    img[10:, :11, 13:, 0] = 0.66
    img[10:, 11:, :13, 0] = 0.77
    img[10:, 11:, 13:, 0] = 0.88
    return vigra.taggedView(img, axistags=vigra.defaultAxistags("zyxc"))


def test_slic(input_data, graph):
    with Pipeline(graph=graph) as slic_pipeline:
        slic_pipeline.add(OpArrayPiper, Input=input_data)
        slic_pipeline.add(OpSlic, NumSegments=8)
        seg = slic_pipeline[-1].outputs["Output"][:].wait()

    assert len(np.unique(seg)) == 8

    assert np.all(seg[:10, :11, :13, 0] == 1)
    assert np.all(seg[:10, :11, 13:, 0] == 2)
    assert np.all(seg[:10, 11:, :13, 0] == 3)
    assert np.all(seg[:10, 11:, 13:, 0] == 4)
    assert np.all(seg[10:, :11, :13, 0] == 5)
    assert np.all(seg[10:, :11, 13:, 0] == 6)
    assert np.all(seg[10:, 11:, :13, 0] == 7)
    assert np.all(seg[10:, 11:, 13:, 0] == 8)
