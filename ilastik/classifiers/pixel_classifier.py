from typing import List, Tuple
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from threading import Lock

import numpy as np
import vigra
from vigra.learning import RandomForest

from ilastik.array5d.array5D import Array5D, Slice5D, Point5D, Shape5D
from ilastik.features.feature_extractor import FeatureExtractor, FeatureData
from ilastik.annotations import Annotation, FeatureSamples, LabelSamples
from ilastik.data_source import DataSource
from ilastik.utility import JsonSerializable

class Predictions(Array5D):
    """An array of floats from 0.0 to 1.0. The value in each channel represents
    how likely that pixel is to belong to the classification class associated with
    that channel"""
    @classmethod
    def allocate(cls, slc:Slice5D, dtype=np.float32, axiskeys:str=Point5D.LABELS, value:int=0):
        return super().allocate(slc, dtype=dtype, axiskeys=axiskeys, value=value)

    def show(self):
        return self.as_uint8().show_channels()

    def as_pil_images(self):
        pil_channel_images = []
        for img in self.as_uint8().images():
            for c in img.channels():
                pil_channel_images.append(c.as_pil_images()[0])
        return pil_channel_images

class PixelClassifier(JsonSerializable):
    def __init__(self, feature_extractor:FeatureExtractor, annotations:List[Annotation],*,
                 num_trees:int=100, num_forests:int=multiprocessing.cpu_count(), random_seed:int=0):
        assert len(annotations) > 0
        self.feature_extractor = feature_extractor
        self.num_trees = num_trees

        tree_counts = np.array( [num_trees // num_forests] * num_forests )
        tree_counts[:num_trees % num_forests] += 1
        tree_counts = list(map(int, tree_counts))

        samples = [a.get_samples(feature_extractor) for a in annotations]
        gathered_samples = samples[0].concatenate(*samples[1:])

        self.classes = gathered_samples.label.classes
        self.num_classes = len(self.classes)

        X = gathered_samples.feature.linear_raw()
        y = gathered_samples.label.linear_raw().astype(np.uint32)
        self.forests = [None] * num_forests
        self.oobs = [None] * num_forests
        with ThreadPoolExecutor(max_workers=num_forests) as executor:
            def train_forest(forest_index):
                self.forests[forest_index] = RandomForest(tree_counts[forest_index])
                self.oobs[forest_index] = self.forests[forest_index].learnRF(X, y, random_seed)
            for i in range(num_forests):
                executor.submit(train_forest, i)

    @classmethod
    @lru_cache()
    def get(cls, *classifier_args, **classifier_kwargs):
        return cls(*classifier_args, **classifier_kwargs)

    def get_expected_roi(self, data_slice:DataSource):
        c_start = data_slice.c.start
        c_stop = c_start + self.num_classes
        return data_slice.with_coord(c=slice(c_start, c_stop))

    def allocate_predictions(self, data_slice:DataSource):
        return Predictions.allocate(self.get_expected_roi(data_slice))

    def predict(self, data_slice:DataSource, out:Predictions=None) -> Predictions:
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

        return predictions, feature_data

class StrictPixelClassifier(PixelClassifier):
    """A PixelClassifier that does not admit data which does not match its FeatureExtractors"""

    def __init__(self, feature_extractor:FeatureExtractor, annotations:List[Annotation], *args, **kwargs):
        for annot in annotations:
            feature_extractor.ensure_applicable(annot.raw_data)
        super().__init__(feature_extractor, annotations, *args, **kwargs)

    def predict(self, data_slice:DataSource, out:Predictions=None) -> Predictions:
        self.feature_extractor.ensure_applicable(data_slice)
        return super().predict(data_slice, out)
