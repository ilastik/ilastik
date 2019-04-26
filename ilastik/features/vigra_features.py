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

        slice_offset = (source.shape - out.shape) / 2
        out_slice = out.shape.to_slice_5d().translated(slice_offset)
        vigra_roi = out_slice.to_tuple(out_axes)

        return self.filter_fn(source.raw(out_axes).astype(numpy.float32),
                              sigma=self.sigma, window_size=self.window_size,
                              out=out.raw(out_axes + 'c'),
                              roi=vigra_roi)

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

