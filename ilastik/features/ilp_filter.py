from abc import abstractmethod, ABC
from typing import Type, TypeVar, List, TypeVar, ClassVar, Mapping, Iterator, Sequence, Dict, Any
import re

import numpy as np
from ndstructs.utils import from_json_data


from .feature_extractor import ChannelwiseFilter


FE = TypeVar("FE", bound="IlpFilter")


class IlpFilter(ChannelwiseFilter):
    REGISTRY: ClassVar[Mapping[str, Type[FE]]] = {}

    @property
    @abstractmethod
    def ilp_scale(self) -> float:
        pass

    @classmethod
    @abstractmethod
    def from_ilp_scale(cls: Type[FE], scale: float, compute_in_2d: bool, num_input_channels) -> FE:
        pass

    @property
    def ilp_name(self) -> str:
        name = re.sub(r"([a-z])([A-Z])", r"\1___\2", self.__class__.__name__).replace("___", " ").title()
        name = re.sub(r"\bOf\b", "of", name)
        name += f" (σ={self.ilp_scale})"
        name += " in 2D" if self.axis_2d is not None else " in 3D"
        return name

    @classmethod
    def from_ilp_classifier_feature_name(cls, feature_name: bytes) -> "ChannelwiseFilter":
        feature_name = feature_name.decode("utf8")
        name = re.search(r"^(?P<name>[a-zA-Z \-]+)", description).group("name").strip()
        klass = cls.REGISTRY[name.title().replace(" ", "")]
        scale = float(re.search(r"σ=(?P<sigma>[0-9.]+)", description).group("sigma"))
        return klass.from_ilp_scale(scale, axis_2d="z" if "in 2D" in description else None)

    @classmethod
    def from_ilp_classifier_feature_names(cls, feature_names: List[bytes]) -> List["ChannelwiseFilter"]:
        feature_extractors: List[ChannelwiseFilter] = []
        for feature_description in feature_names:
            extractor = cls.from_ilp_feature_name(feature_description)
            if len(feature_extractors) == 0 or feature_extractors[-1] != extractor:
                feature_extractors.append(extractor)
        return feature_extractors

    @classmethod
    def from_ilp_data(cls, data: Mapping, num_input_channels: int) -> List["IlpFilter"]:
        feature_names: List[str] = [feature_name.decode("utf-8") for feature_name in data["FeatureIds"][()]]
        compute_in_2d: List[bool] = list(data["ComputeIn2d"][()])
        scales: List[float] = list(data["Scales"][()])
        selection_matrix = data["SelectionMatrix"][()]  # feature name x scales

        feature_extractors = []
        for feature_idx, feature_name in enumerate(feature_names):
            feature_class = IlpFilter.REGISTRY[feature_name]
            for scale_idx, (scale, in_2d) in enumerate(zip(scales, compute_in_2d)):
                if selection_matrix[feature_idx][scale_idx]:
                    axis_2d = "z" if in_2d else None
                    extractor = feature_class.from_ilp_scale(
                        scale, axis_2d=axis_2d, num_input_channels=num_input_channels
                    )
                    feature_extractors.append(extractor)
        return feature_extractors

    @classmethod
    def from_json_data(cls, data) -> "IlpFilter":
        return cls.REGISTRY[data["__class__"]].from_json_data(data)

    @classmethod
    def dump_as_ilp_data(cls, feature_extractors: Sequence["IlpFilter"]) -> Dict[str, Any]:
        if not feature_extractors:
            return {}
        out = {}

        feature_names = [
            "GaussianSmoothing",
            "LaplacianOfGaussian",
            "GaussianGradientMagnitude",
            "DifferenceOfGaussians",
            "StructureTensorEigenvalues",
            "HessianOfGaussianEigenvalues",
        ]
        out["FeatureIds"] = np.asarray([fn.encode("utf8") for fn in feature_names])

        default_scales = [0.3, 0.7, 1.0, 1.6, 3.5, 6.0, 10.0]
        extra_scales = set(fe.ilp_scale for fe in feature_extractors if fe.ilp_scale not in default_scales)
        scales = default_scales + sorted(extra_scales)
        out["Scales"] = np.asarray(scales)

        SelectionMatrix = np.zeros((len(feature_names), len(scales)), dtype=bool)
        for fe in feature_extractors:
            name_idx = feature_names.index(fe.__class__.__name__)
            scale_idx = scales.index(fe.ilp_scale)
            SelectionMatrix[name_idx, scale_idx] = True

        ComputeIn2d = np.full(len(scales), True, dtype=bool)
        for idx, fname in enumerate(feature_names):
            ComputeIn2d[idx] = all(fe.axis_2d for fe in feature_extractors if fe.__class__.__name__ == fname)

        out["SelectionMatrix"] = SelectionMatrix
        out["ComputeIn2d"] = ComputeIn2d  # [: len(scales)]  # weird .ilp quirk in featureTableWidget.py:524
        out["StorageVersion"] = "0.1"
        return out

    def to_ilp_feature_names(self) -> Iterator[bytes]:
        for c in range(self.num_input_channels * self.channel_multiplier):
            name_and_channel = self.ilp_name + f" [{c}]"
            yield name_and_channel.encode("utf8")
