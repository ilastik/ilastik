from abc import ABC, abstractmethod
from functools import lru_cache
from typing import List, Iterator

from PIL import Image as PilImage
import numpy as np

import enum
from enum import IntEnum

from ilastik.array5d import Array5D, Image, Point5D, Shape5D, Slice5D
from ilastik.utility import JsonSerializable

@enum.unique
class AddressMode(IntEnum):
    BLACK = 0
    MIRROR = enum.auto()
    WRAP = enum.auto()

class DataSource(Slice5D):
    @classmethod
    @abstractmethod
    def get_full_shape(cls, url:str) -> Shape5D:
        pass

    def __init__(self, url:str, *, t=slice(None), c=slice(None), x=slice(None), y=slice(None), z=slice(None)):
        self.url = url
        self.full_shape = self.get_full_shape(url)
        self.roi = Slice5D(t=t, c=c, x=x, y=y, z=z).defined_with(self.full_shape)
        super().__init__(**self.roi.to_dict())

    def __repr__(self):
        return super().__repr__() + f"({self.url.split('/')[-1]})"

    def rebuild(self, *, t=slice(None), c=slice(None), x=slice(None), y=slice(None), z=slice(None)) -> 'DataSource':
        return self.__class__(self.url, t=t, c=c, x=x, y=y, z=z)

    def __hash__(self):
        return hash((self.url, self.roi))

    def __eq__(self, other):
        if not super().__eq__(other):
            return False
        if isinstance(other, self.__class__):
            return self.url == other.url
        return True

    def full(self) -> 'DataSource':
        return self.__class__(self.url, **Slice5D.all().to_dict())

    @property
    @abstractmethod
    def dtype(self):
        pass

    @abstractmethod
    def get(self) -> Array5D:
        pass

    def contains(self, slc:Slice5D) -> bool:
        return self.roi.contains(slc.defined_with(self.full_shape))

    @property
    def tile_shape(self):
        """A sensible tile shape. Override this with your data chunk size"""
        return Shape5D(x=2048, y=2048, c=self.shape.c)

    def clamped(self, slc:Slice5D=None) -> 'DataSource':
        return super().clamped(slc or self.full())

    def retrieve(self, address_mode:AddressMode=AddressMode.BLACK) -> Array5D:
        # FIXME: Remove address_mode or implement all variations and make feature extractors
        # use te correct one
        out = Image.allocate(self, dtype=self.dtype, value=0)
        data_roi = self.clamped()
        for tile in data_roi.get_tiles():
            tile_data = tile.get()
            out.set(tile_data, autocrop=True)
        return out #TODO: make slice read-only

    def get_tiles(self, tile_shape:Shape5D=None):
        for tile in super().get_tiles(tile_shape or self.tile_shape):
            clamped_tile = tile.clamped(self.full())
            yield self.__class__(self.url, **clamped_tile.to_dict())

    def mod_tile(self, tile_shape:Shape5D=None) -> 'DataSource':
        return super().mod_tile(tile_shape or self.tile_shape)

    def __getstate__(self):
        return self.json_data

    def __setstate__(self, data:dict):
        self.__init__(data['url'], Slice5D.from_json(data['roi']))


class FlatDataSource(DataSource):
    """A naive implementation o DataSource that can read images using PIL"""

    @classmethod
    @lru_cache()
    def get_full_shape(cls, url:str) -> Shape5D:
        img = PilImage.open(url)
        return Shape5D(x=img.width, y=img.height, c=len(img.getbands()))

    @property
    def tile_shape(self):
        return Shape5D(x=200, y=200, c=self.shape.c)

    def __init__(self, url:str, *, t=slice(None), c=slice(None), x=slice(None), y=slice(None), z=slice(None)):
        raw_data = np.asarray(PilImage.open(url))
        axiskeys = 'yxc'[:len(raw_data.shape)]
        self._data = Image(raw_data, axiskeys=axiskeys)
        super().__init__(url, t=t, c=c, x=x, y=y, z=z)

    @property
    def dtype(self):
        return self._data.dtype

    def get(self) -> Image:
        return self._data.cut(self.roi, copy=True)
