from abc import ABC, abstractmethod
from typing import List, Iterator, Tuple

import vigra.filters
import numpy as np

from ilastik.array5d import Slice5D, Point5D, Shape5D
from ilastik.array5d import Array5D, Image, ScalarImage, StaticLine, LinearData
from ilastik.features.feature_extractor import FeatureExtractor, FeatureData
from ilastik.data_source import DataSource, DataSourceSlice
from PIL import Image as PilImage

class ScribblingsOutOfBounds(Exception):
    def __init__(self, scribblings:ScalarImage, data_source:DataSource, offset:Point5D):
        super().__init__(f"Scribblings {scribblings} offset by {offset} exceeds bounds of data_source {data_source}")

class WrongShapeException(Exception):
    def __init__(self, path:str, data:np.ndarray):
        super().__init__(f"Annotations from {path} have bad shape: {data.shape}")

class LabelSamples(StaticLine):
    @classmethod
    def create(cls, annotation: 'Annotation'):
        samples = annotation.sample_channels(annotation.as_mask())
        return cls.fromArray5D(samples)

    @property
    def classes(self) -> List[int]:
        return list(np.unique(self.linear_raw()))

class FeatureSamples(FeatureData, StaticLine):
    @classmethod
    def create(cls, scribblings: ScalarImage, data: FeatureData):
        samples = data.sample_channels(scribblings.as_mask())
        return cls.fromArray5D(samples)

class Samples:
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

class Annotation:
    def __init__(self, scribblings:ScalarImage, data_source:DataSource, offset:Point5D=Point5D.zero()):
        assert scribblings.dtype == np.uint32
        assert offset.c == 0

        scribblings_bbox = scribblings.shape.with_coord(c=data_source.shape.c).to_slice_5d()
        self.global_bbox = scribblings_bbox.offset(offset)
        if not data_source.shape.to_slice_5d().contains(self.global_bbox):
            raise ScribblingsOutOfBounds(scribblings=scribblings, data_source=data_source, offset=offset)

        self.scribblings = scribblings
        self.data_source = data_source
        self.offset = offset
        self.data_source_slice = data_source.cut(self.global_bbox)

    @classmethod
    def from_png(cls, path:str, data_source:DataSource, offset:Point5D=Point5D.zero()):
        data = np.asarray(PilImage.open(path)).astype(np.uint32)
        return cls(ScalarImage(data, 'yx'), data_source, offset=offset)

    def get_samples(self, feature_extractor:FeatureExtractor) -> Samples:
        all_label_samples = []
        all_feature_samples = []
        for data_slice in self.data_source_slice.get_tiles(): #tiling allows for caching of the features
            data_roi = data_slice.roi().clamped_with_slice(self.global_bbox)
            scribblings_roi = data_roi.offset(- self.offset).with_full_c()
            feature_roi = data_roi.mod_tile(self.data_source.tile_shape).with_full_c()

            scribblings_tile = self.scribblings.cut(scribblings_roi)
            feature_tile = feature_extractor.compute(data_slice).cut(feature_roi)

            label_samples = LabelSamples.create(scribblings_tile)
            feature_samples = FeatureSamples.create(scribblings_tile, feature_tile)
            assert feature_samples.shape.c == feature_extractor.get_expected_shape(data_slice).c
            all_label_samples.append(label_samples)
            all_feature_samples.append(feature_samples)
        return Samples(label_samples=all_label_samples[0].concatenate(*all_label_samples[1:]),
                       feature_samples=all_feature_samples[0].concatenate(*all_feature_samples[1:]))

    def __repr__(self):
        return f"<Annotation {self.scribblings.shape} for data_source: {self.data_source}>"
