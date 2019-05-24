from abc import ABC, abstractmethod
from typing import List, Iterator, Tuple

import vigra.filters
import numpy as np

from ilastik.array5d import Slice5D, Point5D, Shape5D
from ilastik.array5d import Array5D, Image, ScalarImage, StaticLine, LinearData
from ilastik.features.feature_extractor import FeatureExtractor, FeatureData
from ilastik.data_source import DataSource, DataSourceSlice
from PIL import Image as PilImage

class Scribblings(ScalarImage):
    """Single-channel image containing user scribblings"""

    def __init__(self, arr:np.ndarray, axiskeys:str):
        super().__init__(arr, axiskeys)
        assert self.dtype == np.uint32

    def __hash__(self):
        return hash(self._data.tobytes())

    def __eq__(self, other):
        if isinstance(other, Scribblings):
            return False
        return np.all(self._data == other._data)

class LabelSamples(StaticLine):
    """A single-channel array with a single spacial dimension containing integers
    representing the class to which a pixel belongs"""

    @classmethod
    def create(cls, annotation: 'Annotation'):
        samples = annotation.sample_channels(annotation.as_mask())
        return cls.fromArray5D(samples)

    @property
    def classes(self) -> List[int]:
        return list(np.unique(self.linear_raw()))

class FeatureSamples(FeatureData, StaticLine):
    """A multi-channel array with a single spacial dimension, with eac channel
    representing a feature calculated on top of a annotated pixel"""

    @classmethod
    def create(cls, scribblings: Scribblings, data: FeatureData):
        samples = data.sample_channels(scribblings.as_mask())
        return cls.fromArray5D(samples)

class Samples:
    """A mapping from pixel labels to pixel features"""

    def __init__(self, feature_samples:FeatureSamples, label_samples:LabelSamples):
        assert feature_samples.length == label_samples.length
        self.feature = feature_samples
        self.label = label_samples

    def count(self) -> int:
        return self.label.shape.x

    def concatenate(self, *others:List['Samples']):
        all_features = self.feature.concatenate(*[sample.feature for sample in others])
        all_labels = self.label.concatenate(*[sample.label for sample in others])
        return Samples(feature_samples=all_features, label_samples=all_labels)

class ScribblingsOutOfBounds(Exception):
    def __init__(self, scribblings:Scribblings, raw_data:DataSource, offset:Point5D):
        super().__init__(f"Scribblings {scribblings} offset by {offset} exceeds bounds of raw_data {raw_data}")

class WrongShapeException(Exception):
    def __init__(self, path:str, data:np.ndarray):
        super().__init__(f"Annotations from {path} have bad shape: {data.shape}")

class Annotation:
    """User scribblings attached to the raw data onto which they were drawn"""

    def __init__(self, scribblings:Scribblings, raw_data:DataSource, offset:Point5D=Point5D.zero()):
        assert offset.c == 0

        self.data_roi = scribblings.shape.to_slice_5d().offset(offset).with_full_c()
        if not raw_data.contains(self.data_roi):
            raise ScribblingsOutOfBounds(scribblings=scribblings, raw_data=raw_data, offset=offset)

        self.scribblings = scribblings
        self.raw_data = raw_data
        self.offset = offset
        self.raw_data_slice = raw_data.cut(self.data_roi)

    @classmethod
    def from_png(cls, path:str, raw_data:DataSource, offset:Point5D=Point5D.zero()):
        data = np.asarray(PilImage.open(path)).astype(np.uint32)
        return cls(Scribblings(data, 'yx'), raw_data, offset=offset)

    def get_samples(self, feature_extractor:FeatureExtractor) -> Samples:
        all_label_samples = []
        all_feature_samples = []
        for data_tile in self.raw_data_slice.get_tiles(): #tiling allows for caching of the features
            scribbled_area = data_tile.clamped_with_slice(self.data_roi)
            scribblings_roi = scribbled_area.offset(- self.offset).with_full_c()
            feature_roi = scribbled_area.mod_tile().with_full_c()

            scribblings_tile = self.scribblings.cut(scribblings_roi)
            feature_tile = feature_extractor.compute(data_tile).cut(feature_roi)

            label_samples = LabelSamples.create(scribblings_tile)
            feature_samples = FeatureSamples.create(scribblings_tile, feature_tile)
            assert feature_samples.shape.c == feature_extractor.get_expected_shape(data_tile).c
            all_label_samples.append(label_samples)
            all_feature_samples.append(feature_samples)
        return Samples(label_samples=all_label_samples[0].concatenate(*all_label_samples[1:]),
                       feature_samples=all_feature_samples[0].concatenate(*all_feature_samples[1:]))

    def __repr__(self):
        return f"<Annotation {self.scribblings.shape} for raw_data: {self.raw_data}>"
