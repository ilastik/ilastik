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

class ClassList(StaticLine):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert self.dtype == np.uint32

    def raw(self, axiskeys:str=None):
        axiskeys = axiskeys or self.with_c_as_last_axis().squeezed_shape.axiskeys
        return super().raw(axiskeys)

class Annotation(ScalarImage):
    def __init__(self, arr:np.ndarray, axiskeys:str, raw_data:Array5D, offset:Point5D=Point5D.zero()):
        super().__init__(arr, axiskeys)
        assert self.dtype == np.uint32

        if self.shape + offset > raw_data.shape:
            raise AnnotationOutOfBounds(annotation=self, raw_data=raw_data, offset=offset)

        self.raw_data = raw_data
        self.offset = offset
        self._samples = None
        self._classes = None

    def cut(self, roi:Slice5D):
        slices = roi.to_slices(self.axiskeys)
        return self.__class__(self._data[slices], self.axiskeys,
                              raw_data=self.raw_data, offset=roi.start + self.offset)

    def get_samples(self, feature_extractor:FeatureExtractor) -> Tuple[FeatureData, ClassList]:
        if self._samples is not None:
            return self._samples, self._classes
        roi = self.shape.to_slice_5d().offset(self.offset)
        roi = roi.with_coord(c=slice(0, self.raw_data.shape.c))
        features = feature_extractor.compute(self.raw_data.cut(roi)) #TODO:roi + halo

        indices = tuple(zip(*np.nonzero(self._data)))

        classes = StaticLine.allocate(Shape5D(x=len(indices), c=1), np.uint32)
        samples = FeatureData.allocate(classes.shape.with_coord(c=features.shape.c), features.dtype)

        #FIXME: do this all inside numpy
        for i, index in enumerate(indices):
            slc = Slice5D(**{k:v for k,v in zip(self.axiskeys, index)})
            slc  = slc.with_coord(c=slice(None))
            classes.set(self.cut(slc), x=i)
            samples.set(features.cut(slc), x=i)

        self._samples = samples
        self._classes = ClassList.fromArray5D(classes)

        return self._samples, self._classes

    def __repr__(self):
        return f"<Annotaion {self.shape}  for raw_data: {self.raw_data}>"
