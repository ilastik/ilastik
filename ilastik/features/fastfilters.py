from abc import abstractmethod
from dataclasses import dataclass
from typing import Optional

import vigra
import fastfilters
import numpy

from .feature_extractor import ChannelwiseFilter, FeatureData
from ndstructs import Array5D, Image, ScalarImage
from ndstructs import Point5D, Slice5D, Shape5D
from ndstructs.datasource import DataSource, BackedSlice5D

class ChannelwiseFastFilter(ChannelwiseFilter):
    def __init__(self, axis_2d: Optional[str] = None):
        super().__init__(axis_2d=axis_2d)

    def __repr__(self):
        props = " ".join(f"{k}={v}" for k,v in self.__dict__.items())
        return f"<{self.__class__.__name__} {props}>"

    @abstractmethod
    def filter_fn(self, source_raw: numpy.ndarray) -> numpy.ndarray:
        pass

    @property
    def kernel_shape(self) -> Shape5D:
        #FIXME: Add appropriate "kernel_shape" property to filters
        args = {k:5 for k in Point5D.SPATIAL_LABELS}
        if self.axis_2d:
            args[self.axis_2d] = 1
        return Shape5D(**args)

    def _compute_slice(self, source_roi:BackedSlice5D, out:FeatureData):
        source_axes = "xyz"
        if self.axis_2d:
            source_axes = source_axes.replace(self.axis_2d, "")
        target_axes = source_axes
        if self.channel_multiplier > 1:
            target_axes += 'c'

        source_raw = source_roi.enlarged(self.halo).retrieve().raw(source_axes).astype(numpy.float32)
        target_raw = out.raw(target_axes)

        feature_slices = list(source_roi.shape.to_slice_5d().translated(self.halo).with_full_c().to_slices(target_axes))
        raw_features = self.filter_fn(source_raw)
        target_raw[...] = raw_features[feature_slices]


class StructureTensorEigenvalues(ChannelwiseFastFilter):
    def __init__(self, innerScale:float, outerScale: float, window_size:float=0, axis_2d: Optional[str] = None):
        super().__init__(axis_2d=axis_2d)
        self.innerScale = innerScale
        self.outerScale = outerScale
        self.window_size = window_size

    def filter_fn(self, source_raw: numpy.ndarray) -> numpy.ndarray:
        return fastfilters.structureTensorEigenvalues(
            source_raw,
            innerScale=self.innerScale,
            outerScale=self.outerScale,
            window_size=self.window_size
        )

    @property
    def channel_multiplier(self) -> int:
        return 2 if self.axis_2d else 3



class SigmaWindowFilter(ChannelwiseFastFilter):
    def __init__(self, sigma: float, window_size:float = 0, axis_2d: Optional[str] = None):
        super().__init__(axis_2d=axis_2d)
        self.sigma = sigma
        self.window_size = window_size

class GaussianGradientMagnitude(SigmaWindowFilter):
    def filter_fn(self, source_raw:numpy.ndarray) -> numpy.ndarray:
        return fastfilters.gaussianGradientMagnitude(source_raw, sigma=self.sigma, window_size=self.window_size)

class GaussianSmoothing(SigmaWindowFilter):
    def filter_fn(self, source_raw: numpy.ndarray) -> numpy.ndarray:
        return fastfilters.gaussianSmoothing(source_raw, sigma=self.sigma, window_size=self.window_size)

class DifferenceOfGaussians(ChannelwiseFastFilter):
    def __init__(self, sigma0:float, sigma1: float, window_size:float=0, axis_2d: Optional[str] = None):
        super().__init__(axis_2d=axis_2d)
        self.sigma0 = sigma0
        self.sigma1 = sigma1
        self.window_size = window_size

    def __repr__(self):
        return f"<{self.__class__.__name__} sigma0:{self.sigma0} sigma1:{self.sigma1} window_size:{self.window_size} axis_2d:{self.axis_2d}>"

    def filter_fn(self, source_raw: numpy.ndarray) -> numpy.ndarray:
        a = fastfilters.gaussianSmoothing(source_raw, sigma=self.sigma0, window_size=self.window_size)
        b = fastfilters.gaussianSmoothing(source_raw, sigma=self.sigma1, window_size=self.window_size)
        return a - b


class ScaleWindowFilter(ChannelwiseFastFilter):
    def __init__(self, scale: float, window_size:float=0, axis_2d: Optional[str] = None):
        super().__init__(axis_2d=axis_2d)
        self.scale = scale
        self.window_size = window_size

    @classmethod
    def from_ilastik_scale(cls, scale: float):
        return cls(scale)

class HessianOfGaussianEigenvalues(ScaleWindowFilter):
    def filter_fn(self, source_raw: numpy.ndarray) -> numpy.ndarray:
        return fastfilters.hessianOfGaussianEigenvalues(source_raw, scale=self.scale, window_size=self.window_size)

    @property
    def channel_multiplier(self) -> int:
        return 2 if self.axis_2d else 3

class LaplacianOfGaussian(ScaleWindowFilter):
    def filter_fn(self, source_raw: numpy.ndarray) -> numpy.ndarray:
        return fastfilters.laplacianOfGaussian(source_raw, scale=self.scale, window_size=self.window_size)
