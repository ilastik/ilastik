from abc import abstractmethod
from dataclasses import dataclass

import vigra
import numpy

from .feature_extractor import FlatChannelwiseFilter, FeatureData
from ilastik.array5d import Array5D, Image, ScalarImage
from ilastik.array5d.point5D import Point5D, Slice5D, Shape5D
from ilastik.data_source import DataSourceSlice

class VigraChannelwiseFilter(FlatChannelwiseFilter):
    def __init__(self, sigma:float, window_size:float=0, stack_axis:str='z'):
        super().__init__(stack_axis=stack_axis)
        self.sigma = sigma
        self.window_size = window_size

    def __repr__(self):
        return f"<{self.__class__.__name__} sigma:{self.sigma} window_size:{self.window_size} stack_axis:{self.stack_axis}>"

    @property
    @abstractmethod
    def filter_fn(self):
        pass

    @property
    def kernel_shape(self) -> Shape5D:
        #FIXME: Add appropriate "kernel_shape" property to filters
        args = {k:5 for k in Point5D.SPATIAL_LABELS}
        args[self.stack_axis] = 1
        return Shape5D(**args)

    def _compute_slice(self, source_roi:DataSourceSlice, out:FeatureData):
        source = ScalarImage.fromArray5D(source_roi.retrieve(self.halo))
        source_axes = source.squeezed_shape.axiskeys
        vigra_roi = out.shape.to_slice_5d().offset(self.halo).to_tuple(source_axes)
        return self.filter_fn(source.raw(source_axes).astype(numpy.float32),
                              sigma=self.sigma, window_size=self.window_size,
                              out=out.raw(source_axes + 'c'),
                              roi=vigra_roi)

#FIXME: Add appropriate "kernel_shape" property to filters
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

