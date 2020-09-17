import json
import pickle
from typing import Any, List, Optional

import h5py
import numpy

from ilastik.experimental import features

from . import types

PIXEL_CLASSIFICATION = b"Pixel Classification"


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
    if type_ == PIXEL_CLASSIFICATION:
        return _PixelClassProjectImpl(hdf5_file)

    raise NotImplementedError("Unknown project type {type_}")


class _MatrixFeatureList(types.FeatureList):
    def __init__(self, *, names: List[str], scales: List[int], sel_matrix: numpy.ndarray) -> None:
        # TODO: Validate size
        self.__rows = names
        self.__cols = scales
        self.__sel_matrix = sel_matrix

    def as_matrix(self):
        return types.FeatureMatrix(self.__rows, self.__cols, self.__sel_matrix)

    def __iter__(self):
        for row_idx, name in enumerate(self.__rows):
            for col_idx, scale in enumerate(self.__cols):
                if self.__sel_matrix[row_idx][col_idx]:
                    yield features.create_feature_by_name(name, int(scale * 10))


class _PixelClassProjectImpl(types.PixelClassificationProject):
    INPUT_DATA_KEY = "Input Data"
    INPUT_DATA_INFOS_KEY = "infos"
    INPUT_DATA_RAW_KEY = "Raw Data"
    INPUT_DATA_AXIS_TAGS_KEY = "axistags"
    INPUT_DATA_SHAPE_KEY = "shape"

    FEATURES_KEY = "FeatureSelections"
    FEATURES_IDS_KEY = "FeatureIds"
    FEATURES_SCALES_KEY = "Scales"
    FEATURES_SELECTION_MATRIX_KEY = "SelectionMatrix"
    PIXEL_CLASSIFICATION_KEY = "PixelClassification"
    PIXEL_CLASSIFICATION_TYPE_KEY = "pickled_type"
    PIXEL_CLASSIFICATION_FACTORY_KEY = "ClassifierFactory"
    PIXEL_CLASSIFICATION_FORESTS_KEY = "ClassifierForests"
    LABEL_NAMES_KEY = "LabelNames"

    _SENTINEL = object()

    def __init__(self, hdf5_file: h5py.File) -> None:
        self.__file = hdf5_file
        self.__project_data_info = self._SENTINEL

    @property
    def data_info(self) -> Optional[types.ProjectDataInfo]:
        if self.__project_data_info is self._SENTINEL:
            no_data = False
            try:
                infos_group = self.__file[self.INPUT_DATA_KEY][self.INPUT_DATA_INFOS_KEY]
            except KeyError:
                no_data = True

            if no_data or not len(infos_group):
                self.__project_data_info = None
                return self.__project_data_info

            info = next(iter(infos_group.values()))

            json_bytes = info[self.INPUT_DATA_RAW_KEY][self.INPUT_DATA_AXIS_TAGS_KEY][()]
            tags_dict = json.loads(json_bytes.decode("ascii"))
            shape = info[self.INPUT_DATA_RAW_KEY][self.INPUT_DATA_SHAPE_KEY][()]

            if len(shape) != len(tags_dict["axes"]):
                raise ValueError(f"Shape {shape} and axistags {tags_dict} mismatch")

            res = []
            spatial_axes = ""
            num_channels = 1
            for size, dim in zip(shape, tags_dict["axes"]):
                if dim["key"] in "xyz":
                    spatial_axes += dim["key"]
                elif dim["key"] == "c":
                    num_channels = size

            self.__project_data_info = types.ProjectDataInfo(spatial_axes, num_channels)

        return self.__project_data_info

    @property
    def features(self) -> Optional[types.FeatureList]:
        try:
            features_group = self.__file[self.FEATURES_KEY]
            feature_names = [name.decode("ascii") for name in features_group[self.FEATURES_IDS_KEY][()]]
            scales = features_group[self.FEATURES_SCALES_KEY][()]
            sel_matrix = features_group[self.FEATURES_SELECTION_MATRIX_KEY][()]
        except KeyError:
            # Project has no selected features
            return None

        else:
            return _MatrixFeatureList(names=feature_names, scales=scales, sel_matrix=sel_matrix)

    @property
    def classifier(self):
        try:
            pixel_class_group = self.__file[self.PIXEL_CLASSIFICATION_KEY]

            classfier_group = pixel_class_group[self.PIXEL_CLASSIFICATION_FORESTS_KEY]
            classifier_type = pickle.loads(classfier_group[self.PIXEL_CLASSIFICATION_TYPE_KEY][()])
            classifier = classifier_type.deserialize_hdf5(classfier_group)

            classifier_factory = pickle.loads(pixel_class_group[self.PIXEL_CLASSIFICATION_FACTORY_KEY][()])
            label_count = len(pixel_class_group[self.LABEL_NAMES_KEY])
        except KeyError:
            # Project has no trained classifier
            return None

        else:
            return types.Classifier(classifier, classifier_factory, label_count)
