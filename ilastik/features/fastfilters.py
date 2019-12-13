from abc import abstractmethod
from dataclasses import dataclass

import vigra
import fastfilters
import numpy

from .feature_extractor import FlatChannelwiseFilter, FeatureData
from ndstructs import Array5D, Image, ScalarImage
from ndstructs import Point5D, Slice5D, Shape5D
from ndstructs.datasource import DataSource

class ChannelwiseFastFilter(FlatChannelwiseFilter):
    def __init__(self, stack_axis:str='z'):
        super().__init__(stack_axis=stack_axis)

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
        args[self.stack_axis] = 1
        return Shape5D(**args)

    def _compute_slice(self, source_roi:DataSource, out:FeatureData):
        source = ScalarImage.fromArray5D(source_roi.enlarged(self.halo).retrieve())
        source_axes = source.squeezed_shape.axiskeys
        source_raw = source.raw(source_axes).astype(numpy.float32)

        target_raw = out.raw(source_axes + 'c').squeeze()
        feature_slices = list(source_roi.shape.to_slice_5d().translated(self.halo).with_full_c().to_slices(source_axes))
        if self.get_channel_multiplier(source_roi) > 1:
            feature_slices.append(slice(None))

        raw_features = self.filter_fn(source_raw)
        target_raw[...] = raw_features[feature_slices]

class SigmaWindowFilter(ChannelwiseFastFilter):
    def __init__(self, sigma: float, window_size:float = 0, stack_axis:str="z"):
        super().__init__(stack_axis=stack_axis)
        self.sigma = sigma
        self.window_size = window_size


class ScaleWindowFilter(ChannelwiseFastFilter):
    def __init__(self, scale: float, window_size:float=0, stack_axis:str="z"):
        super().__init__(stack_axis=stack_axis)
        self.scale = scale
        self.window_size = window_size


class GaussianSmoothing(SigmaWindowFilter):
    def filter_fn(self, source_raw: numpy.ndarray) -> numpy.ndarray:
        return fastfilters.gaussianSmoothing(source_raw, sigma=self.sigma, window_size=self.window_size)


class DifferenceOfGaussians(ChannelwiseFastFilter):
    def __init__(self, sigma0:float, sigma1: float, window_size:float=0, stack_axis:str='z'):
        super().__init__(stack_axis=stack_axis)
        self.sigma0 = sigma0
        self.sigma1 = sigma1

    def __repr__(self):
        return f"<{self.__class__.__name__} sigma0:{self.sigma0} sigma1:{self.sigma1} window_size:{self.window_size} stack_axis:{self.stack_axis}>"

    def filter_fn(self, source_raw: numpy.ndarray) -> numpy.ndarray:
        a = fastfilters.gaussianSmoothing(source_raw, sigma=self.sigma0, window_size=self.window_size)
        b = fastfilters.gaussianSmoothing(source_raw, sigma=self.sigma1, window_size=self.window_size)
        return a - b


class HessianOfGaussianEigenvalues(ScaleWindowFilter):
    def filter_fn(self, source_raw: numpy.ndarray) -> numpy.ndarray:
        return fastfilters.hessianOfGaussianEigenvalues(source_raw, scale=self.scale, window_size=self.window_size)

    def get_channel_multiplier(self, roi:Slice5D) -> int:
        return len(roi.present_spatial_axes())


class StructureTensorEigenvalues(ChannelwiseFastFilter):
    def __init__(self, innerScale:float, outerScale: float, window_size:float=0, stack_axis:str='z'):
        super().__init__(stack_axis=stack_axis)
        self.innerScale = innerScale
        self.innerScale = innerScale

    def filter_fn(self, source_raw: numpy.ndarray) -> numpy.ndarray:
        return fastfilters.structureTensorEigenvalues(
            source_raw,
            innerScale=self.innerScale,
            outerScale=self.outerScale,
            window_size=self.window_size
        )

    def get_channel_multiplier(self, roi:Slice5D) -> int:
        return len(roi.present_spatial_axes())


class GaussianGradientMagnitude(SigmaWindowFilter):
    def filter_fn(self, source_raw:numpy.ndarray) -> numpy.ndarray:
        return fastfilters.gaussianGradientMagnitude(source_raw, sigma=self.sigma, window_size=self.window_size)


class LaplacianOfGaussian(ScaleWindowFilter):
    def filter_fn(self, source_raw: numpy.ndarray) -> numpy.ndarray:
        return fastfilters.laplacianOfGaussian(source_raw, scale=self.scale, window_size=self.window_size)
