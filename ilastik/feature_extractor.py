from abc import ABC, abstractmethod

import vigra.filters
import numpy

from ilastik.array5d import Array5D, Slice5D, Point5D, Shape5D

class FeatureExtractor(ABC):
    def __init__(self, sigma:float, window_size:float):
        self.sigma = sigma
        self.window_size = window_size

    @abstractmethod
    def getFeature(self, roi, out=None):
        pass

class GaussianSmoothing(FeatureExtractor):
    def __init__(self, sigma:float, window_size:float=0.0):
        super().__init__(sigma=sigma, window_size=window_size)

    def getFeature(self, source:Array5D, roi:Slice5D=None, out:Array5D=None) -> Array5D:
        target = out or Array5D.allocate(source.shape_5d, dtype=source.dtype)
        assert source.shape_5d == target.shape_5d
        for t, tp in enumerate(source.timeIter()):
            for z, slc in enumerate(tp.sliceIter()):
                outslice = target.cut(Slice5D(t=t, z=z)).as_xyc()
                vigra.filters.gaussianSmoothing(slc.as_xyc(), sigma=self.sigma, out=outslice)
        return target

