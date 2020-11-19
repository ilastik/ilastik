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
        compute_in_2d: 1d array for each scale reflecting if feature should be computed in 2D
    """

    names: List[str]
    scales: List[float]
    selections: numpy.ndarray
    compute_in_2d: numpy.ndarray


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
    def feature_matrix(self) -> Optional[FeatureMatrix]:
        ...

    @abc.abstractproperty
    def classifier(self) -> Optional[Classifier]:
        pass

    @abc.abstractproperty
    def data_info(self) -> Optional[ProjectDataInfo]:
        ...
