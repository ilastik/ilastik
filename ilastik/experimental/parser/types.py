import abc
from dataclasses import dataclass
from typing import Any, List, Optional

import numpy


@dataclass(frozen=True)
class FeatureMatrix:
    """
    Provides OpFeatureSelection compatible interface

    Attributes:
        names: List of feature ids
        scales: List of feature scales
        selections: Boolean matrix where rows are feature names and scales are columuns
            True value means feature is enabled
    """

    names: List[str]
    scales: List[float]
    selections: numpy.ndarray


class FeatureList(abc.ABC):
    @abc.abstractmethod
    def as_matrix(self) -> FeatureMatrix:
        ...

    @abc.abstractmethod
    def __iter__(self):
        ...


@dataclass
class Classifier:
    instance: Any
    factory: Any
    label_count: int


@dataclass
class ProjectDataInfo:
    spatial_axes: str
    num_channels: int
    axis_order: str


class PixelClassificationProject(abc.ABC):
    @abc.abstractproperty
    def features(self) -> Optional[FeatureList]:
        ...

    @abc.abstractproperty
    def classifier(self) -> Optional[Classifier]:
        pass

    @abc.abstractproperty
    def data_info(self) -> Optional[ProjectDataInfo]:
        ...
