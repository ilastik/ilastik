import pytest
import numpy as np


from ndstructs import Array5D
from ndstructs.datasource import ArrayDataSource
from ilastik.features.fastfilters import GaussianSmoothing
import fastfilters

def test_gaussian_smoothing():
    sigma = 1.2
    data = Array5D(np.random.rand(100, 200, 3), axiskeys="yxc")
    datasource = ArrayDataSource(data=data)
    extractor = GaussianSmoothing(sigma=1.2)
    features = extractor.compute(datasource)

    for channel, feature_out in zip(data.channels(), features.channel_stacks(extractor.get_channel_multiplier(data.roi))):
        import pydevd; pydevd.settrace()
        expected_features = fastfilters.gaussianSmoothing(channel.raw("yx"), sigma=sigma)
        assert (expected_features == channel.raw("yx")).all()
