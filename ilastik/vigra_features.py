from abc import abstractmethod

import vigra

from .feature_extractor import FlatChannelwiseFilter
from ilastik.array5d import Array5D, Image, ScalarImage

class VigraChannelwiseFilter(FlatChannelwiseFilter):
    @property
    @abstractmethod
    def filter_fn(self):
        pass

    def _do_compute(self, source:ScalarImage, out:Image):
        return self.filter_fn(source.raw().squeeze(),
                              sigma=self.sigma, window_size=self.window_size,
                              out=out.raw().squeeze())

class GaussianSmoothing(VigraChannelwiseFilter):
    @property
    def output_channels(self) -> int:
        return 1

    @property
    def filter_fn(self):
        return vigra.filters.gaussianSmoothing

    def allocate_for(self, source:Array5D) -> Array5D:
        #gaussian doesn't have to necessarily output in float
        return Array5D.allocate(source.shape, dtype=source.dtype)

class HessianOfGaussian(VigraChannelwiseFilter):
    @property
    def output_channels(self) -> int:
        return 3

    @property
    def filter_fn(self):
        return vigra.filters.hessianOfGaussian

