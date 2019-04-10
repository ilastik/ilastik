from abc import abstractmethod

import vigra
import numpy

from .feature_extractor import FlatChannelwiseFilter
from ilastik.array5d import Array5D, Image, ScalarImage

class VigraChannelwiseFilter(FlatChannelwiseFilter):
    @property
    @abstractmethod
    def filter_fn(self):
        pass

    def _do_compute(self, source:ScalarImage, out:Image):
        return self.filter_fn(source.raw().squeeze().astype(numpy.float32),
                              sigma=self.sigma, window_size=self.window_size,
                              out=out.raw().squeeze())

class GaussianSmoothing(VigraChannelwiseFilter):
    @property
    def dimension(self) -> int:
        return 1

    @property
    def filter_fn(self):
        return vigra.filters.gaussianSmoothing

class HessianOfGaussian(VigraChannelwiseFilter):
    @property
    def dimension(self) -> int:
        return 3

    @property
    def filter_fn(self):
        return vigra.filters.hessianOfGaussian

