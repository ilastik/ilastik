from typing import Tuple

import numpy as np

from ilastik.array5d.array5D import Array5D, Slice5D, Shape5D, Image, ScalarImage, LinearData, StaticData
from ilastik.features.feature_extractor import FeatureCollection, FeatureData


class Labels(ScalarImage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert self.dtype == np.uint8

    class ClassList(LinearData, StaticData):
        #FIXME: maybe this should only be spawnable as uint32
        def raw(self, axiskeys:str=None):
            axiskeys = axiskeys or self.with_c_as_last_axis().squeezed_shape.axiskeys
            return super().raw(axiskeys)

    def sample(self, data:Array5D) -> Tuple[FeatureData, ClassList]:
        #FIXME: maybe don't allow Classlist and Samples to be created empty?
        assert self.shape.with_coord(c=data.shape.c) == data.shape
        indices = tuple(zip(*np.nonzero(self._data)))

        classes = self.ClassList.allocate(Shape5D(x=len(indices), c=1), np.uint32)
        samples = FeatureData.allocate(classes.shape.with_coord(c=data.shape.c), data.dtype)

        #FIXME: do this all inside numpy
        for i, index in enumerate(indices):
            slc = Slice5D(**{k:v for k,v in zip(self.axiskeys, index)})
            slc  = slc.with_coord(c=slice(None))
            classes.set(self.cut(slc), x=i)
            samples.set(data.cut(slc), x=i)
        return samples, classes
