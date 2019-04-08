from abc import ABC, abstractmethod

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

    @property
    @abstractmethod
    def output_channels(self) -> int:
        pass

    def get_expected_shape(self, source:Array5D):
        shape = source.shape
        return shape.with_coord(c=shape.c * self.output_channels)

    @abstractmethod
    def compute(self, roi, out=None):
        pass

class FlatChannelwiseFilter(FeatureExtractor):
    def __init__(self, sigma:float, window_size:float=0.0):
        super().__init__(sigma=sigma, window_size=window_size)

    def compute(self, source:Array5D, roi:Slice5D=None, out:Array5D=None) -> Array5D:
        target = out or self.allocate_for(source)
        assert target.shape == self.get_expected_shape(source)
        for source_image, target_image in zip(source.imageIter(), target.imageIter()):
            for c, source_channel in enumerate(source_image.channelIter()):
                out = target_image.cut_with(c=slice(c, c+self.output_channels))
                self._do_compute(source_channel, out=out)
        return target

    @abstractmethod
    def _do_compute(self, source:ScalarImage, out:Image):
        pass
