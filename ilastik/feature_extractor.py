from abc import ABC, abstractmethod

import vigra.filters
import numpy

from ilastik.array5d import Array5D, Roi5D, Point5D, Shape5D

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

    def getFeature(self, source:Array5D, roi:Roi5D=None, out:Array5D=None):
        target = out or Array5D.allocate(source.shape5D)
        for t, tp in enumerate(source.timeIter()):
            for z, slc in tp.sliceIter():
                if out is not None:
                    vigra.filters.gaussianSmoothing(slc, sigma=self.sigma, out=)

                out.assign_to_z_slice()

