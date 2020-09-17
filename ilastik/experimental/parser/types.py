import abc
from dataclasses import dataclass
from typing import Any, List, Optional

import numpy

@dataclass
class FeatureMatrix:
    rows: List[str]
    cols: List[int]
    matrix: numpy.ndarray


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



