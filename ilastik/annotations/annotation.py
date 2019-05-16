from abc import ABC, abstractmethod
from typing import List, Iterator, Tuple

import vigra.filters
import numpy as np

from ilastik.array5d import Slice5D, Point5D, Shape5D
from ilastik.array5d import Array5D, Image, ScalarImage, StaticLine, LinearData
from ilastik.features.feature_extractor import FeatureExtractor, FeatureData
from ilastik.data_source import DataSource, DataSourceSlice
from PIL import Image as PilImage

class AnnotationOutOfBounds(Exception):
    def __init__(self, annotation:'Annotation', data_source:DataSource, offset:Point5D):
        super().__init__(f"Annotation {annotation} offset by {offset} exceeds bounds of data_source {data_source}")

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
    def create(cls, annotation: 'Annotation', data: FeatureData):
        samples = data.sample_channels(annotation.as_mask())
        return cls.fromArray5D(samples)

class Samples:
    def __init__(self, feature_samples:FeatureSamples, label_samples:LabelSamples):
        assert feature_samples.length == label_samples.length
        self.feature = feature_samples
        self.label = label_samples

    def concatenate(self, *others:List['Samples']):
        all_features = self.feature.concatenate(*[sample.feature for sample in others])
        all_labels = self.label.concatenate(*[sample.label for sample in others])
        return Samples(feature_samples=all_features, label_samples=all_labels)

class Annotation(ScalarImage):
    def __init__(self, arr:np.ndarray, axiskeys:str, data_source:DataSource, offset:Point5D=Point5D.zero()):
        super().__init__(arr, axiskeys)
        assert self.dtype == np.uint32

        if self.shape + offset > data_source.shape:
            raise AnnotationOutOfBounds(annotation=self, data_source=data_source, offset=offset)

        self.data_source = data_source
        self.bounding_box = self.shape.to_slice_5d()
        self.global_bounding_box = self.bounding_box.offset(offset).with_full_c()
        self.data_slice = DataSourceSlice.from_slice(data_source, self.global_bounding_box)
        self.offset = offset

        self._mask = None

    def as_mask(self):
        if self._mask is None:
            self._mask = super().as_mask()
        return self._mask

    @classmethod
    def from_png(cls, path:str, data_source:DataSource):
        data = np.asarray(PilImage.open(path)).astype(np.uint32)
        if len(data.shape) != 2:
            raise WrongShapeException(path, data)
        return cls(data, 'yx', data_source)

    def rebuild(self, arr:np.array, axiskeys:str, offset:Point5D=None) -> 'Array5D':
        return self.__class__(arr, axiskeys, data_source=self.data_source,
                              offset=self.offset if offset is None else offset)

    def cut(self, roi:Slice5D) -> 'Annotation':
        slices = roi.to_slices(self.axiskeys)
        return self.rebuild(self._data[slices], self.axiskeys, offset=roi.start + self.offset)

    def get_samples(self, feature_extractor:FeatureExtractor) -> Samples:
        all_label_samples = []
        all_feature_samples = []
        for global_tile in self.data_slice.get_tiles(): #tiling allows for caching of the features
            global_roi = global_tile.roi().clamped_with_slice(self.global_bounding_box)
            local_roi = global_roi.offset(- self.offset).with_full_c()
            feature_roi = global_roi.mod_tile(self.data_source.tile_shape)

            annotation_tile = self.cut(local_roi)
            feature_tile = feature_extractor.compute(global_tile).cut(feature_roi)

            label_samples = LabelSamples.create(annotation_tile)
            feature_samples = FeatureSamples.create(annotation_tile, feature_tile)
            all_label_samples.append(label_samples)
            all_feature_samples.append(feature_samples)
        return Samples(label_samples=all_label_samples[0].concatenate(*all_label_samples[1:]),
                       feature_samples=all_feature_samples[0].concatenate(*all_feature_samples[1:]))

    def __repr__(self):
        return f"<Annotation {self.shape}  for data_source: {self.data_source}>"
