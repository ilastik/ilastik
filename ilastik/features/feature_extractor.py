from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor as Executor
from dataclasses import dataclass
import functools
from operator import mul
from typing import List, Iterable, Tuple

import numpy as np

from ndstructs import Slice5D, Point5D, Shape5D
from ndstructs import Array5D, Image, ScalarImage, LinearData
from ndstructs.datasource import DataSource
from ndstructs.utils import JsonSerializable

class FeatureData(Array5D):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #FIXME:
        #assert arr.dtype == np.float32

    def as_pil_images(self):
        return self.as_uint8().as_pil_images()

    def show(self):
        return self.as_uint8().show_channels()

class FeatureDataMismatchException(Exception):
    def __init__(self, feature_extractor:'FeatureExtractor', data_source:DataSource):
        super().__init__(f"Feature {feature_extractor} can't be cleanly applied to {data_source}")


class FeatureExtractor(JsonSerializable):
    """A specification of how feature data is to be (reproducibly) computed"""

    def __hash__(self):
        return hash((self.__class__, tuple(self.__dict__.values())))

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.__dict__ == other.__dict__

    @abstractmethod
    def get_expected_roi(self, input_roi:DataSource, channel_offset:int=0) -> Shape5D:
        pass

    def allocate_for(self, input_roi:DataSource, channel_offset:int=0) -> FeatureData:
        #FIXME: vigra needs C to be the last REAL axis rather than the last axis of the view -.-
        out_roi = self.get_expected_roi(input_roi, channel_offset)
        return FeatureData.allocate(out_roi, dtype=np.float32, axiskeys='tzyxc')

    @functools.lru_cache()
    def compute(self, input_roi:DataSource, channel_offset:int=0) -> FeatureData:
        out_features = self.allocate_for(input_roi, channel_offset)
        self.compute_into(input_roi, out_features)
        out_features.setflags(write=False)
        return out_features

    @abstractmethod
    def compute_into(self, input_roi:DataSource, out:FeatureData) -> FeatureData:
        pass

    def is_applicable_to(self, data_slice:DataSource) -> bool:
        return data_slice.shape >= self.kernel_shape

    def ensure_applicable(self, data_slice:DataSource):
        if not self.is_applicable_to(data_slice):
            raise FeatureDataMismatchException(self, data_slice)

    @property
    @abstractmethod
    def kernel_shape(self) -> Shape5D:
        pass

    @property
    def halo(self) -> Point5D:
        return self.kernel_shape // 2


class ChannelwiseFeatureExtractor(FeatureExtractor):
    def get_channel_multiplier(self, roi:Slice5D) -> int:
        "Number of channels emited by this feature extractor for each input channel"
        return 1

    def get_expected_roi(self, datasource:DataSource, channel_offset:int=0) -> Shape5D:
        num_output_channels = datasource.shape.c * self.get_channel_multiplier(datasource)
        c_start = channel_offset
        c_stop = c_start + num_output_channels
        return Slice5D(**{**datasource.to_dict(), "c":slice(c_start, c_stop)})

class FlatChannelwiseFilter(ChannelwiseFeatureExtractor):
    """A Feature extractor with a 2D kernel that computes independently for every
    spatial slice and for every channel in its input"""

    def __init__(self, stack_axis:str='z'):
        super().__init__()
        self.stack_axis = stack_axis

    def compute_into(self, input_roi:DataSource, out:FeatureData) -> FeatureData:
        for source_image_roi, out_image in zip(input_roi.images(self.stack_axis), out.images(self.stack_axis)):
            out_channel_stacks = out_image.channel_stacks(step=self.get_channel_multiplier(source_image_roi))
            for source_channel_roi, out_features in zip(source_image_roi.channels(), out_channel_stacks):
                self._compute_slice(source_channel_roi, out=out_features)
        return out

    @abstractmethod
    def _compute_slice(self, raw_data:DataSource, out:Image):
        pass

    def _debug_show(self, rawData: DataSource, featureData: FeatureData):
        channel_multiplier = int(featureData.shape.c / rawData.shape.c)
        assert channel_multiplier == self.get_channel_multiplier(rawData)
        print(f"Showing features as a group of  {channel_multiplier}-channel images")
        for channel_stack in featureData.channel_stacks(channel_multiplier):
            channel_stack.as_uint8(normalized=False).show_images()


class FeatureExtractorCollection(ChannelwiseFeatureExtractor):
    def __init__(self, extractors:Iterable[FeatureExtractor]):
        assert len(extractors) > 0
        self.extractors = tuple(extractors)

        shape_params = {}
        for label in Point5D.LABELS:
            shape_params[label] = max(f.kernel_shape[label] for f in extractors)
        self._kernel_shape = Shape5D(**shape_params)

    @classmethod
    @functools.lru_cache()
    def get(cls, extractors:Tuple[FeatureExtractor]):
        return cls(extractors)

    def __repr__(self):
        return f"<{self.__class__.__name__} {[repr(f) for f in self.extractors]}>"

    @property
    def kernel_shape(self):
        return self._kernel_shape

    def get_channel_multiplier(self, roi:Slice5D) -> int:
        return sum(f.get_channel_multiplier(roi) for f in self.extractors)

    def compute_into(self, input_roi:DataSource, out:FeatureData) -> FeatureData:
        assert out.roi == self.get_expected_roi(input_roi)
        channel_offset = out.roi.start.c
        for fx in self.extractors:
            out_roi:Slice5D = fx.get_expected_roi(input_roi, channel_offset)
            out_array:FeatureData = out.cut(out_roi)
            fx.compute_into(input_roi, out=out_array)
            channel_offset += out_roi.shape.c
        return out
