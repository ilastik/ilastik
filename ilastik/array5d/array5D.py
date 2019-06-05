import itertools
from typing import Iterator, List, Tuple
import numpy as np
import os
from PIL import Image as PilImage
import uuid

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
    """A wrapper around np.ndarray with labeled axes. Enforces 5D, even if some
    dimensions are of size 1. Sliceable with Slice5D's"""
    DISPLAY_IMAGE_PREFIX='/tmp/junk_test_image_'
    os.system(f"rm -vf {DISPLAY_IMAGE_PREFIX}*")

    def __init__(self, arr:np.ndarray, axiskeys:str, location:Point5D=Point5D.zero()):
        assert len(arr.shape) == len(axiskeys)
        missing_keys = [key for key in Point5D.LABELS if key not in axiskeys]
        self._axiskeys = ''.join(missing_keys) + axiskeys
        assert sorted(self._axiskeys) == sorted(Point5D.LABELS)
        slices = tuple([np.newaxis for key  in missing_keys] + [...])
        self._data = arr[slices]
        self.location = location

    @classmethod
    def fromArray5D(cls, array:'Array5D'):
        return cls(array._data, array.axiskeys, array.location)

    @classmethod
    def from_file(cls, path:str, location:Point5D=Point5D.zero()):
        data = np.asarray(PilImage.open(path))
        return cls(data, 'yxc'[:len(data.shape)], location=location)

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.to_slice_5d()}>"

    @classmethod
    def allocate(cls, slc:Slice5D, dtype, axiskeys:str=Point5D.LABELS, value:int=None):
        assert sorted(axiskeys) == sorted(Point5D.LABELS)
        assert slc.is_defined() #FIXME: Create DefinedSlice class?
        arr = np.empty(slc.shape.to_tuple(axiskeys), dtype=dtype)
        arr = cls(arr, axiskeys, slc.start)
        if value is not None:
            arr._data[...] = value
        return arr

    @property
    def dtype(self):
        return self._data.dtype

    @property
    def axiskeys(self):
        return self._axiskeys

    @property
    def rawshape(self):
        return RawShape(self.shape, **{axis:idx for idx, axis in enumerate(self.axiskeys)})

    @property
    def squeezed_shape(self) -> RawShape:
        return self.rawshape

    @property
    def _shape(self) -> Tuple:
        return self._data.shape

    @property
    def shape(self) -> Shape5D:
        return Shape5D(**{key:value for key, value in zip(self.axiskeys, self._shape)})

    def iter_over(self, axis:str, step:int=1) -> Iterator['Array5D']:
        for slc in self.roi.iter_over(axis, step):
            yield self.cut(slc)

    def frames(self) -> Iterator['Array5D']:
        return self.iter_over('t')

    def planes(self, key='z') -> Iterator['Array5D']:
        return self.iter_over(key)

    def channels(self) -> Iterator['Array5D']:
        return self.iter_over('c')

    def channel_stacks(self, step):
        return self.iter_over('c', step=step)

    def images(self, through_axis='z') -> Iterator['Image']:
        for image_slice in self.roi.images(through_axis):
                yield Image.fromArray5D(self.cut(image_slice))

    def as_mask(self) -> 'Array5D':
        return Array5D(self._data > 0, axiskeys=self.axiskeys)

    def sample_channels(self, mask:'ScalarData') -> 'LinearData':
        assert self.shape.with_coord(c=1) == mask.shape
        sampling_axes = self.with_c_as_last_axis().axiskeys
        raw_mask = mask.raw(sampling_axes.replace('c', ''))
        return StaticLine(self.raw(sampling_axes)[raw_mask], StaticLine.DEFAULT_AXES)

    def setflags(self, *, write:bool):
        self._data.setflags(write=write)

    def normalized(self, iteration_axes:str='tzc') -> 'Array5D':
        normalized = self.allocate(self.shape, self.dtype, self.axiskeys)
        axis_ranges = tuple(range(self.shape[key]) for key in iteration_axes)
        for indices in itertools.product(*axis_ranges):
            slc = Slice5D(**{k:v for k,v in zip(iteration_axes, indices)})
            source_slice = self.cut(slc).raw(self.axiskeys)
            dest_slice = normalized.cut(slc).raw(self.axiskeys)
            data_range = np.amax(source_slice) - np.amin(source_slice)
            if data_range != 0:
                dest_slice[...] = (source_slice / data_range * np.iinfo(self.dtype).max).astype(self.dtype)
            else:
                dest_slice[...] = source_slice
        return normalized

    def rebuild(self, arr:np.array, axiskeys:str, location:Point5D=None) -> 'Array5D':
        location = self.location if location is None else location
        return self.__class__(arr, axiskeys, location)

    def moveaxis(self, source:str, destination:str):
        source_indices = tuple(self.axiskeys.index(k) for k in source)
        dest_indices = tuple(self.axiskeys.index(k) for k in destination)
        moved_arr = np.moveaxis(self._data, source=source_indices, destination=dest_indices)
        return self.rebuild(moved_arr, axiskeys=self.rawshape.swapped(source, destination).axiskeys)

    def raw(self, axiskeys:str) -> np.ndarray:
        """Returns a raw view of the underlying np.ndarray, containing only the axes
        identified by and ordered like 'axiskeys'"""

        assert all(self.shape[axis] == 1 for axis in Point5D.LABELS if axis not in axiskeys)
        swapped = self.reordered(axiskeys)

        slices = tuple((slice(None) if k in axiskeys else 0) for k in swapped.axiskeys)
        return np.asarray(swapped._data[slices])

    def linear_raw(self):
        """Returns a raw view with one spatial dimension and one channel dimension"""
        return self.raw('txyzc').reshape(self.shape.t * self.shape.volume, self.shape.c)

    def with_c_as_last_axis(self) -> 'Array5D':
        return self.moveaxis('c', self.axiskeys[-1])

    def reordered(self, axiskeys:str):
        source_indices = [self.axiskeys.index(x) for x in axiskeys]
        dest_indices = sorted(source_indices)

        new_axes = ''
        requested_axis = list(axiskeys)
        for axis in self.axiskeys:
            if axis in axiskeys:
                new_axes += requested_axis.pop(0)
            else:
                new_axes += axis

        moved_arr = np.moveaxis(self._data, source=source_indices, destination=dest_indices)

        return self.rebuild(moved_arr, axiskeys=new_axes)

    def local_cut(self, roi:Slice5D, *, copy:bool=False) -> 'Array5D':
        defined_roi = roi.defined_with(self.shape)
        slices = defined_roi.to_slices(self.axiskeys)
        if copy:
            cut_data = np.copy(self._data[slices])
        else:
            cut_data = self._data[slices]
        return self.rebuild(cut_data, self.axiskeys, location=self.location + defined_roi.start)

    def cut(self, roi:Slice5D, *, copy:bool=False) -> 'Array5D':
        return self.local_cut(roi.translated(-self.location), copy=copy) #TODO: define before translate?

    def clamped(self, roi:Slice5D) -> 'Array5D':
        return self.cut(self.roi.clamped(roi))

    def to_slice_5d(self):
        return self.shape.to_slice_5d().translated(self.location)

    @property
    def roi(self):
        return self.to_slice_5d()

    def set(self, value:'Array5D', autocrop:bool=False):
        if autocrop:
            value_slc = value.roi.clamped(self.roi)
            value = value.cut(value_slc)
        self.cut(value.roi).raw(Point5D.LABELS)[...] = value.raw(Point5D.LABELS)

    def as_pil_images(self):
        return [img.as_pil_image() for img in self.images()]

    def __eq__(self, other):
        if not isinstance(other, Array5D) or self.shape != other.shape:
            raise Exception(f"Comparing Array5D {self} with {other}")

        return np.all(self._data == other._data)

    def as_uint8(self, normalized=True):
        multi = 255 if normalized else 1
        return Array5D((self._data * multi).astype(np.uint8), axiskeys=self.axiskeys)

    def _show(self):
        path = f"{self.DISPLAY_IMAGE_PREFIX}_{uuid.uuid4()}.png"
        self.as_pil_images()[0].save(path)
        os.system(f"gimp {path}")

    def show_images(self):
        for img_idx, img in enumerate(self.images()):
            for channel_idx, channel in enumerate(img.channels()):
                channel._show()

    def show_channels(self):
        for img in self.images():
            for channel in img.channels():
                channel._show()


class StaticData(Array5D):
    """An Array5D with a single time frame"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert self.shape.is_static

    @property
    def squeezed_shape(self) -> RawShape:
        return super().squeezed_shape.to_static()

class ScalarData(Array5D):
    """An Array5D with a single channel"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert self.shape.is_scalar

    @property
    def squeezed_shape(self) -> RawShape:
        return super().squeezed_shape.to_scalar()

class FlatData(Array5D):
    """An Array5D with less than 3 spacial dimensions having a size > 1"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert self.shape.is_flat

    @property
    def squeezed_shape(self) -> RawShape:
        return super().squeezed_shape.to_planar()

class LinearData(Array5D):
    """An Array5D with at most 1 spacial dimension having size > 1"""

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
    """An Array5D representing a 2D image"""

    def channels(self) -> Iterator['ScalarImage']:
        for channel in super().channels():
            yield ScalarImage(channel._data, self.axiskeys)

    def as_pil_image(self):
        assert self.dtype == np.uint8
        raw_axes = 'yx' if self.shape.is_scalar else 'yxc'
        return PilImage.fromarray(self.raw(raw_axes))

class ScalarImage(Image, ScalarData):
    pass

class ScalarLine(LinearData, ScalarData):
    pass

class StaticLine(StaticData, LinearData):
    DEFAULT_AXES = 'xc'
    def concatenate(self, *others: List['LinearData']) -> 'LinearData':
        axes = self.squeezed_shape.axiskeys
        concat_axis = self.squeezed_shape.to_scalar().axiskeys
        raw_all = [self.raw(axes)] + [o.raw(axes) for o in others]
        data = np.concatenate(raw_all, axis=axes.index(concat_axis))
        return self.rebuild(data, axes)
