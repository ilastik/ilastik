from abc import ABC, abstractmethod

import vigra.filters
import numpy

from ilastik.array5d import Array5D, Slice5D, Point5D, Shape5D

class FeatureExtractor(ABC):
    def __init__(self, sigma:float, window_size:float):
        self.sigma = sigma
        self.window_size = window_size

    def allocate_for(self, source:Array5D) -> Array5D:
        shape = source.shape_5d
        output_shape = shape.with_axis_as('c', shape.c * self.output_channels)
        return Array5D.allocate(output_shape, dtype=numpy.float32)

    @abstractmethod
    def compute(self, roi, out=None):
        pass

class BasicPerChannelFilter(FeatureExtractor):
    def __init__(self, sigma:float, window_size:float=0.0):
        super().__init__(sigma=sigma, window_size=window_size)

    @property
    @abstractmethod
    def output_channels(self) -> int:
        pass

    def compute(self, source:Array5D, roi:Slice5D=None, out:Array5D=None) -> Array5D:
        target = out or self.allocate_for(source)
        assert source.shape_5d == target.shape_5d
        for t, tp in enumerate(source.timeIter()):
            for z, z_slice in enumerate(tp.sliceIter()):
                for c, c_slice in enumerate(z_slice.channelIter()):
                    out_slice = Slice5D(t=t, z=z, c=slice(c, c+self.output_channels))
                    self._do_compute(c_slice, out=target.cut(out_slice))
        return target

    @abstractmethod
    def _do_compute(self, source:Array5D, out:Array5D):
        pass

class GaussianSmoothing(BasicPerChannelFilter):
    @property
    def output_channels(self) -> int:
        return 1

    def allocate_for(self, source:Array5D) -> Array5D:
        return Array5D.allocate(source.shape_5d, dtype=source.dtype)

    def _do_compute(self, source_slice:Array5D, out:Array5D):
        #import pydevd; pydevd.settrace()
        return vigra.filters.gaussianSmoothing(source_slice.raw_xy(), sigma=self.sigma,
                                               out=out.raw_xy(),
                                               window_size=self.window_size)

class HessianOfGaussian(BasicPerChannelFilter):
    @property
    def output_channels(self, source:Array5D) -> int:
        return 3

    def _do_compute(self, source_slice:Array5D, out:Array5D):
        return vigra.filters.hessianOfGaussian(source_slice.raw_xy(), sigma=self.sigma,
                                               out=out.raw_xyc(),
                                               window_size=self.window_size)


