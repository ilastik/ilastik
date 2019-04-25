from abc import ABC, abstractmethod
from functools import reduce
from operator import mul
from typing import List, Iterator

import vigra.filters
import numpy as np

from ilastik.array5d import Slice5D, Point5D, Shape5D
from ilastik.array5d import Array5D, Image, ScalarImage, LinearData

class FeatureData(Array5D):
    def __init__(self, arr:np.ndarray, axiskeys:str):
        assert arr.dtype == np.float32
        super().__init__(arr, axiskeys)

    def linear_raw(self):
        """Returns a raw view with one spatial dimension and one channel dimension"""
        shape_dict = {**self.shape.to_dict(), 'c':1}
        first_dimension = reduce(mul, shape_dict.values(), 1)
        first_dimension = int(first_dimension)
        new_shape = (first_dimension, self.shape.c)

        #FIXME: this nukes axistags and i don't know how to put them back =/
        return np.asarray(self.with_c_as_last_axis()._data.reshape(new_shape))

class FeatureExtractor(ABC):
    def __init__(self, sigma:float, window_size:float):
        self.sigma = sigma
        self.window_size = window_size

    def __repr__(self):
        return f"<{self.__class__.__qualname__} sigma={self.sigma} window_size={self.window_size}>"

    def allocate_for(self, roi:Slice5D) -> Array5D:
        return FeatureData.allocate(self.get_expected_shape(roi), dtype=np.float32)

    @abstractmethod
    def get_expected_shape(self, roi:Slice5D) -> Shape5D:
        pass

    @abstractmethod
    def compute(self, raw_data:Array5D, out:Array5D=None) -> Array5D:
        pass

class FlatChannelwiseFilter(FeatureExtractor):
    def __init__(self, sigma:float, window_size:float=0.0):
        super().__init__(sigma=sigma, window_size=window_size)

    @property
    @abstractmethod
    def dimension(self) -> int:
        "Number of channels emmited by this feature extractor for each input channel"
        pass

    def get_expected_shape(self, roi:Slice5D) -> Shape5D:
        assert roi.is_defined()
        num_output_channels = roi.shape.c * self.dimension
        return roi.shape.with_coord(c=num_output_channels)

    def compute(self, data_source:DataSource, roi:Shape5D, out:Array5D=None) -> Array5D:
        roi = roi.defined_with(data_source.shape)
        roi_with_halo = roi #TODO: roi.enlarged(self.radius ??).clamped(data_source.shape)

        data = data_source.retrieve(roi_with_halo)
        target = out or self.allocate_for(roi) #NB: target has no halo!
        assert target.shape == self.get_expected_shape(roi)
        for source_image, target_image in zip(data.images(), target.images()):
            for source_channel, out_features in zip(source_image.channels(), target_image.channel_stacks(step=self.dimension)):
                self._do_compute(source_channel, out=out_features)
        return target.cut()

    @abstractmethod
    def _do_compute(self, raw_data:ScalarImage, out:Image):
        pass

class FeatureCollection(FlatChannelwiseFilter):
    def __init__(self, *features:List[FeatureExtractor]):
        assert len(features) > 0
        self.features = features

    @property
    def dimension(self):
        return sum(f.dimension for f in self.features)

    def _do_compute(self, raw_data:ScalarImage, out:Image):
        channel_count = 0
        for f in self.features:
            channel_stop = channel_count + f.dimension
            feature_out = out.cut_with(c=slice(channel_count, channel_stop))
            f._do_compute(raw_data, out=feature_out)
            channel_count = channel_stop
