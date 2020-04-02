from abc import abstractmethod
from dataclasses import dataclass
from typing import Optional, TypeVar
import math
import fastfilters

import numpy

from .feature_extractor import FeatureData
from .ilp_filter import IlpFilter
from ndstructs import Array5D, Image, ScalarImage
from ndstructs import Point5D, Slice5D, Shape5D
from ndstructs.datasource import DataSource, DataSourceSlice


class ChannelwiseFastFilter(IlpFilter):
    def __init__(self, *, num_input_channels: int, axis_2d: Optional[str] = None, presmooth_sigma: float = 0):
        self.presmooth_sigma = presmooth_sigma
        super().__init__(axis_2d=axis_2d, num_input_channels=num_input_channels)

    @classmethod
    def from_json_data(cls, data):
        return from_json_data(cls, data)

    @classmethod
    def calc_presmooth_sigma(cls, scale: float) -> float:
        if scale > 1.0:
            return math.sqrt(scale ** 2 - 1.0)
        else:
            return scale

    def get_ilp_scale(self, capped_scale: float) -> float:
        if capped_scale < 1:
            return capped_scale
        if self.presmooth_sigma == 1.0:
            return 1.0
        # presmooth_sigma = math.sqrt(ilp_scale ** 2 - 1.0)
        # presmooth_sigma ** 2 = ilp_scale ** 2 - 1.0
        # presmooth_sigma ** 2 + 1 = ilp_scale ** 2
        # math.sqrt(presmooth_sigma ** 2 + 1) = ilp_scale
        return numpy.around(math.sqrt(self.presmooth_sigma ** 2 + 1), decimals=2)

    def __repr__(self):
        props = " ".join(f"{k}={v}" for k, v in self.__dict__.items())
        return f"<{self.__class__.__name__} {props}>"

    @abstractmethod
    def filter_fn(self, source_raw: numpy.ndarray) -> numpy.ndarray:
        pass

    @property
    def kernel_shape(self) -> Shape5D:
        # FIXME: Add appropriate "kernel_shape" property to filters
        args = {k: 30 for k in Point5D.SPATIAL_LABELS}
        if self.axis_2d:
            args[self.axis_2d] = 1
        return Shape5D(**args)

    def _compute_slice(self, source_roi: DataSourceSlice, out: FeatureData):
        assert source_roi.shape.c == 1 and source_roi.shape.t == 1
        haloed_roi = source_roi.enlarged(self.halo)
        if self.presmooth_sigma > 0:
            gaussian_filter = GaussianSmoothing(
                sigma=self.presmooth_sigma, axis_2d=self.axis_2d, window_size=3.5, num_input_channels=1
            )
            source_data = gaussian_filter.compute(haloed_roi)
        else:
            source_data = haloed_roi.retrieve()

        source_axes = "zyx"
        if self.axis_2d:
            source_axes = source_axes.replace(self.axis_2d, "")

        raw_data: numpy.ndarray = source_data.raw(source_axes).astype(numpy.float32)
        features = FeatureData(
            self.filter_fn(raw_data),
            axiskeys=source_axes + ("c" if self.channel_multiplier > 1 else ""),
            location=haloed_roi.start.with_coord(c=out.roi.start.c),
        )
        out.set(features, autocrop=True)


class StructureTensorEigenvalues(ChannelwiseFastFilter):
    def __init__(
        self,
        *,
        innerScale: float,
        outerScale: float,
        num_input_channels: int,
        window_size: float = 0,
        axis_2d: Optional[str] = None,
        presmooth_sigma: float = 0,
    ):
        super().__init__(axis_2d=axis_2d, num_input_channels=num_input_channels, presmooth_sigma=presmooth_sigma)
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
        capped_scale = min(scale, 1.0)
        return cls(
            innerScale=capped_scale,
            outerScale=0.5 * capped_scale,
            axis_2d=axis_2d,
            num_input_channels=num_input_channels,
            presmooth_sigma=cls.calc_presmooth_sigma(scale),
        )

    @property
    def ilp_scale(self) -> float:
        return self.get_ilp_scale(self.innerScale)


IlpFilter.REGISTRY[StructureTensorEigenvalues.__name__] = StructureTensorEigenvalues


SigmaFilter = TypeVar("SigmaFilter", bound="SigmaWindowFilter")


class SigmaWindowFilter(ChannelwiseFastFilter):
    def __init__(
        self,
        *,
        sigma: float,
        num_input_channels: int,
        window_size: float = 0,
        axis_2d: Optional[str] = None,
        presmooth_sigma: float = 0,
    ):
        super().__init__(axis_2d=axis_2d, num_input_channels=num_input_channels, presmooth_sigma=presmooth_sigma)
        self.sigma = sigma
        self.window_size = window_size

    @classmethod
    def from_ilp_scale(
        cls: SigmaFilter, scale: float, num_input_channels: int, axis_2d: Optional[str] = None
    ) -> SigmaFilter:
        return cls(
            sigma=min(scale, 1.0),
            axis_2d=axis_2d,
            num_input_channels=num_input_channels,
            presmooth_sigma=cls.calc_presmooth_sigma(scale),
        )

    @property
    def ilp_scale(self) -> float:
        return self.get_ilp_scale(self.sigma)


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
        presmooth_sigma: float = 0,
    ):
        super().__init__(axis_2d=axis_2d, num_input_channels=num_input_channels, presmooth_sigma=presmooth_sigma)
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
        capped_scale = min(scale, 1.0)
        return cls(
            sigma0=capped_scale,
            sigma1=capped_scale * 0.66,
            axis_2d=axis_2d,
            num_input_channels=num_input_channels,
            presmooth_sigma=cls.calc_presmooth_sigma(scale),
        )

    @property
    def ilp_scale(self) -> float:
        return self.get_ilp_scale(self.sigma0)


IlpFilter.REGISTRY[DifferenceOfGaussians.__name__] = DifferenceOfGaussians


ScaleFilter = TypeVar("ScaleFilter", bound="ScaleWindowFilter")


class ScaleWindowFilter(ChannelwiseFastFilter):
    def __init__(
        self,
        *,
        scale: float,
        num_input_channels: int,
        window_size: float = 0,
        axis_2d: Optional[str] = None,
        presmooth_sigma: float = 0,
    ):
        super().__init__(axis_2d=axis_2d, num_input_channels=num_input_channels, presmooth_sigma=presmooth_sigma)
        self.scale = scale
        self.window_size = window_size

    @classmethod
    def from_ilp_scale(
        cls: ScaleFilter, scale: float, num_input_channels: int, axis_2d: Optional[str] = None
    ) -> ScaleFilter:
        return cls(
            scale=min(scale, 1.0),
            axis_2d=axis_2d,
            num_input_channels=num_input_channels,
            presmooth_sigma=cls.calc_presmooth_sigma(scale),
        )

    @property
    def ilp_scale(self) -> float:
        return self.get_ilp_scale(self.scale)


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
