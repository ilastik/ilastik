import json
import pickle
from typing import Any, List, Optional

import h5py
import numpy

from . import types


class IlastikProject:
    def __init__(self, path: str, mode: str = "r") -> None:
        if mode != "r":
            raise NotImplementedError(f"mode: {mode}")

        self.__mode = mode
        self.__path = path
        self.__file = None

    def __enter__(self):
        self.__file = h5py.File(self.__path, mode=self.__mode)
        return _create_project_wrap(self.__file)

    def __exit__(self, exc_type, exc, tb):
        if self.__file:
            self.__file.close()


WORKFLOW_KEY = "workflowName"


def _create_project_wrap(hdf5_file):
    type_ = hdf5_file[WORKFLOW_KEY][()]
    try:
        return types.registry[type_](hdf5_file)
    except KeyError:
        raise NotImplementedError(f"Unknown project type {type_}")


class _Keys:
    INPUT_DATA = "Input Data"
    INPUT_DATA_INFOS = "infos"
    INPUT_DATA_RAW = "Raw Data"
    INPUT_DATA_AXIS_TAGS = "axistags"
    INPUT_DATA_SHAPE = "shape"

    FEATURES = "FeatureSelections"
    FEATURES_IDS = "FeatureIds"
    FEATURES_SCALES = "Scales"
    FEATURES_COMPUTE_IN_2D = "ComputeIn2d"
    FEATURES_SELECTION_MATRIX = "SelectionMatrix"
    PIXEL_CLASSIFICATION = "PixelClassification"
    PIXEL_CLASSIFICATION_TYPE = "pickled_type"
    PIXEL_CLASSIFICATION_FACTORY = "ClassifierFactory"
    PIXEL_CLASSIFICATION_FORESTS = "ClassifierForests"
    LABEL_NAMES = "LabelNames"


class _PixelClassProjectImpl(types.PixelClassificationProject):
    _SENTINEL = object()
    workflowname = b"Pixel Classification"

    def __init__(self, hdf5_file: h5py.File) -> None:
        self.__file = hdf5_file
        self.__project_data_info = self._SENTINEL

    @property
    def ready_for_prediction(self):
        return all([self.data_info, self.feature_matrix, self.classifier])

    @property
    def data_info(self) -> Optional[types.ProjectDataInfo]:
        if self.__project_data_info is self._SENTINEL:
            no_data = False
            try:
                infos_group = self.__file[_Keys.INPUT_DATA][_Keys.INPUT_DATA_INFOS]
            except KeyError:
                no_data = True

            if no_data or not len(infos_group):
                self.__project_data_info = None
                return self.__project_data_info

            info = next(iter(infos_group.values()))

            json_bytes = info[_Keys.INPUT_DATA_RAW][_Keys.INPUT_DATA_AXIS_TAGS][()]
            tags_dict = json.loads(json_bytes.decode("ascii"))
            shape = info[_Keys.INPUT_DATA_RAW][_Keys.INPUT_DATA_SHAPE][()]

            if len(shape) != len(tags_dict["axes"]):
                raise ValueError(f"Shape {shape} and axistags {tags_dict} mismatch")

            res = []
            spatial_axes = ""
            axis_order = ""
            num_channels = 1
            for size, dim in zip(shape, tags_dict["axes"]):
                if dim["key"] in "xyz":
                    spatial_axes += dim["key"]
                elif dim["key"] == "c":
                    num_channels = size

                axis_order += dim["key"]

            self.__project_data_info = types.ProjectDataInfo(spatial_axes, num_channels, axis_order)

        return self.__project_data_info

    @property
    def feature_matrix(self) -> Optional[types.FeatureMatrix]:
        try:
            features_group = self.__file[_Keys.FEATURES]
            feature_names = [name.decode("ascii") for name in features_group[_Keys.FEATURES_IDS][()]]
            scales = features_group[_Keys.FEATURES_SCALES][()]
            sel_matrix = features_group[_Keys.FEATURES_SELECTION_MATRIX][()]
            compute_in_2d = features_group[_Keys.FEATURES_COMPUTE_IN_2D][()]
        except KeyError:
            # Project has no selected features
            return None

        else:
            return types.FeatureMatrix(feature_names, scales, sel_matrix, compute_in_2d)

    @property
    def classifier(self):
        try:
            pixel_class_group = self.__file[_Keys.PIXEL_CLASSIFICATION]

            classfier_group = pixel_class_group[_Keys.PIXEL_CLASSIFICATION_FORESTS]
            classifier_type = pickle.loads(classfier_group[_Keys.PIXEL_CLASSIFICATION_TYPE][()])
            classifier = classifier_type.deserialize_hdf5(classfier_group)

            classifier_factory = pickle.loads(pixel_class_group[_Keys.PIXEL_CLASSIFICATION_FACTORY][()])
            label_count = len(pixel_class_group[_Keys.LABEL_NAMES])
        except KeyError:
            # Project has no trained classifier
            return None

        else:
            return types.Classifier(classifier, classifier_factory, label_count)
