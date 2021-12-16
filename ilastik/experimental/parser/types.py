import abc
from dataclasses import dataclass
from typing import Any, List, Mapping, Optional, Literal

import numpy

_registry = {}


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


@dataclass
class ObjectFeatures:
    """
    Interface compatible with OpRegionFeatures

    Attributes:
        selected_features: Dictionary of the form
            [plugin_name][feature_name][parameter_name] = value

    """

    selected_features: Mapping[str, Mapping[str, Any]]


@dataclass
class ThresholdingSettings:
    """
    Interface for OpThresholdTwoLevels
    """

    method: int
    min_size: int
    max_size: int
    low_threshold: float
    high_threshold: float
    smoother_sigmas: Mapping[Literal["z", "y", "x"], float]
    channel: int
    core_channel: Optional[int]


class IlastikProject(abc.ABC):
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if isinstance(cls.workflowname, bytes):
            _registry[cls.workflowname] = cls
        elif isinstance(cls.workflowname, property):
            # ignore abstract subclasses
            pass
        else:
            raise TypeError(f"workflowname must by `bytes` not `{type(cls.workflowname)}`")

    @property
    @abc.abstractclassmethod
    def workflowname(cls) -> str:
        ...

    @abc.abstractproperty
    def data_info(self) -> Optional[ProjectDataInfo]:
        ...

    @abc.abstractproperty
    def ready_for_prediction(self) -> bool:
        """Loaded project contains all necessary data for prediction"""
        ...


class PixelClassificationProject(IlastikProject):
    @abc.abstractproperty
    def feature_matrix(self) -> Optional[FeatureMatrix]:
        ...

    @abc.abstractproperty
    def classifier(self) -> Optional[Classifier]:
        pass


class ObjectClassificationProjectBase(IlastikProject):
    @abc.abstractproperty
    def selected_object_features(self) -> Optional[ObjectFeatures]:
        pass

    @abc.abstractproperty
    def classifier(self) -> Optional[Classifier]:
        pass


class ObjectClassificationFromPredictionProject(ObjectClassificationProjectBase):
    @abc.abstractproperty
    def thresholding_settings(self) -> Optional[ThresholdingSettings]:
        pass


registry = _registry
