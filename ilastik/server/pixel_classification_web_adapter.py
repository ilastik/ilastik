from typing import Type, Hashable, Optional, List
from ilastik.workflows.pixelClassification.pixel_classification_workflow_2 import PixelClassificationWorkflow2
from ilastik.server.WebContext import WebContext
from ilastik.classifiers.ilp_pixel_classifier import IlpVigraPixelClassifier
from ilastik.features.ilp_filter import IlpFilter
from ilastik.annotations import Annotation


class PixelClassificationWorkflow2WebAdapter:
    def __init__(self, *, web_context: Type[WebContext], workflow: PixelClassificationWorkflow2):
        self.web_context = web_context
        self.workflow = workflow

    def drop_classifier(self) -> None:
        classifier = self.workflow.drop_classifier()
        if classifier is not None:
            self.web_context.remove(self.classificer.__class__, self.classifier)

    def store_classifier(self, classifier: Optional[IlpVigraPixelClassifier]) -> Optional[Hashable]:
        if classifier is not None:
            return self.web_context.store(classifier)
        return None

    def add_feature_extractors(self, extractors: List[IlpFilter], updateClassifier: bool = True) -> List[Hashable]:
        "Adds feature extractors to workflow, returns uuid of the extractors"
        self.store_classifier(self.workflow.add_feature_extractors(extractors, updateClassifier))
        return [self.web_context.store(extractor) for extractor in extractors]

    def remove_feature_extractors(
        self, extractors: List[IlpFilter], updateClassifier: bool = True
    ) -> Optional[Hashable]:
        out = self.store_classifier(self.workflow.remove_feature_extractors(extractors, updateClassifier))
        for extractor in extractors:
            self.web_context.remove(extractor)
        return out

    def add_annotations(self, annotations: List[Annotation], updateClassifier: bool = True) -> List[Hashable]:
        "Adds annotations to workflow, returns uuid of the annotations"
        self.store_classifier(self.workflow.add_annotations(annotations, updateClassifier=updateClassifier))
        return [self.web_context.store(annotation) for annotation in annotations]

    def remove_annotations(self, annotations: List[Annotation], updateClassifier: bool = True) -> Optional[Hashable]:
        return self.store_classifier(self.workflow.remove_annotations(annotations, updateClassifier=updateClassifier))

    def get_classifier(self) -> Optional[Hashable]:
        if self.workflow.classifier is None:
            self.workflow.try_update_pixel_classifier(True)
        return self.store_classifier(self.workflow.classifier)
