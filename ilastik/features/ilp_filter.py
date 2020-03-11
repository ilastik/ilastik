from abc import abstractmethod, ABC
from typing import Type, TypeVar, List, TypeVar, ClassVar, Mapping, Iterator
import re

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

    def to_ilp_feature_names(self) -> Iterator[bytes]:
        for c in range(self.num_input_channels * self.channel_multiplier):
            name_and_channel = self.ilp_name + f" [{c}]"
            yield name_and_channel.encode("utf8")
