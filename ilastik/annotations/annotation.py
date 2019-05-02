from abc import ABC, abstractmethod
from typing import List, Iterator, Tuple

import vigra.filters
import numpy as np

from ilastik.array5d import Slice5D, Point5D, Shape5D
from ilastik.array5d import Array5D, Image, ScalarImage, StaticLine
from ilastik.features.feature_extractor import FeatureExtractor, FeatureData
from ilastik.data_source import DataSource, DataSpec
from PIL import Image as PilImage

class AnnotationOutOfBounds(Exception):
    def __init__(self, annotation:'Annotation', data_source:DataSource, offset:Point5D):
        super().__init__(f"Annotation {annotation} offset by {offset} exceeds bounds of data_source {data_source}")

class WrongShapeException(Exception):
    def __init__(self, path:str, data:np.ndarray):
        super().__init__(f"Annotations from {path} have bad shape: {data.shape}")

class Labels(StaticLine):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert self.dtype == np.uint32

class Samples:
    def __init__(self, features:FeatureData, labels:Labels):
        assert features.shape.is_line and features.shape.volume == labels.length
        self.features = features
        self.labels = labels

class Annotation(ScalarImage):
    def __init__(self, arr:np.ndarray, axiskeys:str, data_source:DataSource, offset:Point5D=Point5D.zero()):
        super().__init__(arr, axiskeys)
        assert self.dtype == np.uint32

        if self.shape + offset > data_source.shape:
            raise AnnotationOutOfBounds(annotation=self, data_source=data_source, offset=offset)

        self.data_source = data_source
        self.offset = offset
        self.out_axes = 'xc'

        self._mask = None
        self._labels = None

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
        roi = self.shape.to_slice_5d().offset(self.offset)
        roi = roi.with_coord(c=slice(0, self.data_source.shape.c))
        spec = DataSpec.from_slice(self.data_source, roi)
        features = feature_extractor.compute(spec)

        sampling_axes = features.with_c_as_last_axis().axiskeys

        mask = self.raw(sampling_axes.replace('c', '')) > 0

        labels_data = self.raw(sampling_axes)[mask]
        feature_data = features.raw(sampling_axes)[mask]

        return Samples(features=FeatureData(feature_data, self.out_axes),
                       labels=Labels(labels_data, self.out_axes))

    def __repr__(self):
        return f"<Annotation {self.shape}  for data_source: {self.data_source}>"
