###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2023, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#          http://ilastik.org/license.html
###############################################################################
import json
import pickle
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List, Type, TypeVar, Union

import h5py
import numpy
import numpy.typing as npt

from lazyflow.classifiers import (
    LazyflowPixelwiseClassifierABC,
    LazyflowPixelwiseClassifierFactoryABC,
    LazyflowVectorwiseClassifierABC,
    LazyflowVectorwiseClassifierFactoryABC,
)


class StrEnum(str, Enum):
    pass


class IlastikAPIError(Exception):
    pass


T = TypeVar("T", bound="ILPNode")


class ILPNode(ABC):
    @classmethod
    @abstractmethod
    def from_ilp_group(cls: Type[T], group: h5py.Group) -> T:
        ...


@dataclass(frozen=True)
class FeatureMatrix(ILPNode):
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
    selections: npt.NDArray[numpy.bool_]
    compute_in_2d: npt.NDArray[numpy.bool_]

    @classmethod
    def from_ilp_group(cls, features_group: h5py.Group) -> "FeatureMatrix":
        class Keys(StrEnum):
            # feature keys in project file
            FEATURES_IDS = "FeatureIds"
            FEATURES_SCALES = "Scales"
            FEATURES_COMPUTE_IN_2D = "ComputeIn2d"
            FEATURES_SELECTION_MATRIX = "SelectionMatrix"

        if missingkeys := [k for k in Keys if k not in features_group]:
            raise IlastikAPIError(f"Missing keys for feature matrix in project file: {missingkeys}")

        feature_names: List[str] = [name.decode("ascii") for name in features_group[Keys.FEATURES_IDS][()]]  # type: ignore
        scales: List[float] = features_group[Keys.FEATURES_SCALES][()]  # type: ignore
        sel_matrix: npt.NDArray[numpy.bool_] = features_group[Keys.FEATURES_SELECTION_MATRIX][()]  # type: ignore
        compute_in_2d: npt.NDArray[numpy.bool_] = features_group[Keys.FEATURES_COMPUTE_IN_2D][()]  # type: ignore

        return cls(feature_names, scales, sel_matrix, compute_in_2d)


@dataclass
class Classifier(ILPNode):
    instance: Union[LazyflowPixelwiseClassifierABC, LazyflowVectorwiseClassifierABC]
    factory: Union[LazyflowPixelwiseClassifierFactoryABC, LazyflowVectorwiseClassifierFactoryABC]
    label_count: int

    @classmethod
    def from_ilp_group(cls, pixel_class_group: h5py.Group) -> "Classifier":
        class Keys(StrEnum):
            PIXEL_CLASSIFICATION_FORESTS = "ClassifierForests"
            PIXEL_CLASSIFICATION_FACTORY = "ClassifierFactory"
            PIXEL_CLASSIFICATION_TYPE = "ClassifierForests/pickled_type"
            LABEL_NAMES = "LabelNames"

        if missingkeys := [k for k in Keys if k not in pixel_class_group]:
            raise IlastikAPIError(f"Missing keys in project file: {missingkeys}")

        classifier_type = pickle.loads(pixel_class_group[Keys.PIXEL_CLASSIFICATION_TYPE][()])
        classifier = classifier_type.deserialize_hdf5(pixel_class_group[Keys.PIXEL_CLASSIFICATION_FORESTS])

        classifier_factory = pickle.loads(pixel_class_group[Keys.PIXEL_CLASSIFICATION_FACTORY][()])
        label_count = len(pixel_class_group[Keys.LABEL_NAMES])

        return cls(classifier, classifier_factory, label_count)


@dataclass
class ProjectDataInfo(ILPNode):
    spatial_axes: str
    num_channels: int
    axis_order: str

    @classmethod
    def from_ilp_group(cls, infos_group: h5py.Group) -> "ProjectDataInfo":
        class Keys(StrEnum):
            # input data keys in project file
            RAW_DATA = "Raw Data"
            RAW_DATA_AXIS_TAGS = "Raw Data/axistags"
            RAW_DATA_SHAPE = "Raw Data/shape"

        info = next(iter(infos_group.values()))

        if missingkeys := [k for k in Keys if k not in info]:
            raise IlastikAPIError(f"Missing data info keys in project file: {missingkeys}.")

        json_bytes = info[Keys.RAW_DATA_AXIS_TAGS][()]
        tags_dict = json.loads(json_bytes.decode("ascii"))
        shape = info[Keys.RAW_DATA_SHAPE][()]

        if len(shape) != len(tags_dict["axes"]):
            raise IlastikAPIError(f"Shape {shape} and axistags {tags_dict} mismatch")

        axis_order = "".join(dim["key"] for dim in tags_dict["axes"])
        spatial_axes = "".join(ax for ax in axis_order if ax in "xyz")

        try:
            num_channels = shape[axis_order.index("c")]
        except ValueError:
            num_channels = 1

        return cls(spatial_axes, num_channels, axis_order)
