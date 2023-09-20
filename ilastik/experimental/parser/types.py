import json
import pickle
from dataclasses import dataclass
from enum import Enum
from typing import Any, List

import h5py
import numpy


class StrEnum(str, Enum):
    pass


class IlastikAPIError(Exception):
    pass


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

    @staticmethod
    def from_ilp_group(features_group: h5py.Group) -> "FeatureMatrix":
        class Keys(StrEnum):
            # feature keys in project file
            FEATURES_IDS = "FeatureIds"
            FEATURES_SCALES = "Scales"
            FEATURES_COMPUTE_IN_2D = "ComputeIn2d"
            FEATURES_SELECTION_MATRIX = "SelectionMatrix"

        if missingkeys := [k for k in Keys if k not in features_group]:
            raise IlastikAPIError(f"Missing keys for feature matrix in project file: {missingkeys}")

        feature_names = [name.decode("ascii") for name in features_group[Keys.FEATURES_IDS][()]]
        scales = features_group[Keys.FEATURES_SCALES][()]
        sel_matrix = features_group[Keys.FEATURES_SELECTION_MATRIX][()]
        compute_in_2d = features_group[Keys.FEATURES_COMPUTE_IN_2D][()]

        return FeatureMatrix(feature_names, scales, sel_matrix, compute_in_2d)


@dataclass
class Classifier:
    instance: Any
    factory: Any
    label_count: int

    @staticmethod
    def from_ilp_group(pixel_class_group: h5py.Group) -> "Classifier":
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

        return Classifier(classifier, classifier_factory, label_count)


@dataclass
class ProjectDataInfo:
    spatial_axes: str
    num_channels: int
    axis_order: str

    @staticmethod
    def from_ilp_group(infos_group: h5py.Group) -> "ProjectDataInfo":
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

        spatial_axes = ""
        axis_order = ""
        num_channels = 1
        for size, dim in zip(shape, tags_dict["axes"]):
            if dim["key"] in "xyz":
                spatial_axes += dim["key"]
            elif dim["key"] == "c":
                num_channels = size

            axis_order += dim["key"]

        return ProjectDataInfo(spatial_axes, num_channels, axis_order)
