from abc import ABC, abstractmethod
from typing import List, Iterator

import vigra.filters
import numpy

from ilastik.array5d import Slice5D, Point5D, Shape5D
from ilastik.array5d import Array5D, Image, ScalarImage

class FeatureExtractor(ABC):
    def __init__(self, sigma:float, window_size:float):
        self.sigma = sigma
        self.window_size = window_size

    def __repr__(self):
        return f"<{self.__class__.__qualname__} sigma={self.sigma} window_size={self.window_size}>"

    def allocate_for(self, source:Array5D) -> Array5D:
        return Array5D.allocate(self.get_expected_shape(source), dtype=numpy.float32)

    @abstractmethod
    def get_expected_shape(self, source:Array5D) -> Shape5D:
        pass

    @abstractmethod
    def compute(self, source:Array5D, out:Array5D=None) -> Array5D:
        pass

class FlatChannelwiseFilter(FeatureExtractor):
    def __init__(self, sigma:float, window_size:float=0.0):
        super().__init__(sigma=sigma, window_size=window_size)

    @property
    @abstractmethod
    def dimension(self) -> int:
        "Number of channels emmited by this feature extractor for each input channel"
        pass

    def get_expected_shape(self, source:Array5D) -> Shape5D:
        num_output_channels = source.shape.c * self.dimension
        return source.shape.with_coord(c=num_output_channels)

    def compute(self, source:Array5D, out:Array5D=None) -> Array5D:
        target = out or self.allocate_for(source)
        assert target.shape == self.get_expected_shape(source)
        for source_image, target_image in zip(source.images(), target.images()):
            for source_channel, out_features in zip(source_image.channels(), target_image.channel_stacks(step=self.dimension)):
                self._do_compute(source_channel, out=out_features)
        return target

    @abstractmethod
    def _do_compute(self, source:ScalarImage, out:Image):
        pass

class FeatureCollection(FlatChannelwiseFilter):
    def __init__(self, *features:List[FeatureExtractor]):
        assert len(features) > 0
        self.features = features

    @property
    def dimension(self):
        return sum(f.dimension for f in self.features)

    def _do_compute(self, source:ScalarImage, out:Image):
        channel_count = 0
        for f in self.features:
            channel_stop = channel_count + f.dimension
            feature_out = out.cut_with(c=slice(channel_count, channel_stop))
            f._do_compute(source, out=feature_out)
            channel_count = channel_stop
