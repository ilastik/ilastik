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

    @property
    def radius(self):
        return 0

    def _do_compute(self, source:ScalarImage, out:Image):
        out_axes = source.squeezed_shape.axiskeys

        slice_offset = Point5D.zero(**{k:self.radius for k in out_axes})
        out.to_slice_5d().translated(slice_offset)

        out_feature_axes = out_axes + 'c'
        vigra_roi_end = out.raw(out_axes).shape
        vigra_roi_begin = (0)out.raw(out_axes).shape
        feature_data = self.filter_fn(source.raw(out_axes).astype(numpy.float32),
                              sigma=self.sigma, window_size=self.window_size)
                              #out=out.raw(out_feature_axes))
        out

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

