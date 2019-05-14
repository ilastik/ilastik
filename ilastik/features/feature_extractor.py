from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor as Executor
from functools import reduce
from operator import mul
from typing import List, Iterator

import vigra.filters
import numpy as np

from ilastik.array5d import Slice5D, Point5D, Shape5D
from ilastik.array5d import Array5D, Image, ScalarImage, LinearData
from ilastik.data_source import DataSource, DataSpec

class FeatureData(Array5D):
    def __init__(self, arr:np.ndarray, axiskeys:str):
        #FIXME:
        #assert arr.dtype == np.float32
        super().__init__(arr, axiskeys)

    def as_uint8(self):
        return Array5D((self._data * 255).astype(np.uint8), axiskeys=self.axiskeys)

class FeatureDataMismatchException(Exception):
    def __init__(self, feature_extractor:'FeatureExtractor', data_source:DataSource):
        super().__init__(f"Feature {feature_extractor} can't be cleanly applied to {data_source}")

class FeatureExtractor(ABC):
    def __init__(self, sigma:float, window_size:float):
        self.sigma = sigma
        self.window_size = window_size

    def __repr__(self):
        return f"<{self.__class__.__name__} sigma={self.sigma} window_size={self.window_size} kernel={self.kernel_shape}>"

    def allocate_for(self, roi:DataSpec) -> Array5D:
        #FIXME: vigra needs C to be the last REAL axis rather than the last axis of the view -.-
        return FeatureData.allocate(self.get_expected_shape(roi), dtype=np.float32, axiskeys='tzxyc')

    @abstractmethod
    def get_expected_shape(self, roi:DataSpec) -> Shape5D:
        pass

    @abstractmethod
    def compute(self, roi:DataSpec, out:Array5D=None) -> Array5D:
        pass

    def is_applicable_to(self, data:DataSource) -> bool:
        return data.shape >= self.kernel_shape

    def ensure_applicable(self, data_source:DataSource):
        if not self.is_applicable_to(data_source):
            raise FeatureDataMismatchException(self, data_source)

    @property
    @abstractmethod
    def kernel_shape(self) -> Shape5D:
        pass

    @property
    def halo(self) -> Point5D:
        return self.kernel_shape // 2

class FlatChannelwiseFilter(FeatureExtractor):
    def __init__(self, sigma:float, window_size:float=0.0, stack_axis:str='z'):
        super().__init__(sigma=sigma, window_size=window_size)
        self.stack_axis = stack_axis

    @property
    @abstractmethod
    def dimension(self) -> int:
        "Number of channels emited by this feature extractor for each input channel"
        pass

    def get_expected_shape(self, roi:DataSpec) -> Shape5D:
        num_output_channels = roi.shape.c * self.dimension
        return roi.shape.with_coord(c=num_output_channels)

    def compute(self, roi:DataSpec, out:Array5D=None) -> Array5D:
        data = roi.retrieve(self.halo)
        target = out or self.allocate_for(roi) #N.B.: target has no halo
        assert target.shape == self.get_expected_shape(roi)

        with Executor(thread_name_prefix="feature_slice") as executor:
            for source_image, target_image in zip(data.images(self.stack_axis), target.images(self.stack_axis)):
                for source_channel, out_features in zip(source_image.channels(), target_image.channel_stacks(step=self.dimension)):
                    executor.submit(self._compute_slice, source_channel, out=out_features)
        return target

    @abstractmethod
    def _compute_slice(self, raw_data:ScalarImage, out:Image):
        pass

class FeatureCollection(FeatureExtractor):
    def __init__(self, *features:List[FeatureExtractor]):
        assert len(features) > 0
        self.features = features

        shape_params = {}
        for label in Point5D.LABELS:
            shape_params[label] = max(f.kernel_shape[label] for f in features)
        self._kernel_shape = Shape5D(**shape_params)

    def __repr__(self):
        return f"<{self.__class__.__name__} {[repr(f) for f in self.features]}>"

    @property
    def kernel_shape(self):
        return self._kernel_shape

    def get_expected_shape(self, roi:DataSpec) -> Shape5D:
        channel_size = sum(f.get_expected_shape(roi).c for f in self.features)
        return roi.shape.with_coord(c=channel_size)

    def compute(self, roi:DataSpec, out:Array5D=None) -> Array5D:
        data = roi.retrieve(self.halo)
        target = out or self.allocate_for(roi)
        assert target.shape == self.get_expected_shape(roi)

        with Executor(max_workers=len(self.features), thread_name_prefix="features") as executor:
            channel_count = 0
            for f in self.features:
                channel_stop = channel_count + f.get_expected_shape(roi).c
                feature_out = target.cut_with(c=slice(channel_count, channel_stop))
                executor.submit(f.compute, roi, out=feature_out)
                channel_count = channel_stop
        return target
