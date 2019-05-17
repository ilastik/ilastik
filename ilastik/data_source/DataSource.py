from abc import ABC, abstractmethod
from typing import List, Iterator

from PIL import Image as PilImage
import numpy as np

import enum
from enum import Enum

from ilastik.array5d import Array5D, Point5D, Shape5D, Slice5D
from ilastik.utility import JsonSerializable

@enum.unique
class DataSourceAddressMode(Enum):
    BLACK = 0

class DataSource(JsonSerializable):
    def __init__(self, url:str):
        self.url = url

    def __hash__(self): #TODO: maybe include shape/tile_shape?
        return hash(self.url)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.url == other.url and self.tile_shape == other.tile_shape

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.shape} from {self.url}>"

    def cut_with(self, *, t=slice(None), c=slice(None), x=slice(None), y=slice(None), z=slice(None)) -> 'DataSourceSlice':
        return self.cut(Slice5D(t=t, c=c, x=x, y=y, z=z))

    def cut(self, slc:Slice5D) -> 'DataSourceSlice':
        return DataSourceSlice.from_slice(self, slc.defined_with(self.shape))

    def all(self) -> 'DataSourceSlice':
        return self.cut(self.shape.to_slice_5d())

    @property
    def tile_shape(self):
        """A sensible tile shape. Override this with your data chunk size"""
        return Shape5D(x=2048, y=2048, c=self.shape.c)

    @property
    @abstractmethod
    def shape(self) -> Shape5D:
        pass

    @property
    @abstractmethod
    def dtype(self):
        pass

    def contains(self, slc:Slice5D) -> bool:
        return self.shape.to_slice_5d().contains(slc.defined_with(self.shape))

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

    def json_serialize(self):
        return {'url': self.url,
                'shape': self.shape}

class DataSourceSlice(Slice5D):
    """A Slice5D tied to a DataSource"""

    def __init__(self, data_source:DataSource, *, t=slice(None), c=slice(None), x=slice(None), y=slice(None), z=slice(None)):
        super().__init__(t=t, c=c, x=x, y=y, z=z)
        self.data_source = data_source

    def rebuild(self, *, t=slice(None), c=slice(None), x=slice(None), y=slice(None), z=slice(None)):
        return self.__class__(self.data_source, t=t, c=c, x=x, y=y, z=z)

    def __hash__(self):
        return hash((super().__hash__(), self.data_source))

    def __eq__(self, other):
        if not isinstance(other, DataSourceSlice):
            return False
        return super().__eq__(other) and other.data_source == self.data_source

    @classmethod
    def from_slice(cls, data_source:DataSource, slc:Slice5D):
        return cls(data_source, **slc.to_dict())

    def retrieve(self, halo:Point5D=Point5D.zero()):
        return self.data_source.retrieve(self, halo)

    def get_tiles(self, tile_shape:Shape5D = None):
        for tile in super().get_tiles(tile_shape or self.data_source.tile_shape):
            yield tile.clamped_with_slice(self.data_source.shape.to_slice_5d())

    def mod_tile(self, tile_shape:Shape5D=None) -> 'DataSourceSlice':
        return super().mod_tile(tile_shape or self.data_source.tile_shape)

class FlatDataSource(DataSource):
    def __init__(self, url:str):
        super().__init__(url)
        raw_data = np.asarray(PilImage.open(url))
        axiskeys = 'yxc'[:len(raw_data.shape)]
        self._data = Array5D(raw_data, axiskeys=axiskeys)

    @property
    def shape(self):
        return self._data.shape

    @property
    def dtype(self):
        return self._data.dtype

    def do_retrieve(self, roi:Slice5D):
        return self._data.cut(roi)
