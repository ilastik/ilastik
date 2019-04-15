from typing import List
import multiprocessing
from threading import Lock

import numpy as np
import vigra
from vigra.learning import RandomForest

from ilastik.array5d.array5D import Array5D
from ilastik.features.feature_extractor import FeatureCollection, FeatureData
from ilastik.labels.annotation import Annotation 

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

        #FIXME: concatenate annotation samples!
        X, y = annotations[0].get_samples(feature_collection)

        self.forests = [RandomForest(tc) for tc in tree_counts]
        self.oobs = [forest.learnRF(X.linear_raw(), y.raw()) for forest in self.forests]

    def predict(self, raw_data:Array5D):
        feature_data = self.feature_collection.compute(raw_data)

        total_predictions = None
        for forest in self.forests:
            forest_predictions = forest.predictProbabilities(feature_data.linear_raw())
            forest_predictions *= forest.treeCount()
            if total_predictions is None:
                total_predictions = forest_predictions
            else:
                total_predictions += forest_predictions

        total_predictions /= self.num_trees

        num_classes = total_predictions.shape[-1]
        raw_out_shape = raw_data.with_c_as_last_axis().rawshape.to_shape_tuple(with_c=num_classes)
        out_axiskeys =  raw_data.with_c_as_last_axis().axiskeys

        import pydevd; pydevd.settrace()
        reshaped_predictions = total_predictions.reshape(raw_out_shape)
        tagged_view = vigra.taggedView(reshaped_predictions, axistags=out_axiskeys)
        return Array5D(tagged_view)
