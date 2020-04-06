from typing import Optional, Dict, Hashable, Any, Union, List
import uuid

import flask

from ndstructs import Point5D, Slice5D, Shape5D, Array5D
from ndstructs.datasource import (
    DataSource,
    DataSourceSlice,
    SequenceDataSource,
    SkimageDataSource,
    PrecomputedChunksDataSource,
)
from ndstructs.utils import JsonSerializable, from_json_data, JsonReference

from ilastik.utility import flatten, unflatten, listify
from ilastik.annotations import Annotation
from ilastik.classifiers.pixel_classifier import (
    PixelClassifier,
    Predictions,
    VigraPixelClassifier,
    ScikitLearnPixelClassifier,
)
from ilastik.workflows.pixelClassification.pixel_classification_workflow_2 import (
    PixelClassificationWorkflow2,
    DataLane,
    GuiDataSource,
)
from ilastik.classifiers.ilp_pixel_classifier import IlpVigraPixelClassifier

from ilastik.features.feature_extractor import FeatureExtractor, FeatureDataMismatchException
from ilastik.features import (
    GaussianSmoothing,
    HessianOfGaussianEigenvalues,
    GaussianGradientMagnitude,
    LaplacianOfGaussian,
    DifferenceOfGaussians,
    StructureTensorEigenvalues,
)


datasource_classes = [DataSource, SequenceDataSource, SkimageDataSource, PrecomputedChunksDataSource]

feature_extractor_classes = [
    FeatureExtractor,  # this allows one to GET /feature_extractor and get a list of all created feature extractors
    GaussianSmoothing,
    HessianOfGaussianEigenvalues,
    GaussianGradientMagnitude,
    LaplacianOfGaussian,
    DifferenceOfGaussians,
    StructureTensorEigenvalues,
]

classifier_classes = [
    PixelClassifier,
    VigraPixelClassifier,
    ScikitLearnPixelClassifier,
    IlpVigraPixelClassifier,
    Annotation,
]

workflow_classes = [PixelClassificationWorkflow2, DataLane, GuiDataSource]

context_classes = {
    klass.__name__: klass
    for klass in datasource_classes + feature_extractor_classes + classifier_classes + workflow_classes
}


class EntityNotFoundException(Exception):
    def __init__(self, entity_id):
        super().__init__(f"Could find entity with id {entity_id}")


class WebContext:
    objects = {}
    pyid_to_storage_ref = {}

    @classmethod
    def get_class_named(cls, name: str):
        name = name if name in context_classes else name.title().replace("_", "")
        return context_classes[name]

    @classmethod
    def create(cls, klass):
        request_payload = cls.get_request_payload()
        obj = klass.from_json_data(request_payload, dereferencer=cls.dereferencer)
        key = cls.store(obj)
        return obj, key

    @classmethod
    def load(cls, ref: Union[JsonReference, str]) -> Any:
        try:
            ref = ref if isinstance(ref, JsonReference) else JsonReference.from_str(ref)
            return cls.objects[ref]
        except KeyError as e:
            raise EntityNotFoundException(ref) from e

    @classmethod
    def store(cls, obj: Any) -> JsonReference:
        ref = JsonReference.create()
        cls.objects[ref] = obj
        cls.pyid_to_storage_ref[id(obj)] = ref
        return ref

    @classmethod
    def get_ref(cls, obj: Any) -> JsonReference:
        return cls.pyid_to_storage_ref[id(obj)]

    @classmethod
    def referencer(cls, obj: Any) -> Optional[JsonReference]:
        try:
            return cls.get_ref(obj)
        except KeyError:
            return None

    @classmethod
    def dereferencer(cls, ref: JsonReference) -> Any:
        return cls.load(ref)

    @classmethod
    def remove(cls, klass: type, key):
        if not isinstance(key, uuid.UUID):
            key = cls.get_ref(obj)
        target_class = cls.objects[key].__class__
        if not issubclass(target_class, klass):
            raise Exception(f"Unexpected class {target_class} when deleting object with key {key}")
        return cls.objects.pop(key)

    @classmethod
    def get_request_payload(cls):
        payload = {}
        payload.update(flask.request.form)
        for k, v in flask.request.files.items():
            payload[k] = v.read()
        return listify(unflatten(payload))

    @classmethod
    def get_all(cls, klass) -> List[Any]:
        return [obj for obj in cls.objects.values() if isinstance(obj, klass)]
