from typing import Sequence, List, Dict
import multiprocessing
import pickle
import tempfile
import re
import os
import itertools

from vigra.learning import RandomForest as VigraRandomForest
import numpy as np
import h5py

from .pixel_classifier import VigraPixelClassifier
from ilastik.features.ilp_filter import IlpFilter
from ilastik.annotations import Annotation, Color

from ilastik import Project
from lazyflow.classifiers.parallelVigraRfLazyflowClassifier import ParallelVigraRfLazyflowClassifierFactory


class IlpVigraPixelClassifier(VigraPixelClassifier):
    DEFAULT_ILP_CLASSIFIER_FACTORY = pickle.dumps(ParallelVigraRfLazyflowClassifierFactory(), 0)

    def __init__(
        self,
        *,
        feature_extractors: Sequence[IlpFilter],
        forests: List[VigraRandomForest],
        strict: bool = False,
        classes: List[int],
        color_map: Dict[Color, np.uint8],
    ):
        super().__init__(
            feature_extractors=feature_extractors, forests=forests, strict=strict, classes=classes, color_map=color_map
        )

    @classmethod
    def train(
        cls,
        feature_extractors: Sequence[IlpFilter],
        annotations: Sequence[Annotation],
        *,
        num_trees: int = 100,
        num_forests: int = multiprocessing.cpu_count(),
        random_seed: int = 0,
        strict: bool = False,
    ):
        return super().train(
            feature_extractors=feature_extractors,
            annotations=annotations,
            num_trees=num_trees,
            num_forests=num_forests,
            random_seed=random_seed,
            strict=strict,
        )

    @classmethod
    def from_ilp_data(cls, data: h5py.Group) -> "VigraPixelClassifier":
        forest_groups = [data[key] for key in data.keys() if re.match("^Forest\d+$", key)]
        forests = [VigraRandomForest(fg.file.filename, fg.name) for fg in forest_groups]
        feature_extractors = ChannelwiseFilter.from_classifier_feature_names(data["feature_names"])
        classes = list(data["known_labels"][()])
        return cls(feature_extractors=feature_extractors, forests=forests, classes=classes, strict=True)

    def get_forest_data(self):
        tmp_file_handle, tmp_file_path = tempfile.mkstemp(suffix=".h5")
        os.close(tmp_file_handle)
        for forest_index, forest in enumerate(self.forests):
            forest.writeHDF5(tmp_file_path, f"/Forest{forest_index:04d}")
        with h5py.File(tmp_file_path, "r") as f:
            out = Project.h5_group_to_dict(f["/"])
        os.remove(tmp_file_path)
        return out

    @property
    def ilp_data(self) -> dict:
        out = self.get_forest_data()
        feature_names: Iterator[bytes] = itertools.chain(*[ff.to_ilp_feature_names() for ff in self.feature_extractors])
        out["feature_names"] = np.asarray(list(feature_names))
        out[
            "pickled_type"
        ] = b"clazyflow.classifiers.parallelVigraRfLazyflowClassifier\nParallelVigraRfLazyflowClassifier\np0\n."
        out["known_labels"] = np.asarray(self.classes).astype(np.uint32)
        return out

    def __getstate__(self):
        out = self.__dict__.copy()
        forest_data = self.get_forest_data()
        out["forests"] = self.get_forest_data()
        return out

    def __setstate__(self, data):
        forests: List[VigraRandomForest] = []
        tmp_file_handle, tmp_file_path = tempfile.mkstemp(suffix=".h5")
        os.close(tmp_file_handle)
        with h5py.File(tmp_file_path, "r+") as f:
            for forest_key, forest_data in data["forests"].items():
                forest_group = f.create_group(forest_key)
                Project.populate_h5_group(forest_group, forest_data)
                forests.append(VigraRandomForest(tmp_file_path, forest_group.name))
        os.remove(tmp_file_path)

        self.forests = forests
        self.num_trees = data["num_trees"]
        self.strict = data["strict"]
        self.feature_extractors = data["feature_extractors"]
        self.feature_extractor = data["feature_extractor"]
        self.classes = data["classes"]
        self.num_classes = data["num_classes"]
        self.color_map = data["color_map"]

    @property
    def ilp_classifier_factory(self) -> bytes:
        num_trees = sum(f.treeCount() for f in self.forests)
        return pickle.dumps(
            ParallelVigraRfLazyflowClassifierFactory(num_trees_total=num_trees, num_forests=len(self.forests)), 0
        )
