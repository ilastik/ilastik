from abc import abstractmethod
import functools
from typing import List, Iterable, Optional, TypeVar, ClassVar, Mapping, Type, Union
from pathlib import Path
import re

import numpy as np
import h5py

from ndstructs import Slice5D, Point5D, Shape5D
from ndstructs import Array5D
from ndstructs.datasource import DataSource, DataSourceSlice
from ndstructs.utils import JsonSerializable


class FeatureData(Array5D):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # FIXME:
        # assert arr.dtype == np.float32

    def show(self):
        return self.as_uint8().show_channels()


class FeatureDataMismatchException(Exception):
    def __init__(self, feature_extractor: "FeatureExtractor", data_source: DataSource):
        super().__init__(f"Feature {feature_extractor} can't be cleanly applied to {data_source}")


FE = TypeVar("FE", bound="FeatureExtractor")


class FeatureExtractor(JsonSerializable):
    """A specification of how feature data is to be (reproducibly) computed"""

    REGISTRY: ClassVar[Mapping[str, Type[FE]]] = {}

    @classmethod
    @abstractmethod
    def from_ilastik_scale(cls: Type[FE], scale: float, compute_in_2d: bool) -> FE:
        pass

    @staticmethod
    def from_ilp_group(group: h5py.Group) -> List[FE]:
        feature_names: List[str] = [feature_name.decode("utf-8") for feature_name in group["FeatureIds"][()]]
        compute_in_2d: List[bool] = list(group["ComputeIn2d"][()])
        scales: List[float] = list(group["Scales"][()])
        selection_matrix = group["SelectionMatrix"][()]  # feature name x scales

        feature_extractors = []
        for feature_idx, feature_name in enumerate(feature_names):
            feature_class = FeatureExtractor.REGISTRY[feature_name]
            for scale_idx, (scale, in_2d) in enumerate(zip(scales, compute_in_2d)):
                if selection_matrix[feature_idx][scale_idx]:
                    feature_extractors.append(feature_class.from_ilastik_scale(scale, axis_2d="z" if in_2d else None))
        return feature_extractors

    @staticmethod
    def from_classifier_feature_names(feature_names: h5py.Dataset) -> List["FeatureExtractor"]:
        feature_extractors = []
        for feature_description in feature_names:
            description = feature_description.decode("utf8")
            name = re.search(r"^(?P<name>[a-zA-Z \-]+)", description).group("name").strip()
            klass = FeatureExtractor.REGISTRY[name.title().replace(" ", "")]
            scale = float(re.search(r"σ=(?P<sigma>[0-9.]+)", description).group("sigma"))
            extractor = klass.from_ilastik_scale(scale, axis_2d="z" if "in 2D" in description else None)
            if len(feature_extractors) == 0 or feature_extractors[-1] != extractor:
                feature_extractors.append(extractor)
        return feature_extractors

    def __hash__(self):
        return hash((self.__class__, tuple(self.__dict__.values())))

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.__dict__ == other.__dict__

    @abstractmethod
    def get_expected_shape(self, input_shape: Shape5D) -> Shape5D:
        pass

    def allocate_for(self, input_shape: Shape5D) -> FeatureData:
        # FIXME: vigra needs C to be the last REAL axis rather than the last axis of the view -.-
        out_roi = self.get_expected_shape(input_shape).to_slice_5d()
        return FeatureData.allocate(out_roi, dtype=np.float32, axiskeys="tzyxc")

    @functools.lru_cache()
    def compute(self, input_roi: DataSourceSlice) -> FeatureData:
        out_features = self.allocate_for(input_roi.shape).translated(input_roi.start)
        self.compute_into(input_roi, out_features)
        out_features.setflags(write=False)
        return out_features

    @abstractmethod
    def compute_into(self, input_roi: DataSource, out: FeatureData) -> FeatureData:
        pass

    def is_applicable_to(self, datasource: DataSource) -> bool:
        return datasource.shape >= self.kernel_shape

    def ensure_applicable(self, datasource: DataSource):
        if not self.is_applicable_to(datasource):
            raise FeatureDataMismatchException(self, datasource)

    @property
    @abstractmethod
    def kernel_shape(self) -> Shape5D:
        pass

    @property
    def halo(self) -> Point5D:
        return self.kernel_shape // 2


class ChannelwiseFilter(FeatureExtractor):
    """A Feature extractor that computes independently for every
    spatial slice and for every channel in its input"""

    def __init__(self, axis_2d: Optional[str] = None):
        super().__init__()
        self.axis_2d = axis_2d

    @property
    def channel_multiplier(self) -> int:
        "Number of channels emited by this feature extractor for each input channel"
        return 1

    def get_expected_shape(self, input_shape: Shape5D) -> Shape5D:
        return input_shape.with_coord(c=input_shape.c * self.channel_multiplier)

    def compute_into(self, input_roi: DataSourceSlice, out: FeatureData) -> FeatureData:
        in_step: Shape5D = input_roi.shape.with_coord(c=1, t=1)  # compute features independently for each c and each t
        if self.axis_2d:
            in_step = in_step.with_coord(**{self.axis_2d: 1})  # also compute in 2D slices
        out_step: Shape5D = in_step.with_coord(c=self.channel_multiplier)

        for slc_in, slc_out in zip(input_roi.split(in_step), out.split(out_step)):
            self._compute_slice(slc_in, out=slc_out)
        return out

    @abstractmethod
    def _compute_slice(self, raw_data: DataSourceSlice, out: FeatureData):
        pass

    def _debug_show(self, rawData: DataSourceSlice, featureData: FeatureData):
        channel_multiplier = int(featureData.shape.c / rawData.shape.c)
        assert channel_multiplier == self.channel_multiplier
        print(f"Showing features as a group of  {channel_multiplier}-channel images")
        for channel_stack in featureData.channel_stacks(channel_multiplier):
            channel_stack.as_uint8(normalized=False).show_images()


class FeatureExtractorCollection(FeatureExtractor):
    def __init__(self, extractors: Iterable[FeatureExtractor]):
        assert len(extractors) > 0
        self.extractors = tuple(extractors)

        shape_params = {}
        for label in Point5D.LABELS:
            shape_params[label] = max(f.kernel_shape[label] for f in extractors)
        self._kernel_shape = Shape5D(**shape_params)

    @classmethod
    def from_ilastik_scale(cls, scale: float, compute_in_2d: bool) -> "FeatureExtractorCollection":
        raise NotImplementedError("It makes no sense to implement this")

    def __repr__(self):
        return f"<{self.__class__.__name__} {[repr(f) for f in self.extractors]}>"

    @property
    def kernel_shape(self):
        return self._kernel_shape

    def get_expected_shape(self, input_shape: Shape5D) -> Shape5D:
        expected_c = sum(fx.get_expected_shape(input_shape).c for fx in self.extractors)
        return input_shape.with_coord(c=expected_c)

    @property
    def channel_multiplier(self) -> int:
        return sum(f.channel_multiplier for f in self.extractors)

    def compute_into(self, input_roi: DataSourceSlice, out: FeatureData) -> FeatureData:
        assert out.shape == self.get_expected_shape(input_roi.shape)
        offset = Point5D.zero()
        for fx in self.extractors:
            out_roi: Slice5D = fx.get_expected_shape(input_roi.shape).to_slice_5d().translated(offset)
            out_array: FeatureData = out.local_cut(out_roi)
            fx.compute_into(input_roi, out=out_array)
            offset += Point5D.zero(c=out_roi.shape.c)
        return out
