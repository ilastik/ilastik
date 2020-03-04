from abc import ABCMeta, abstractproperty, abstractmethod
from typing import List, Tuple, Iterable, Optional
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
import re
from threading import Lock

import numpy as np
import vigra
import h5py
from vigra.learning import RandomForest as VigraRandomForest
from sklearn.ensemble import RandomForestClassifier as ScikitRandomForestClassifier

from ndstructs import Array5D, Slice5D, Point5D, Shape5D
from ilastik.features.feature_extractor import FeatureExtractor, FeatureData
from ilastik.features.feature_extractor import FeatureExtractorCollection
from ilastik.annotations import Annotation, FeatureSamples, LabelSamples
from ndstructs.datasource import DataSourceSlice, DataSource
from ndstructs.utils import JsonSerializable, from_json_data


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
    num_classes: int

    def __init__(self, feature_extractor: FeatureExtractor, annotations: Tuple[Annotation]):
        samples = [a.get_samples(feature_extractor) for a in annotations]
        gathered_samples = samples[0].concatenate(*samples[1:])
        self.num_classes = len(gathered_samples.label.classes)
        self.X = gathered_samples.feature.linear_raw()
        self.y = gathered_samples.label.as_incremental().linear_raw().astype(np.uint32)


class PixelClassifier(JsonSerializable):
    def __init__(self, feature_extractor: FeatureExtractor, num_classes: int, strict: bool):
        self.strict = strict
        self.feature_extractor = feature_extractor
        self.num_classes = num_classes

    @classmethod
    @lru_cache()
    def get(cls, *classifier_args, **classifier_kwargs):
        return cls(*classifier_args, **classifier_kwargs)

    def get_expected_roi(self, data_slice: Slice5D) -> Slice5D:
        c_start = data_slice.c.start
        c_stop = c_start + self.num_classes
        return data_slice.with_coord(c=slice(c_start, c_stop))

    def allocate_predictions(self, data_slice: Slice5D):
        return Predictions.allocate(self.get_expected_roi(data_slice))

    def predict(self, data_slice: DataSourceSlice, out: Predictions = None) -> Predictions:
        if self.strict:
            self.feature_extractor.ensure_applicable(data_slice.datasource)
        return self._do_predict(data_slice=data_slice, out=out)

    @abstractmethod
    def _do_predict(self, data_slice: DataSourceSlice, out: Predictions = None) -> Predictions:
        pass


class PixelClassifierDataSource(DataSource):
    def __init__(self, classifier: PixelClassifier, raw_datasource: DataSource):
        expected_roi = classifier.get_expected_roi(raw_datasource.roi)
        super().__init__(
            url=f"classification of {raw_datasource} via {classifier.__class__.__name__}",
            tile_shape=raw_datasource.tile_shape,
            dtype=np.dtype("float32"),
            name=f"PixelClassifierDataSource[{raw_datasource.name}]",
            shape=expected_roi.shape,
            location=expected_roi.start,
        )
        self.classifier = classifier
        self.raw_datasource = raw_datasource

    def _get_tile(self, tile: Slice5D) -> Predictions:
        raw_slice = tile.with_coord(c=self.raw_datasource.roi.c)
        data_slice = DataSourceSlice(datasource=self.raw_datasource, **raw_slice.to_dict())
        return self.classifier.predict(data_slice)


class ScikitLearnPixelClassifier(PixelClassifier):
    def __init__(
        self,
        *,
        feature_extractor: FeatureExtractor,
        forest: ScikitRandomForestClassifier,
        num_classes: int,
        strict: bool = False,
    ):
        super().__init__(num_classes=forest.n_classes_, feature_extractor=feature_extractor, strict=strict)
        self.forest = forest

    @classmethod
    def train(
        cls,
        feature_extractors: Tuple[FeatureExtractor, ...],
        annotations: Tuple[Annotation, ...],
        *,
        num_trees: int = 100,
        random_seed: int = 0,
        strict: bool = False,
    ) -> "ScikitLearnPixelClassifier":
        fx_collection = FeatureExtractorCollection(feature_extractors)
        assert len(annotations) > 0
        if strict:
            for annot in annotations:
                fx_collection.ensure_applicable(annot.raw_data)

        training_data = TrainingData(fx_collection, annotations)
        forest = ScikitRandomForestClassifier(n_estimators=num_trees, random_state=random_seed)
        forest.fit(training_data.X, training_data.y.squeeze())
        print(cls)
        return cls(forest=forest, feature_extractor=fx_collection, num_classes=training_data.num_classes, strict=strict)

    @classmethod
    def from_json_data(cls, data: dict) -> "ScikitLearnPixelClassifier":
        return from_json_data(cls.train, data)

    def _do_predict(self, data_slice: DataSourceSlice, out: Optional[Predictions] = None) -> Predictions:
        feature_data = self.feature_extractor.compute(data_slice)
        predictions_shape = data_slice.shape.with_coord(c=self.num_classes)
        predictions_raw_line = self.forest.predict_proba(feature_data.linear_raw())
        predictions = Predictions.from_line(predictions_raw_line, shape=predictions_shape, location=data_slice.start)
        if out is not None:
            assert out.shape == predictions.shape
            out.localSet(predictions)
            return out, feature_data
        else:
            return predictions


class VigraPixelClassifier(PixelClassifier):
    def __init__(self, *, feature_extractor: FeatureExtractor, forests: List[VigraRandomForest], strict: bool = False):
        super().__init__(num_classes=forests[0].labelCount(), feature_extractor=feature_extractor, strict=strict)
        self.forests = forests
        self.num_trees = sum(f.treeCount() for f in forests)

    @classmethod
    def train(
        cls,
        feature_extractors: Tuple[FeatureExtractor, ...],
        annotations: Tuple[Annotation, ...],
        *,
        num_trees: int = 100,
        num_forests: int = multiprocessing.cpu_count(),
        random_seed: int = 0,
        strict: bool = False,
    ):
        fx_collection = FeatureExtractorCollection(feature_extractors)
        assert len(annotations) > 0
        if strict:
            for annot in annotations:
                fx_collection.ensure_applicable(annot.raw_data)

        training_data = TrainingData(fx_collection, annotations)

        tree_counts = np.array([num_trees // num_forests] * num_forests)
        tree_counts[: num_trees % num_forests] += 1
        tree_counts = list(map(int, tree_counts))

        forests = [VigraRandomForest(tree_counts[forest_index]) for forest_index in range(num_forests)]

        def train_forest(forest_index):
            forests[forest_index].learnRF(training_data.X, training_data.y, random_seed)

        with ThreadPoolExecutor(max_workers=num_forests) as executor:
            for i in range(num_forests):
                executor.submit(train_forest, i)
        return cls(feature_extractor=fx_collection, forests=forests, strict=strict)

    @classmethod
    def from_json_data(cls, data: dict) -> "VigraPixelClassifier":
        return from_json_data(cls.train, data)

    @classmethod
    def from_ilp_group(cls, group: h5py.Group) -> "VigraPixelClassifier":
        forest_groups = [group[key] for key in group.keys() if re.match("^Forest\d+$", key)]
        forests = [VigraRandomForest(fg.file.filename, fg.name) for fg in forest_groups]
        feature_extractors = FeatureExtractor.from_classifier_feature_names(group["feature_names"])
        fx_collection = FeatureExtractorCollection(feature_extractors)
        return cls(feature_extractor=fx_collection, forests=forests, strict=True)

    def _do_predict(self, data_slice: DataSourceSlice, out: Predictions = None) -> Predictions:
        feature_data = self.feature_extractor.compute(data_slice)
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

        return predictions
