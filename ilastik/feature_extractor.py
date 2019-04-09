from abc import ABC, abstractmethod
from typing import List

import vigra.filters
import numpy

from ilastik.array5d import Slice5D, Point5D, Shape5D
from ilastik.array5d import Array5D, Image, ScalarImage

class FeatureExtractor(ABC):
    def __init__(self, sigma:float, window_size:float):
        self.sigma = sigma
        self.window_size = window_size

    def allocate_for(self, source:Array5D) -> Array5D:
        return Array5D.allocate(self.get_expected_shape(source), dtype=numpy.float32)

    @abstractmethod
    def get_expected_shape(self, source:Array5D) -> Shape5D:
        pass

    @abstractmethod
    def compute(self, source:Array5D, roi:Slice5D=None, out:Array5D=None) -> Array5D:
        pass

class FlatChannelwiseFilter(FeatureExtractor):
    def __init__(self, sigma:float, window_size:float=0.0):
        super().__init__(sigma=sigma, window_size=window_size)

    @property
    @abstractmethod
    def out_channels_per_input_channel(self) -> int:
        pass

    def get_expected_shape(self, source:Array5D) -> Shape5D:
        shape = source.shape
        return shape.with_coord(c=shape.c * self.out_channels_per_input_channel)

    def image_at(self, source:Image, *, c:int) -> Array5D:
        channel_slice = slice(c, c+self.out_channels_per_input_channel)
        return source.cut_with(c=channel_slice)

    def compute(self, source:Array5D, roi:Slice5D=None, out:Array5D=None) -> Array5D:
        target = out or self.allocate_for(source)
        assert target.shape == self.get_expected_shape(source)
        for source_image, target_image in zip(source.imageIter(), target.imageIter()):
            for c, source_channel in enumerate(source_image.channelIter()):
                out = self.image_at(target_image, c=c)
                self._do_compute(source_channel, out=out)
        return target

    @abstractmethod
    def _do_compute(self, source:ScalarImage, out:Image):
        pass

class FeatureCollection(FlatChannelwiseFilter):
    def __init__(self, *features:List[FeatureExtractor]):
        assert len(features) > 0
        self.features = features

    @property
    def out_channels_per_input_channel(self):
        return sum(f.out_channels_per_input_channel for f in self.features)

    def _do_compute(self, source:ScalarImage, out:Image):
        channel_count = 0
        for f in self.features:
            feature_out = f.image_at(out, c=channel_count)
            f._do_compute(source, out=feature_out)
            channel_count += f.out_channels_per_input_channel
