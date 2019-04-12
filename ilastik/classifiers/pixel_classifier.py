from typing import List
import multiprocessing
from threading import Lock

import numpy as np
from vigra.learning import RandomForest

from ilastik.features.feature_extractor import FeatureCollection, FeatureData
from ilastik.labels.annotation import Annotation 

class PixelClassifier:
    def __init__(self, feature_collection:FeatureCollection, annotations:List[Annotation],
                 num_trees=100, num_forests=None, variable_importance_path=None,
                 variable_importance_enabled=False):
        assert len(annotations) > 0
        self.num_trees = num_trees
        num_forests = num_forests or multiprocessing.cpu_count()

        tree_counts = np.array( [num_trees // num_forests] * num_forests )
        tree_counts[:num_trees % num_forests] += 1
        tree_counts = list(map(int, tree_counts))

        #FIXME: concatenate annotation samples!
        X, y = annotations[0].get_samples(feature_collection)
        import pydevd; pydevd.settrace()

        self.forests = [RandomForest(tc) for tc in tree_counts]
        self.oobs = [forest.learnRF(X.linear_raw(), y.raw()) for forest in self.forests]

    def predict(self, X:FeatureData):
        total_predictions = None
        for forest in self.forests:
            forest_predictions = forest.predictProbabilities(X.linear_raw())
            forest_predictions *= forest.treeCount()
            if total_predictions is None:
                total_predictions = forest_predictions
            else:
                total_predictions += forest_predictions

        return total_predictions / self.num_trees
 
