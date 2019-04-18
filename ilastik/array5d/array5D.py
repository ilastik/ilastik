from typing import Iterator
from collections import OrderedDict

import numpy as np
from PIL import Image as PilImage
import vigra
from vigra import VigraArray, AxisInfo, AxisTags

from .point5D import Point5D, Slice5D, Shape5D

class RawShape:
    def __init__(self, shape:Shape5D, *, t:int=None, c:int=None, x:int=None, y:int=None, z:int=None):
        self.index_map = {axis:idx for axis, idx in zip('tcxyz', (t,c,x,y,z)) if idx is not None}
        self.shape = shape

    @property
    def axiskeys(self):
        pairs = sorted(self.index_map.keys(), key=lambda axis:self.index_map[axis])
        return ''.join(pairs)

    def index(self, axis:str):
        return self.index_map[axis]

    @property
    def spatials(self):
        return {k:v for k,v in self.index_map.items() if k in 'xyz'}

    def drop(self, axis:str) -> 'RawShape':
        leftover_keys = {k:v for k,v in self.index_map.items() if k not in axis}
        return RawShape(self.shape, **leftover_keys)

    def drop_one_spatial(self):
        for axis in 'zyx':
            if axis in self.index_map and self.shape[axis] == 1:
                return self.drop(axis)

    def to_n_spacials(self, n:int):
        out = self
        while len(out.spatials) > n:
            out = out.drop_one_spatial()
        return out

    def to_planar(self):
        return self.to_n_spacials(2)

    def to_linear(self):
        return self.to_n_spacials(1)

    def to_scalar(self):
        return self.drop('c')

    def to_static(self):
        return self.drop('t')

    def to_shape_dict(self):
        return {axis:self.shape[axis] for axis in self.axiskeys}

    def to_index_tuple(self):
        return tuple(self.index_map.values())

    def to_index_discard_tuple(self):
        return tuple(i for i in range(5) if i not in self.to_index_tuple())

    def to_shape_tuple(self, *, with_t=None, with_c=None, with_x=None, with_y=None, with_z=None):
        overrides = {'t': with_t, 'c': with_c, 'x': with_x, 'y': with_y, 'z': with_z}
        out = {k:v for k,v in overrides.items() if v is not None}
        assert all(k in self.axiskeys for k in overrides.keys())

        out = {**self.to_shape_dict(), **out}
        return tuple(out[axis] for axis in self.axiskeys)

    def swapped(self, source:str, destination:str):
        d = dict(self.index_map)
        for source_key, destination_key in zip(source, destination):
            d[source_key], d[destination_key] = self.index_map[destination_key], self.index_map[source_key]
        return RawShape(self.shape, **d)

class Array5D:
    def __init__(self, arr:np.ndarray, axiskeys:str):
        arr = vigra.taggedView(arr, axistags=axiskeys)
        missing_infos = [getattr(AxisInfo, tag) for tag in Point5D.LABELS if tag not in  arr.axistags]
        slices = tuple([vigra.newaxis(info) for info in missing_infos] + [...])
        self._data = arr[slices]

    @classmethod
    def fromArray5D(cls, array):
        return cls(array._data, array.axiskeys)

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.shape}>"

    @classmethod
    def allocate(cls, shape:Shape5D, dtype, axiskeys:str=Point5D.LABELS, value:int=None):
        assert sorted(axiskeys) == sorted(Point5D.LABELS)
        arr = np.empty(shape.to_tuple(axiskeys), dtype=dtype)
        arr = cls(arr, axiskeys)
        if value is not None:
            arr._data[...] = value
        return arr

    @classmethod
    def from_int(cls, value) -> 'Array5D':
        return cls.allocate(Shape5D(), dtype=self.dtype, value=value)

    @property
    def dtype(self):
        return self._data.dtype

    @property
    def axistags(self):
        return self._data.axistags

    @property
    def axiskeys(self):
        return ''.join(tag.key for tag in self.axistags)

    @property
    def rawshape(self):
        return RawShape(self.shape, **{axis:idx for idx, axis in enumerate(self.axiskeys)})

    @property
    def squeezed_shape(self) -> RawShape:
        return self.rawshape

    @property
    def _shape(self):
        return self._data.shape

    @property
    def shape(self) -> Shape5D:
        return Shape5D(**{key:value for key, value in zip(self.axiskeys, self._shape)})

    def iter_over(self, axis:str, step:int=1) -> Iterator['Array5D']:
        assert self.shape[axis] % step == 0
        for axis_value in range(0, self.shape[axis], step):
            yield self.cut_with(**{axis:slice(axis_value, axis_value + step)})

    def frames(self) -> Iterator['Array5D']:
        return self.iter_over('t')

    def planes(self, key='z') -> Iterator['Array5D']:
        return self.iter_over(key)

    def channels(self) -> Iterator['Array5D']:
        return self.iter_over('c')

    def channel_stacks(self, step):
        return self.iter_over('c', step=step)

    def images(self, through_axis='z') -> Iterator['Image']:
        for frame in self.frames():
            for slc in frame.planes(through_axis):
                yield Image(slc._data, self.axiskeys)

    def moveaxis(self, source:str, destination:str):
        source_indices = tuple(self.axiskeys.index(k) for k in source)
        dest_indices = tuple(self.axiskeys.index(k) for k in destination)
        moved_arr = np.moveaxis(self._data, source=source_indices, destination=dest_indices)
        return self.__class__(moved_arr, axiskeys=self.rawshape.swapped(source, destination).axiskeys)

    def raw(self, axiskeys:str):
        #import pydevd; pydevd.settrace()
        swapped = self.moveaxis(self.squeezed_shape.axiskeys, axiskeys)
        raw_shape = swapped.squeezed_shape
        squeezed = np.asarray(swapped._data).squeeze(axis=raw_shape.to_index_discard_tuple())
        return vigra.taggedView(squeezed, axistags=raw_shape.axiskeys)

    def with_c_as_last_axis(self) -> 'Array5D':
        return self.moveaxis('c', self.axiskeys[-1])

    def cut_with(self, *, t=slice(None), c=slice(None), x=slice(None), y=slice(None), z=slice(None)):
        return self.cut(Slice5D(t=t, c=c, x=x, y=y, z=z))

    def cut(self, roi:Slice5D):
        slices = roi.to_slices(self.axiskeys)
        return self.__class__(self._data[slices], self.axiskeys)

    def set(self, value, *, t=slice(None), c=slice(None), x=slice(None), y=slice(None), z=slice(None)):
        slc = Slice5D(t=t, c=c, x=x, y=y, z=z)
        self.set_slice(value, slc=slc)

    def set_slice(self, value, *, slc:Slice5D):
        if isinstance(value, int):
            value = self.from_int(value)
        self.cut(slc)._data[...] = value._data

    def as_pil_images(self):
        return [img.as_pil_image() for img in self.images()]

    def __eq__(self, other):
        if not isinstance(other, Array5D) or self.shape != other.shape:
            raise Exception(f"Comparing Array5D {self} with {other}")

        return np.all(self._data == other._data)

class StaticData(Array5D):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert self.shape.is_static

    @property
    def squeezed_shape(self) -> RawShape:
        return super().squeezed_shape.to_static()

class ScalarData(Array5D):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert self.shape.is_scalar

    @property
    def squeezed_shape(self) -> RawShape:
        return super().squeezed_shape.to_scalar()

class FlatData(Array5D):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert self.shape.is_flat

    @property
    def squeezed_shape(self) -> RawShape:
        return super().squeezed_shape.to_planar()

class LinearData(Array5D):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert self.shape.is_line

    @property
    def length(self):
        return self.shape.volume

    @property
    def squeezed_shape(self) -> RawShape:
        return super().squeezed_shape.to_linear()

class Image(StaticData, FlatData):
    def channels(self) -> Iterator['ScalarImage']:
        for channel in super().channels():
            yield ScalarImage(channel._data, self.axiskeys)

    def as_pil_image(self):
        assert self.dtype == np.uint8
        raw_axis = 'yx' if self.shape.is_scalar else 'yxc'
        return PilImage.fromarray(self.raw(raw_axis))

class ScalarImage(Image, ScalarData):
    pass


class ScalarLine(LinearData, ScalarData):
    pass

class StaticLine(StaticData, LinearData):
    pass
