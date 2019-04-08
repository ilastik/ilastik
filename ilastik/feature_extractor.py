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
        output_shape = shape.with_coord(c=shape.c * self.output_channels)
        return Array5D.allocate(output_shape, dtype=numpy.float32)

    @abstractmethod
    def compute(self, roi, out=None):
        pass

class FlatChannelwiseFilter(FeatureExtractor):
    def __init__(self, sigma:float, window_size:float=0.0):
        super().__init__(sigma=sigma, window_size=window_size)

    @property
    @abstractmethod
    def output_channels(self) -> int:
        pass

    def compute(self, source:Array5D, roi:Slice5D=None, out:Array5D=None) -> Array5D:
        target = out or self.allocate_for(source)
        for t, tp in enumerate(source.timeIter()):
            for z, z_slice in enumerate(tp.sliceIter()):
                for c, c_slice in enumerate(z_slice.channelIter()):
                    out_slice = Slice5D(t=t, z=z, c=slice(c, c+self.output_channels))
                    self._do_compute(c_slice, out=target.cut(out_slice))
        return target

    @abstractmethod
    def _do_compute(self, source:Array5D, out:Array5D):
        pass
