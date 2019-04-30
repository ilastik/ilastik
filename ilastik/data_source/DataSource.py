from abc import ABC, abstractmethod
from typing import List

from PIL import Image as PilImage
import numpy as np

import enum
from enum import Enum

from ilastik.array5d import Array5D, Point5D, Shape5D, Slice5D

@enum.unique
class DataSourceAddressMode(Enum):
    BLACK = 0

class DataSource(ABC):
    def __init__(self, mode=DataSourceAddressMode.BLACK):
        self.mode = mode

    @property
    @abstractmethod
    def shape(self) -> Shape5D:
        pass

    @property
    @abstractmethod
    def dtype(self):
        pass

    def retrieve(self, roi:Slice5D, halo:Point5D=Point5D.zero()) -> Array5D:
        roi = roi.defined_with(self.shape)
        assert self.shape.to_slice_5d().contains(roi)
        haloed_roi = roi.enlarged(halo)
        out = Array5D.allocate(haloed_roi.shape, dtype=self.dtype, value=0)

        data_roi = haloed_roi.clamped_with_slice(self.shape.to_slice_5d())
        data = self.do_retrieve(data_roi)

        offset = data_roi.start - haloed_roi.start
        out.set_slice(data, slc=data.shape.to_slice_5d().offset(offset))
        return out #TODO: make slice read-only

    @abstractmethod
    def do_retrieve(self, roi:Slice5D) -> Array5D:
        pass

class FlatDataSource(DataSource):
    def __init__(self, path:str):
        self.path = path
        raw_data = np.asarray(PilImage.open(path))
        axiskeys = 'yxc'[:len(raw_data.shape)]
        self._data = Array5D(raw_data, axiskeys=axiskeys)
        self.block_shape = Shape5D(**{k:v for k,v in zip(axiskeys, raw_data.shape)})

    @property
    def shape(self):
        return self._data.shape

    @property
    def dtype(self):
        return self._data.dtype

    def do_retrieve(self, roi:Slice5D):
        return self._data.cut(roi)
