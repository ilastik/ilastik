from abc import abstractmethod
from dataclasses import dataclass
from typing import Optional, TypeVar

import vigra
import fastfilters
import numpy

from .feature_extractor import FeatureData
from .ilp_filter import IlpFilter
from ndstructs import Array5D, Image, ScalarImage
from ndstructs import Point5D, Slice5D, Shape5D
from ndstructs.datasource import DataSource, DataSourceSlice


class ChannelwiseFastFilter(IlpFilter):
    def __init__(self, *, num_input_channels: int, axis_2d: Optional[str] = None):
        super().__init__(axis_2d=axis_2d, num_input_channels=num_input_channels)

    def __repr__(self):
        props = " ".join(f"{k}={v}" for k, v in self.__dict__.items())
        return f"<{self.__class__.__name__} {props}>"

    @abstractmethod
    def filter_fn(self, source_raw: numpy.ndarray) -> numpy.ndarray:
        pass

    @property
    def kernel_shape(self) -> Shape5D:
        # FIXME: Add appropriate "kernel_shape" property to filters
        args = {k: 5 for k in Point5D.SPATIAL_LABELS}
        if self.axis_2d:
            args[self.axis_2d] = 1
        return Shape5D(**args)

    def _compute_slice(self, source_roi: DataSourceSlice, out: FeatureData):
        source_axes = "xyz"
        if self.axis_2d:
            source_axes = source_axes.replace(self.axis_2d, "")
        target_axes = source_axes
        if self.channel_multiplier > 1:
            target_axes += "c"

        source_raw = source_roi.enlarged(self.halo).retrieve().raw(source_axes).astype(numpy.float32)
        target_raw = out.raw(target_axes)

        feature_slices = list(source_roi.shape.to_slice_5d().translated(self.halo).with_full_c().to_slices(target_axes))
        raw_features = self.filter_fn(source_raw)
        target_raw[...] = raw_features[feature_slices]


class StructureTensorEigenvalues(ChannelwiseFastFilter):
    def __init__(
        self,
        *,
        innerScale: float,
        outerScale: float,
        num_input_channels: int,
        window_size: float = 0,
        axis_2d: Optional[str] = None,
    ):
        super().__init__(axis_2d=axis_2d, num_input_channels=num_input_channels)
        self.innerScale = innerScale
        self.outerScale = outerScale
        self.window_size = window_size

    def filter_fn(self, source_raw: numpy.ndarray) -> numpy.ndarray:
        return fastfilters.structureTensorEigenvalues(
            source_raw, innerScale=self.innerScale, outerScale=self.outerScale, window_size=self.window_size
        )

    @property
    def channel_multiplier(self) -> int:
        return 2 if self.axis_2d else 3

    @classmethod
    def from_ilp_scale(
        cls, *, scale: float, num_input_channels: int, axis_2d: Optional[str] = None
    ) -> "StructureTensorEigenvalues":
        return cls(innerScale=scale, outerScale=0.5 * scale, axis_2d=axis_2d, num_input_channels=num_input_channels)

    @property
    def ilp_scale(self) -> float:
        return self.innerScale


IlpFilter.REGISTRY[StructureTensorEigenvalues.__name__] = StructureTensorEigenvalues


SigmaFilter = TypeVar("SigmaFilter", bound="SigmaWindowFilter")


class SigmaWindowFilter(ChannelwiseFastFilter):
    def __init__(self, *, sigma: float, num_input_channels: int, window_size: float = 0, axis_2d: Optional[str] = None):
        super().__init__(axis_2d=axis_2d, num_input_channels=num_input_channels)
        self.sigma = sigma
        self.window_size = window_size

    @classmethod
    def from_ilp_scale(
        cls: SigmaFilter, scale: float, num_input_channels: int, axis_2d: Optional[str] = None
    ) -> SigmaFilter:
        return cls(sigma=scale, axis_2d=axis_2d, num_input_channels=num_input_channels)

    @property
    def ilp_scale(self) -> float:
        return self.sigma


class GaussianGradientMagnitude(SigmaWindowFilter):
    def filter_fn(self, source_raw: numpy.ndarray) -> numpy.ndarray:
        return fastfilters.gaussianGradientMagnitude(source_raw, sigma=self.sigma, window_size=self.window_size)


IlpFilter.REGISTRY[GaussianGradientMagnitude.__name__] = GaussianGradientMagnitude


class GaussianSmoothing(SigmaWindowFilter):
    def filter_fn(self, source_raw: numpy.ndarray) -> numpy.ndarray:
        return fastfilters.gaussianSmoothing(source_raw, sigma=self.sigma, window_size=self.window_size)


IlpFilter.REGISTRY[GaussianSmoothing.__name__] = GaussianSmoothing


class DifferenceOfGaussians(ChannelwiseFastFilter):
    def __init__(
        self,
        *,
        sigma0: float,
        sigma1: float,
        num_input_channels: int,
        window_size: float = 0,
        axis_2d: Optional[str] = None,
    ):
        super().__init__(axis_2d=axis_2d, num_input_channels=num_input_channels)
        self.sigma0 = sigma0
        self.sigma1 = sigma1
        self.window_size = window_size

    def __repr__(self):
        return f"<{self.__class__.__name__} sigma0:{self.sigma0} sigma1:{self.sigma1} window_size:{self.window_size} axis_2d:{self.axis_2d}>"

    def filter_fn(self, source_raw: numpy.ndarray) -> numpy.ndarray:
        a = fastfilters.gaussianSmoothing(source_raw, sigma=self.sigma0, window_size=self.window_size)
        b = fastfilters.gaussianSmoothing(source_raw, sigma=self.sigma1, window_size=self.window_size)
        return a - b

    @classmethod
    def from_ilp_scale(
        cls, scale: float, num_input_channels: int, axis_2d: Optional[str] = None
    ) -> "DifferenceOfGaussians":
        return cls(sigma0=scale, sigma1=scale * 0.66, axis_2d=axis_2d, num_input_channels=num_input_channels)

    @property
    def ilp_scale(self) -> float:
        return self.sigma0


IlpFilter.REGISTRY[DifferenceOfGaussians.__name__] = DifferenceOfGaussians


ScaleFilter = TypeVar("ScaleFilter", bound="ScaleWindowFilter")


class ScaleWindowFilter(ChannelwiseFastFilter):
    def __init__(self, *, scale: float, num_input_channels: int, window_size: float = 0, axis_2d: Optional[str] = None):
        super().__init__(axis_2d=axis_2d, num_input_channels=num_input_channels)
        self.scale = scale
        self.window_size = window_size

    @classmethod
    def from_ilp_scale(
        cls: ScaleFilter, scale: float, num_input_channels: int, axis_2d: Optional[str] = None
    ) -> ScaleFilter:
        return cls(scale=scale, axis_2d=axis_2d, num_input_channels=num_input_channels)

    @property
    def ilp_scale(self) -> float:
        return self.scale


class HessianOfGaussianEigenvalues(ScaleWindowFilter):
    def filter_fn(self, source_raw: numpy.ndarray) -> numpy.ndarray:
        return fastfilters.hessianOfGaussianEigenvalues(source_raw, scale=self.scale, window_size=self.window_size)

    @property
    def channel_multiplier(self) -> int:
        return 2 if self.axis_2d else 3


IlpFilter.REGISTRY[HessianOfGaussianEigenvalues.__name__] = HessianOfGaussianEigenvalues


class LaplacianOfGaussian(ScaleWindowFilter):
    def filter_fn(self, source_raw: numpy.ndarray) -> numpy.ndarray:
        return fastfilters.laplacianOfGaussian(source_raw, scale=self.scale, window_size=self.window_size)


IlpFilter.REGISTRY[LaplacianOfGaussian.__name__] = LaplacianOfGaussian
