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


class _InputDataKeys:
    ROOT = "Input Data"
    INFOS = "infos"
    RAW = "Raw Data"
    AXIS_TAGS = "axistags"
    SHAPE = "shape"


class _PixelFeatureKeys:
    ROOT = "FeatureSelections"
    IDS = "FeatureIds"
    SCALES = "Scales"
    COMPUTE_IN_2D = "ComputeIn2d"
    SELECTION_MATRIX = "SelectionMatrix"


class _PixelClassificationKeys:
    ROOT = "PixelClassification"
    TYPE = "pickled_type"
    FACTORY = "ClassifierFactory"
    FORESTS = "ClassifierForests"
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
                infos_group = self.__file[_InputDataKeys.ROOT][_InputDataKeys.INFOS]
            except KeyError:
                no_data = True

            if no_data or not len(infos_group):
                self.__project_data_info = None
                return self.__project_data_info

            info = next(iter(infos_group.values()))

            json_bytes = info[_InputDataKeys.RAW][_InputDataKeys.AXIS_TAGS][()]
            tags_dict = json.loads(json_bytes.decode("ascii"))
            shape = info[_InputDataKeys.RAW][_InputDataKeys.SHAPE][()]

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
            features_group = self.__file[_PixelFeatureKeys.ROOT]
            feature_names = [name.decode("ascii") for name in features_group[_PixelFeatureKeys.IDS][()]]
            scales = features_group[_PixelFeatureKeys.SCALES][()]
            sel_matrix = features_group[_PixelFeatureKeys.SELECTION_MATRIX][()]
            compute_in_2d = features_group[_PixelFeatureKeys.COMPUTE_IN_2D][()]
        except KeyError:
            # Project has no selected features
            return None

        else:
            return types.FeatureMatrix(feature_names, scales, sel_matrix, compute_in_2d)

    @property
    def classifier(self):
        try:
            pixel_class_group = self.__file[_PixelClassificationKeys.ROOT]

            classfier_group = pixel_class_group[_PixelClassificationKeys.FORESTS]
            classifier_type = pickle.loads(classfier_group[_PixelClassificationKeys.TYPE][()])
            classifier = classifier_type.deserialize_hdf5(classfier_group)

            classifier_factory = pickle.loads(pixel_class_group[_PixelClassificationKeys.FACTORY][()])
            label_count = len(pixel_class_group[_PixelClassificationKeys.LABEL_NAMES])
        except KeyError:
            # Project has no trained classifier
            return None

        else:
            return types.Classifier(classifier, classifier_factory, label_count)


class _ObjectFeatureKeys:
    ROOT = "ObjectExtraction"
    FEATURES = "Features"


class _ObjectClassificationKeys:
    ROOT = "ObjectClassification"
    TYPE = "pickled_type"
    FACTORY = "ClassifierFactory"
    FORESTS = "ClassifierForests"
    LABEL_NAMES = "LabelNames"


class ObjectClassificationClassProjImpl(types.ObjectClassificationProjectBase):
    _SENTINEL = object()
    workflowname = b"Object Classification (from binary image)"

    def __init__(self, hdf5_file: h5py.File) -> None:
        self.__file = hdf5_file
        self.__project_data_info = self._SENTINEL

    @property
    def ready_for_prediction(self):
        return all([self.data_info, self.selected_object_features, self.classifier])

    @property
    def data_info(self) -> Optional[types.ProjectDataInfo]:
        if self.__project_data_info is self._SENTINEL:
            no_data = False
            try:
                infos_group = self.__file[_InputDataKeys.ROOT][_InputDataKeys.INFOS]
            except KeyError:
                no_data = True

            if no_data or not len(infos_group):
                self.__project_data_info = None
                return self.__project_data_info

            info = next(iter(infos_group.values()))

            json_bytes = info[_InputDataKeys.RAW][_InputDataKeys.AXIS_TAGS][()]
            tags_dict = json.loads(json_bytes.decode("ascii"))
            shape = info[_InputDataKeys.RAW][_InputDataKeys.SHAPE][()]

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
    def selected_object_features(self) -> Optional[types.ObjectFeatures]:
        try:
            features_root = self.__file[_ObjectFeatureKeys.ROOT][_ObjectFeatureKeys.FEATURES]
        except KeyError:
            return None

        else:
            selected_features = {}
            for feature_group_name, feature_group in features_root.items():
                assert isinstance(feature_group, h5py.Group)
                group_dict = {}
                for feature_name, feature_g in feature_group.items():
                    assert isinstance(feature_g, h5py.Group)
                    assert all(isinstance(v, h5py.Dataset) for v in feature_g.values())
                    group_dict[feature_name] = {k: v[()] for k, v in feature_g.items()}
                selected_features[feature_group_name] = group_dict
            return types.ObjectFeatures(selected_features=selected_features)

    @property
    def classifier(self):
        try:
            object_class_group = self.__file[_ObjectClassificationKeys.ROOT]
            classfier_group = object_class_group[_ObjectClassificationKeys.FORESTS]
            classifier_type = pickle.loads(classfier_group[_ObjectClassificationKeys.TYPE][()])
            # Note, we don't save the classifierfactory in object classification.
            # There has been no way to change it for the user up to 1.4.0b20 (at least)
            # so here we assume it's `ParallelVigraRfLazyflowClassifier`
            from lazyflow.classifiers.parallelVigraRfLazyflowClassifier import (
                ParallelVigraRfLazyflowClassifier,
                ParallelVigraRfLazyflowClassifierFactory,
            )

            assert classifier_type == ParallelVigraRfLazyflowClassifier
            classifier = classifier_type.deserialize_hdf5(classfier_group)
            # add hard-coded factory, see note above.
            classifier_factory = ParallelVigraRfLazyflowClassifierFactory
            label_count = len(object_class_group[_ObjectClassificationKeys.LABEL_NAMES])
        except KeyError:
            # Project has no trained classifier
            return None

        else:
            return types.Classifier(classifier, classifier_factory, label_count)
