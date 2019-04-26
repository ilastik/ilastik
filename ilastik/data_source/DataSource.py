from abc import ABC, abstractmethod
from typing import List

from PIL import Image as PilImage
import numpy as np

from ilastik.array5d import Array5D, Point5D, Shape5D, Slice5D

class DataSource(ABC):
    @property
    @abstractmethod
    def shape(self) -> Shape5D:
        pass

    @abstractmethod
    def retrieve(self, roi:Shape5D) -> Array5D:
        pass

class TiledDataSouce(DataSource):
    def fetch_tile(self, roi:Slice5D):
        pass

    def get_data(self, roi:Shape5D):
        for tile_slice in roi.get_tiles(self.block_shape):
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

    def retrieve(self, roi:Shape5D):
        return self._data.cut(roi) #TODO: make slice read-only

