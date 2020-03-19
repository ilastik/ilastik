from abc import abstractmethod
from typing import List, Tuple, Iterable, Optional, Sequence, Dict
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from threading import Lock

import numpy as np
import vigra
from vigra.learning import RandomForest as VigraRandomForest
from sklearn.ensemble import RandomForestClassifier as ScikitRandomForestClassifier

from ndstructs import Array5D, Slice5D, Point5D, Shape5D
from ilastik.features.feature_extractor import FeatureExtractor, FeatureData, ChannelwiseFilter
from ilastik.features.feature_extractor import FeatureExtractorCollection
from ilastik.annotations import Annotation, FeatureSamples, Color
from ndstructs.datasource import DataSourceSlice, DataSource
from ndstructs.utils import JsonSerializable, from_json_data


class Predictions(Array5D):
    """An array of floats from 0.0 to 1.0. The value in each channel represents
    how likely that pixel is to belong to the classification class associated with
    that channel"""

    def __init__(
        self, arr: np.ndarray, *, axiskeys: str, location: Point5D = Point5D.zero(), color_map: Dict[Color, np.uint8]
    ):
        super().__init__(arr, axiskeys=axiskeys, location=location)
        self.color_map = color_map

    def rebuild(self, arr: np.ndarray, axiskeys: str, location: Point5D = None) -> "Annotation":
        location = self.location if location is None else location
        return self.__class__(arr, axiskeys=axiskeys, location=location, color_map=self.color_map)

    @classmethod
    def allocate(
        cls, *, slc: Slice5D, dtype=np.float32, axiskeys: str = Point5D.LABELS, color_map: Dict[Color, np.uint8]
    ):
        arr = Array5D.allocate(slc, dtype=dtype, axiskeys=axiskeys, value=0)
        return cls(arr._data, axiskeys=arr.axiskeys, location=arr.location, color_map=color_map)


class TrainingData:
    feature_extractors: Sequence[FeatureExtractor]
    combined_extractor: FeatureExtractor
    strict: bool
    color_map: Dict[Color, np.uint8]
    classes: List[int]
    X: np.ndarray  # shape is (num_samples, num_feature_channels)
    y: np.ndarray  # shape is (num_samples, 1)

    def __init__(
        self, *, feature_extractors: Sequence[FeatureExtractor], annotations: Sequence[Annotation], strict: bool
    ):
        assert len(annotations) > 0
        assert len(feature_extractors) > 0
        if strict:
            (fx.ensure_applicable(annot.raw_data) for annot in annotations for fx in feature_extractors)
        annotations = Annotation.sort(annotations)  # sort so the meaning of the channels is always predictable
        combined_extractor = FeatureExtractorCollection(feature_extractors)
        feature_samples = [a.get_feature_samples(combined_extractor) for a in annotations]

        self.feature_extractors = feature_extractors
        self.combined_extractor = combined_extractor
        self.strict = strict
        self.color_map = Color.create_color_map(annot.color for annot in annotations)
        self.classes = list(self.color_map.values())
        self.X = np.concatenate([fs.X for fs in feature_samples])
        self.y = np.concatenate(
            [fs.get_y(self.color_map[annot.color]) for fs, annot in zip(feature_samples, annotations)]
        )
        assert self.X.shape[0] == self.y.shape[0]


class PixelClassifier(JsonSerializable):
    def __init__(
        self,
        *,
        feature_extractors: List[FeatureExtractor],
        classes: List[int],
        strict: bool,
        color_map: Dict[Color, np.uint8],
    ):
        self.strict = strict
        self.feature_extractors = feature_extractors
        self.feature_extractor = FeatureExtractorCollection(feature_extractors)
        self.classes = classes
        self.num_classes = len(classes)
        self.color_map = color_map

    @classmethod
    @lru_cache()
    def get(cls, *classifier_args, **classifier_kwargs):
        return cls(*classifier_args, **classifier_kwargs)

    def get_expected_roi(self, data_slice: Slice5D) -> Slice5D:
        c_start = data_slice.c.start
        c_stop = c_start + self.num_classes
        return data_slice.with_coord(c=slice(c_start, c_stop))

    def allocate_predictions(self, data_slice: Slice5D):
        return Predictions.allocate(slc=self.get_expected_roi(data_slice), color_map=self.color_map)

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
        feature_extractors: Sequence[FeatureExtractor],
        forest: ScikitRandomForestClassifier,
        classes: List[int],
        strict: bool = False,
        color_map: Dict[Color, np.uint8],
    ):
        super().__init__(classes=classes, feature_extractors=feature_extractors, strict=strict, color_map=color_map)
        self.forest = forest

    @classmethod
    def train(
        cls,
        feature_extractors: Sequence[FeatureExtractor],
        annotations: Sequence[Annotation],
        *,
        num_trees: int = 100,
        random_seed: int = 0,
        strict: bool = False,
    ) -> "ScikitLearnPixelClassifier":
        training_data = TrainingData(feature_extractors=feature_extractors, annotations=annotations, strict=strict)
        forest = ScikitRandomForestClassifier(n_estimators=num_trees, random_state=random_seed)
        forest.fit(training_data.X, training_data.y.squeeze())
        return cls(
            forest=forest,
            feature_extractors=feature_extractors,
            classes=training_data.classes,
            strict=strict,
            color_map=training_data.color_map,
        )

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
    def __init__(
        self,
        *,
        feature_extractors: Sequence[FeatureExtractor],
        forests: List[VigraRandomForest],
        classes: List[int],
        strict: bool = False,
        color_map: Dict[Color, np.uint8],
    ):
        super().__init__(classes=classes, feature_extractors=feature_extractors, strict=strict, color_map=color_map)
        self.forests = forests
        self.num_trees = sum(f.treeCount() for f in forests)

    @classmethod
    def train(
        cls,
        feature_extractors: Sequence[FeatureExtractor],
        annotations: Sequence[Annotation],
        *,
        num_trees: int = 100,
        num_forests: int = multiprocessing.cpu_count(),
        random_seed: int = 0,
        strict: bool = False,
    ):
        training_data = TrainingData(feature_extractors=feature_extractors, annotations=annotations, strict=strict)

        tree_counts = np.array([num_trees // num_forests] * num_forests)
        tree_counts[: num_trees % num_forests] += 1
        tree_counts = list(map(int, tree_counts))

        forests = [VigraRandomForest(tree_counts[forest_index]) for forest_index in range(num_forests)]

        def train_forest(forest_index):
            forests[forest_index].learnRF(training_data.X, training_data.y, random_seed)

        with ThreadPoolExecutor(max_workers=num_forests) as executor:
            for i in range(num_forests):
                executor.submit(train_forest, i)
        return cls(
            feature_extractors=feature_extractors,
            forests=forests,
            strict=strict,
            classes=training_data.classes,
            color_map=training_data.color_map,
        )

    @classmethod
    def from_json_data(cls, data: dict) -> "VigraPixelClassifier":
        return from_json_data(cls.train, data)

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
