from abc import ABCMeta, abstractproperty, abstractmethod
from typing import List, Tuple, Iterable
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from threading import Lock

import numpy as np
import vigra
from vigra.learning import RandomForest
from sklearn.ensemble import RandomForestClassifier as ScikitRandomForestClassifier

from ndstructs import Array5D, Slice5D, Point5D, Shape5D
from ilastik.features.feature_extractor import FeatureExtractor, FeatureData
from ilastik.features.feature_extractor import FeatureExtractorCollection
from ilastik.annotations import Annotation, FeatureSamples, LabelSamples
from ndstructs.datasource import BackedSlice5D
from ndstructs.utils import JsonSerializable


class Predictions(Array5D):
    """An array of floats from 0.0 to 1.0. The value in each channel represents
    how likely that pixel is to belong to the classification class associated with
    that channel"""

    @classmethod
    def allocate(cls, slc: Slice5D, dtype=np.float32, axiskeys: str = Point5D.LABELS, value: int = 0):
        return super().allocate(slc, dtype=dtype, axiskeys=axiskeys, value=value)


class TrainingData:
    X: np.ndarray
    y: np.ndarray
    classes: List[int]

    def __init__(self, feature_extractor: FeatureExtractor, annotations: Tuple[Annotation]):
        samples = [a.get_samples(feature_extractor) for a in annotations]
        gathered_samples = samples[0].concatenate(*samples[1:])
        self.classes = gathered_samples.label.classes
        self.X = gathered_samples.feature.linear_raw()
        self.y = gathered_samples.label.as_incremental().linear_raw().astype(np.uint32)


class PixelClassifier(JsonSerializable):
    def __init__(self, classes: List[int]):
        self.classes = classes
        self.num_classes = len(classes)

    @classmethod
    @lru_cache()
    def get(cls, *classifier_args, **classifier_kwargs):
        return cls(*classifier_args, **classifier_kwargs)

    def get_expected_roi(self, data_slice: BackedSlice5D) -> Slice5D:
        c_start = data_slice.c.start
        c_stop = c_start + self.num_classes
        return data_slice.with_coord(c=slice(c_start, c_stop))

    def allocate_predictions(self, data_slice: Slice5D):
        return Predictions.allocate(self.get_expected_roi(data_slice))

    @abstractmethod
    def predict(self, data_slice: BackedSlice5D, out: Predictions = None) -> Tuple[Predictions, FeatureData]:
        pass


class ScikitLearnPixelClassifier(PixelClassifier):
    def __init__(
        self,
        feature_extractors: Tuple[FeatureExtractor, ...],
        annotations: Tuple[Annotation, ...],
        *,
        num_trees: int = 100,
        random_seed: int = 0,
    ):
        assert len(annotations) > 0
        assert len(feature_extractors) > 0
        self.feature_extractors = FeatureExtractorCollection(feature_extractors)
        training_data = TrainingData(self.feature_extractors, annotations)
        self.forest = ScikitRandomForestClassifier(n_estimators=num_trees, random_state=random_seed)
        self.forest.fit(training_data.X, training_data.y.squeeze())
        super().__init__(classes=training_data.classes)

    def predict(self, data_slice: BackedSlice5D, out: Predictions = None) -> Tuple[Predictions, FeatureData]:
        feature_data = self.feature_extractors.compute(data_slice)
        predictions_shape = data_slice.shape.with_coord(c=self.num_classes)
        predictions_raw_line = self.forest.predict_proba(feature_data.linear_raw())
        # FIXME: should location adjust channels in any way?
        predictions = Predictions.from_line(predictions_raw_line, shape=predictions_shape, location=data_slice.start)
        return predictions, feature_data


class VigraPixelClassifier(JsonSerializable):
    def __init__(
        self,
        feature_extractors: Tuple[FeatureExtractor, ...],
        annotations: Tuple[Annotation, ...],
        *,
        num_trees: int = 100,
        num_forests: int = multiprocessing.cpu_count(),
        random_seed: int = 0,
    ):
        assert len(annotations) > 0
        assert len(feature_extractors) > 0
        self.feature_extractors = FeatureExtractorCollection(feature_extractors)
        self.num_trees = num_trees

        tree_counts = np.array([num_trees // num_forests] * num_forests)
        tree_counts[: num_trees % num_forests] += 1
        tree_counts = list(map(int, tree_counts))

        training_data = TrainingData(self.feature_extractors, annotations)
        self.classes = training_data.classes
        self.num_classes = len(self.classes)
        self.forests = [None] * num_forests
        self.oobs = [None] * num_forests
        with ThreadPoolExecutor(max_workers=num_forests) as executor:

            def train_forest(forest_index):
                self.forests[forest_index] = RandomForest(tree_counts[forest_index])
                self.oobs[forest_index] = self.forests[forest_index].learnRF(
                    training_data.X, training_data.y, random_seed
                )

            for i in range(num_forests):
                executor.submit(train_forest, i)
        super().__init__(classes=training_data.classes)

    def predict(self, data_slice: BackedSlice5D, out: Predictions = None) -> Tuple[Predictions, FeatureData]:
        feature_data = self.feature_extractors.compute(data_slice)
        predictions = out or self.allocate_predictions(data_slice)
        assert predictions.roi == self.get_expected_roi(data_slice)
        raw_linear_predictions = predictions.linear_raw()
        lock = Lock()

        def do_predict(forest):
            nonlocal raw_linear_predictions
            forest_predictions = forest.predictProbabilities(feature_data.linear_raw())
            forest_predictions *= forest.treeCount()
            with lock:
                raw_linear_predictions += forest_predictions

        with ThreadPoolExecutor(max_workers=len(self.forests), thread_name_prefix="predictor") as executor:
            for forest in self.forests:
                executor.submit(do_predict, forest)

        raw_linear_predictions /= self.num_trees

        return predictions, feature_data


class StrictPixelClassifier(PixelClassifier):
    """A PixelClassifier that does not admit data which does not match its FeatureExtractors"""

    def __init__(
        self,
        feature_extractors: Tuple[FeatureExtractor, ...],
        annotations: Tuple[Annotation, ...],
        *,
        num_trees: int = 100,
        num_forests: int = multiprocessing.cpu_count(),
        random_seed: int = 0,
    ):
        extractors = list(feature_extractors)
        for annot in annotations:
            for extractor in extractors:
                extractor.ensure_applicable(annot.raw_data)
        super().__init__(
            feature_extractors=extractors,
            annotations=annotations,
            num_trees=num_trees,
            num_forests=num_forests,
            random_seed=random_seed,
        )

    def predict(self, data_slice: BackedSlice5D, out: Predictions = None) -> Predictions:
        self.feature_extractors.ensure_applicable(data_slice.datasource)
        return super().predict(data_slice, out)
