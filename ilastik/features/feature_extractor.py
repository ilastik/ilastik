from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor as Executor
from dataclasses import dataclass
import functools
from operator import mul
from typing import List, Iterator, Tuple

import vigra.filters
import numpy as np

from ilastik.array5d import Slice5D, Point5D, Shape5D
from ilastik.array5d import Array5D, Image, ScalarImage, LinearData
from ilastik.data_source import DataSource

class FeatureData(Array5D):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #FIXME:
        #assert arr.dtype == np.float32

    def as_uint8(self):
        return Array5D((self._data * 255).astype(np.uint8), axiskeys=self.axiskeys)

    def show(self):
        for idx, channel in enumerate(next(self.as_uint8().images()).channels()):
            path = f"/tmp/tmp_show_{idx}.png"
            channel.as_pil_image().save(path)
            import os; os.system(f"gimp {path}")



class FeatureDataMismatchException(Exception):
    def __init__(self, feature_extractor:'FeatureExtractor', data_source:DataSource):
        super().__init__(f"Feature {feature_extractor} can't be cleanly applied to {data_source}")


class FeatureExtractor(ABC):
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
    @property
    @abstractmethod
    def dimension(self) -> int:
        "Number of channels emited by this feature extractor for each input channel"
        pass

    def get_expected_roi(self, roi:Slice5D, channel_offset:int=0) -> Shape5D:
        num_output_channels = roi.shape.c * self.dimension
        c_start = channel_offset
        c_stop = c_start + num_output_channels
        return roi.with_coord(c=slice(c_start, c_stop))

class FlatChannelwiseFilter(ChannelwiseFeatureExtractor):
    """A Feature extractor with a 2D kernel that computes independently for every
    spatial slice and for every channel in its input"""

    def __init__(self, stack_axis:str='z'):
        super().__init__()
        self.stack_axis = stack_axis

    def compute_into(self, input_roi:DataSource, out:FeatureData) -> FeatureData:
        for source_image_roi, out_image in zip(input_roi.images(self.stack_axis), out.images(self.stack_axis)):
            for source_channel_roi, out_features in zip(source_image_roi.channels(), out_image.channel_stacks(step=self.dimension)):
                self._compute_slice(source_channel_roi, out=out_features)
        return out

    @abstractmethod
    def _compute_slice(self, raw_data:DataSource, out:Image):
        pass


class FeatureExtractorCollection(ChannelwiseFeatureExtractor):
    def __init__(self, extractors:Tuple[FeatureExtractor]):
        assert len(extractors) > 0
        self.extractors = extractors

        shape_params = {}
        for label in Point5D.LABELS:
            shape_params[label] = max(f.kernel_shape[label] for f in extractors)
        self._kernel_shape = Shape5D(**shape_params)

    def __repr__(self):
        return f"<{self.__class__.__name__} {[repr(f) for f in self.extractors]}>"

    @property
    def kernel_shape(self):
        return self._kernel_shape

    @property
    def dimension(self) -> int:
        return sum(f.dimension for f in self.extractors)

    def compute_into(self, input_roi:DataSource, out:FeatureData) -> FeatureData:
        assert out.roi == self.get_expected_roi(input_roi)
        channel_offset = out.roi.start.c
        for fx in self.extractors:
            out_roi:Slice5D = fx.get_expected_roi(input_roi, channel_offset)
            out_array:FeatureData = out.cut(out_roi)
            fx.compute_into(input_roi, out=out_array)
            channel_offset += out_roi.shape.c
        return out
