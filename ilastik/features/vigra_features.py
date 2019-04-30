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
        source_axes = source.squeezed_shape.axiskeys
        vigra_roi = out.shape.to_slice_5d().offset(self.halo).to_tuple(source_axes)
        return self.filter_fn(source.raw(source_axes).astype(numpy.float32),
                              sigma=self.sigma, window_size=self.window_size,
                              out=out.raw(source_axes + 'c'),
                              roi=vigra_roi)

#FIXME: Add appropriate "halo" property to filters
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

