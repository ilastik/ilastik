from typing import List
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

import numpy as np
import vigra
from vigra.learning import RandomForest

from ilastik.array5d.array5D import Array5D, Slice5D
from ilastik.features.feature_extractor import FeatureCollection, FeatureData
from ilastik.annotations import Annotation
from ilastik.data_source import DataSource, DataSpec

class Predictions(Array5D):
    """An array of floats from 0.0 to 1.0. Teh value in each channel represents
    how likely that pixel is to belong to the classification class associated with
    that channel"""
    def as_uint8(self):
        return Array5D((self._data * 255).astype(np.uint8), axiskeys=self.axiskeys)

class PixelClassifier:
    def __init__(self, feature_collection:FeatureCollection, annotations:List[Annotation],
                 num_trees=100, num_forests=None, variable_importance_path=None,
                 variable_importance_enabled=False):
        assert len(annotations) > 0
        self.feature_collection = feature_collection
        self.num_trees = num_trees
        num_forests = num_forests or multiprocessing.cpu_count()

        tree_counts = np.array( [num_trees // num_forests] * num_forests )
        tree_counts[:num_trees % num_forests] += 1
        tree_counts = list(map(int, tree_counts))

        samples = annotations[0].get_samples(feature_collection)
        raw_X = samples.features.linear_raw()
        raw_y = samples.labels.linear_raw()
        #TODO: maybe concatenate eveything at once? Or prealloc and index?
        for annotation in annotations[1:]:
            extra_samples = annotation.get_samples(feature_collection)
            raw_X = np.concatenate((raw_X, extra_samples.features.linear_raw()), axis=0)
            raw_y = np.concatenate((raw_y, extra_samples.labels.linear_raw()), axis=0)
        self.classes = list(np.unique(raw_y))
        self.num_classes = len(self.classes)

        self.forests = [None] * num_forests
        with ThreadPoolExecutor(max_workers=num_forests) as executor:
            def train_forest(forest_index):
                self.forests[forest_index] = RandomForest(tree_counts[forest_index])
                self.oobs[forest_index] = self.forests[forest_index].learnRF(raw_X, raw_y)
            for i in range(num_forests):
                executor.submit(train_forest, i)

    def get_expected_shape(self, data_spec:DataSpec):
        input_channels = data_spec.shape.c
        return data_spec.shape.with_coord(c=self.num_classes)

    def allocate_predictions(self, data_spec:DataSpec):
        return Predictions.allocate(self.get_expected_shape(data_spec), dtype=np.float32, value=0)

    def predict(self, data_spec:DataSpec) -> Predictions:
        feature_data = self.feature_collection.compute(data_spec)
        total_predictions = None
        lock = Lock()

        def do_predict(forest):
            nonlocal total_predictions
            forest_predictions = forest.predictProbabilities(feature_data.linear_raw())
            forest_predictions *= forest.treeCount()
            with lock:
                if total_predictions is None:
                    total_predictions = forest_predictions
                else:
                    total_predictions += forest_predictions

        with ThreadPoolExecutor(max_workers=len(self.forests), thread_name_prefix="predictor") as executor:
            for forest in self.forests:
                executor.submit(do_predict, forest)

        total_predictions /= self.num_trees

        out_shape = feature_data.with_c_as_last_axis().rawshape.to_shape_tuple(with_c=self.num_classes)
        out_axiskeys =  feature_data.with_c_as_last_axis().axiskeys

        reshaped_predictions = total_predictions.reshape(out_shape)
        return Predictions(reshaped_predictions, out_axiskeys)
