from typing import Optional, Dict, Hashable
import uuid

import flask

from ndstructs import Point5D, Slice5D, Shape5D, Array5D
from ndstructs.datasource import DataSource, DataSourceSlice, SequenceDataSource
from ndstructs.utils import JsonSerializable, from_json_data

from ilastik.utility import flatten, unflatten, listify
from ilastik.annotations import Annotation
from ilastik.classifiers.pixel_classifier import (
    PixelClassifier,
    Predictions,
    VigraPixelClassifier,
    ScikitLearnPixelClassifier,
)
from ilastik.workflows.pixelClassification.pixel_classification_workflow_2 import PixelClassificationWorkflow2
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


datasource_classes = [DataSource, SequenceDataSource]

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

workflow_classes = {
    klass.__name__: klass
    for klass in datasource_classes + feature_extractor_classes + classifier_classes + [PixelClassificationWorkflow2]
}


class EntityNotFoundException(Exception):
    def __init__(self, entity_id):
        super().__init__(f"Could find entity with id {entity_id}")


class WebContext:
    objects = {}
    pyid_to_objid = {}

    @classmethod
    def do_rpc(cls):
        request_payload = cls.get_request_payload()
        obj = cls.load(request_payload.pop("self"))

    @classmethod
    def get_class_named(cls, name: str):
        name = name if name in workflow_classes else name.title().replace("_", "")
        return workflow_classes[name]

    @classmethod
    def create(cls, klass):
        request_payload = cls.get_request_payload()
        obj = klass.from_json_data(request_payload)
        key = cls.store(obj, obj_id=request_payload.get("id"))
        return obj, key

    @classmethod
    def load(cls, key):
        try:
            return cls.objects[key]
        except KeyError as e:
            raise EntityNotFoundException(key) from e

    @classmethod
    def store(cls, obj, obj_id: Optional[Hashable] = None):
        obj_id = obj_id if obj_id is not None else uuid.uuid4()
        key = f"pointer@{obj_id}"
        cls.objects[key] = obj
        cls.pyid_to_objid[id(obj)] = obj_id
        return key

    @classmethod
    def get_id(cls, obj) -> uuid.UUID:
        return cls.pyid_to_objid[id(obj)]

    @classmethod
    def referencer(cls, obj) -> Optional[str]:
        try:
            return "pointer@" + str(cls.get_id(obj))
        except KeyError:
            return None

    @classmethod
    def remove(cls, klass: type, key):
        if not isinstance(key, uuid.UUID):
            key = cls.get_id(obj)
        target_class = cls.objects[key].__class__
        if not issubclass(target_class, klass):
            raise Exception(f"Unexpected class {target_class} when deleting object with key {key}")
        return cls.objects.pop(key)

    @classmethod
    def get_request_payload(cls):
        payload = {}
        for k, v in flask.request.form.items():
            if isinstance(v, str) and v.startswith("pointer@"):
                payload[k] = cls.load(v)
            else:
                payload[k] = v
        for k, v in flask.request.files.items():
            payload[k] = v.read()
        return listify(unflatten(payload))

    @classmethod
    def get_all(cls, klass) -> Dict[str, object]:
        return {key: obj for key, obj in cls.objects.items() if isinstance(obj, klass)}
