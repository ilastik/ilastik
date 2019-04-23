from abc import ABC, abstractmethod
from typing import List, Iterator, Tuple

import vigra.filters
import numpy as np

from ilastik.array5d import Slice5D, Point5D, Shape5D
from ilastik.array5d import Array5D, Image, ScalarImage, StaticLine
from ilastik.features.feature_extractor import FeatureExtractor, FeatureData

class AnnotationOutOfBounds(Exception):
    def __init__(self, annotation:'Annotation', raw_data:Array5D, offset:Point5D):
        super().__init__(f"Annotation {annotation} offset by {offset} exceeds bounds of raw_data {raw_data}")

class Labels(StaticLine):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert self.dtype == np.uint32

    def raw(self, axiskeys:str=None):
        axiskeys = axiskeys or self.with_c_as_last_axis().squeezed_shape.axiskeys
        return super().raw(axiskeys)

class Samples:
    def __init__(self, features:FeatureData, labels:Labels):
        assert features.shape.is_line and features.shape.volume == labels.length
        self.features = features
        self.labels = labels

class Annotation(ScalarImage):
    def __init__(self, arr:np.ndarray, axiskeys:str, raw_data:Array5D, offset:Point5D=Point5D.zero()):
        super().__init__(arr, axiskeys)
        assert self.dtype == np.uint32

        if self.shape + offset > raw_data.shape:
            raise AnnotationOutOfBounds(annotation=self, raw_data=raw_data, offset=offset)

        self.raw_data = raw_data
        self.offset = offset
        self.sampling_axes = self.raw_data.with_c_as_last_axis().axiskeys
        self.out_axes = 'xc'

        self._mask = None
        self._labels = None

    def rebuild(self, arr:np.array, axiskeys:str, offset:Point5D=None) -> 'Array5D':
        return self.__class__(arr, axiskeys, raw_data=self.raw_data,
                              offset=self.offset if offset is None else offset)

    def cut(self, roi:Slice5D) -> 'Annotation':
        slices = roi.to_slices(self.axiskeys)
        return self.rebuild(self._data[slices], self.axiskeys, offset=roi.start + self.offset)

    @property
    def mask(self):
        if self._mask is not None:
            return self._mask
        mask_axes = self.sampling_axes.replace('c', '')
        self._mask = self.raw(mask_axes) > 0
        return self._mask

    @property
    def labels(self):
        if self._labels is not None:
            return self._labels
        self._labels = Labels(self.raw(self.sampling_axes)[self.mask], self.out_axes)
        return self._labels

    def get_samples(self, feature_extractor:FeatureExtractor) -> Samples:
        roi = self.shape.to_slice_5d().offset(self.offset)
        roi = roi.with_coord(c=slice(0, self.raw_data.shape.c))
        features = feature_extractor.compute(self.raw_data.cut(roi)) #TODO:roi + halo

        feature_data = features.raw(self.sampling_axes)[self.mask]

        return Samples(features=FeatureData(feature_data, self.out_axes),
                       labels=self.labels)

    def __repr__(self):
        return f"<Annotation {self.shape}  for raw_data: {self.raw_data}>"
