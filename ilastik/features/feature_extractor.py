from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from functools import reduce
from operator import mul
from typing import List, Iterator

import vigra.filters
import numpy as np

from ilastik.array5d import Slice5D, Point5D, Shape5D
from ilastik.array5d import Array5D, Image, ScalarImage, LinearData
from ilastik.data_source import DataSource, DataSpec

class FeatureData(Array5D):
    def __init__(self, arr:np.ndarray, axiskeys:str):
        assert arr.dtype == np.float32
        super().__init__(arr, axiskeys)

class FeatureExtractor(ABC):
    def __init__(self, sigma:float, window_size:float):
        self.sigma = sigma
        self.window_size = window_size

    def __repr__(self):
        return f"<{self.__class__.__qualname__} sigma={self.sigma} window_size={self.window_size}>"

    def allocate_for(self, roi:DataSpec) -> Array5D:
        return FeatureData.allocate(self.get_expected_shape(roi), dtype=np.float32)

    @abstractmethod
    def get_expected_shape(self, roi:DataSpec) -> Shape5D:
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

    def get_expected_shape(self, roi:DataSpec) -> Shape5D:
        num_output_channels = roi.shape.c * self.dimension
        return roi.shape.with_coord(c=num_output_channels)

    @property
    def halo(self) -> Point5D:
        return Point5D.zero(x=5, y=5)

    def compute(self, roi:DataSpec, out:Array5D=None) -> Array5D:
        data = roi.retrieve(self.halo)
        target = out or self.allocate_for(roi) #N.B.: target has no halo
        assert target.shape == self.get_expected_shape(roi)
        for source_image, target_image in zip(data.images(), target.images()):
            for source_channel, out_features in zip(source_image.channels(), target_image.channel_stacks(step=self.dimension)):
                self._do_compute(source_channel, out=out_features)
        return target

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
        with ThreadPoolExecutor(max_workers=len(self.features), thread_name_prefix="features") as executor:
            channel_count = 0
            for f in self.features:
                channel_stop = channel_count + f.dimension
                feature_out = out.cut_with(c=slice(channel_count, channel_stop))
                executor.submit(f._do_compute, raw_data, out=feature_out)
                channel_count = channel_stop
