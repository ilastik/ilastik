from typing import Type, Hashable, Optional, List
from urllib.parse import urlparse
from pathlib import Path
from dataclasses import dataclass

import flask

from ilastik.workflows.pixelClassification.pixel_classification_workflow_2 import (
    PixelClassificationWorkflow2,
    DataLane,
    GuiDataSource,
)
from ilastik.server.WebContext import WebContext
from ilastik.classifiers.ilp_pixel_classifier import IlpVigraPixelClassifier
from ilastik.features.ilp_filter import IlpFilter
from ilastik.annotations import Annotation
from ilastik.filesystem import HttpPyFs

from ndstructs.datasource import PrecomputedChunksDataSource


@dataclass
class FeatureSpec:
    name: str
    scale: float
    axis_2d: str
    num_input_channels: int


class PixelClassificationWorkflow2WebAdapter:
    """A class to expose a PixelClassificationWorkflow2 as a web interface"""

    def __init__(self, web_context: Type[WebContext], workflow: PixelClassificationWorkflow2):
        self.web_context = web_context
        self.workflow = workflow

    def _drop_classifier(self) -> None:
        classifier = self.workflow.drop_classifier()
        if classifier is not None:
            self.web_context.remove(self.classificer.__class__, self.classifier)

    def _store_classifier(self, classifier: Optional[IlpVigraPixelClassifier]) -> Optional[Hashable]:
        if classifier is not None:
            return self.web_context.store(classifier)
        else:
            return None

    def add_lane_for_url(self, url: str):
        if url.startswith("precomputed://"):
            url = url.lstrip("precomputed://")
            ds_class = PrecomputedChunksDataSource
        else:
            return flask.Response(f"Unsupported Url: {url}", status=400)

        parsed_url = urlparse(url)
        pathless_url = parsed_url.scheme + "://" + parsed_url.netloc
        if parsed_url.scheme in ("http", "https"):
            fs = HttpPyFs(pathless_url)
        else:
            return flask.Response(f"Unsupported Url: {url}", status=400)

        datasource = ds_class(Path(parsed_url.path), filesystem=fs)
        gui_datasource = GuiDataSource(datasource=datasource)
        lane = DataLane(RawData=gui_datasource)
        self.workflow.add_lane(lane)

        self.web_context.store(datasource)
        self.web_context.store(gui_datasource)

        return flask.jsonify(self.web_context.store(lane).to_json_data())

    def add_feature_extractors(self, extractors: List[IlpFilter], updateClassifier: bool = True) -> flask.Response:
        "Adds feature extractors to workflow, returns uuid of the extractors"
        self._store_classifier(self.workflow.add_feature_extractors(extractors, updateClassifier))
        return flask.jsonify([self.web_context.store(extractor).to_json_data() for extractor in extractors])

    def add_ilp_feature_extractors(self, extractor_specs: List[FeatureSpec]) -> flask.Response:
        extractors = []
        for ex_spec in extractor_specs:
            extractor_class = self.web_context.get_class_named(ex_spec.name)
            extractor = extractor_class.from_ilp_scale(
                scale=ex_spec.scale, axis_2d=ex_spec.axis_2d, num_input_channels=ex_spec.num_input_channels
            )
            extractors.append(extractor)
        return self.add_feature_extractors(extractors)

    def clear_feature_extractors(self, updateClassifier: bool = False) -> flask.Response:
        return self.remove_feature_extractors(self.workflow.feature_extractors, updateClassifier=updateClassifier)

    def remove_feature_extractors(self, extractors: List[IlpFilter], updateClassifier: bool = True) -> flask.Response:
        classifier = self.workflow.remove_feature_extractors(extractors, updateClassifier)
        classifier_id = self._store_classifier(classifier)
        for extractor in extractors:
            self.web_context.remove(IlpFilter, extractor)
        return flask.jsonify(classifier_id)

    def add_annotations(self, annotations: List[Annotation], updateClassifier: bool = True) -> flask.Response:
        "Adds annotations to workflow, returns uuid of the annotations"
        old_num_lanes = len(self.workflow.lanes)
        classifier = self.workflow.add_annotations(annotations, updateClassifier=updateClassifier)
        self._store_classifier(classifier)
        annotation_refs = [self.web_context.store(annotation).to_json_data() for annotation in annotations]
        for lane in self.workflow.lanes[old_num_lanes:]:
            self.web_context.store(lane)
        return flask.jsonify(annotation_refs)

    def remove_annotations(self, annotations: List[Annotation], updateClassifier: bool = True) -> flask.Response:
        classifier = self.workflow.remove_annotations(annotations, updateClassifier=updateClassifier)
        classifier_id = self._store_classifier(classifier)
        return flask.jsonify(classifier_id)

    def get_classifier(self) -> flask.Response:
        if self.workflow.classifier is None:
            self.workflow.try_update_pixel_classifier(True)
        classifier_ref = self._store_classifier(self.workflow.classifier)
        return flask.jsonify(classifier_ref.to_json_data())

    def ilp_project(self) -> flask.Response:
        return flask.send_file(self.workflow.ilp_file, mimetype="application/octet-stream")

    def upload_to_cloud_ilastik(self, cloud_ilastik_token: str, project_name: str) -> flask.Response:
        return flask.jsonify(self.workflow.upload_to_cloud_ilastik(cloud_ilastik_token, project_name))
