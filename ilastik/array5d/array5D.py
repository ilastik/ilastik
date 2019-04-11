from typing import Iterator

import numpy as np
from PIL import Image as PilImage
import vigra
from vigra import VigraArray, AxisInfo, AxisTags

from .point5D import Point5D, Slice5D, Shape5D

class Array5D:
    def __init__(self, arr:vigra.VigraArray, force_dtype=None):
        missing_infos = [getattr(AxisInfo, tag) for tag in Point5D.LABELS if tag not in  arr.axistags]
        slices = tuple([vigra.newaxis(info) for info in missing_infos] + [...])
        self._data = arr[slices]
        if force_dtype is not None and force_dtype != self._data.dtype:
            self._data = self._data.astype(force_dtype)

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.shape}>"

    @classmethod
    def allocate(cls, shape:Shape5D, dtype, axistags:str=Point5D.LABELS, value:int=None):
        #FIXME: maybe create a AxisTags5D class?
        assert sorted(axistags) == sorted(Point5D.LABELS)
        arr = np.random.rand(*shape.to_tuple(axistags)).astype(dtype)
        tagged = vigra.taggedView(arr, axistags=axistags)
        arr = cls(tagged)
        if value is not None:
            arr._data[...] = value
        return arr

    @classmethod
    def from_int(cls, value) -> 'Array5D':
        return cls.allocate(Shape5D(), dtype=np.uint8, value=value)

    @property
    def dtype(self):
        return self._data.dtype

    @property
    def axistags(self):
        return self._data.axistags

    @property
    def axiskeys(self):
        return [tag.key for tag in self.axistags]

    @property
    def squeezed_axistags(self):
        return self._data.squeeze().axistags

    @property
    def spatial_tags(self):
        return [tag for tag in self.squeezed_axistags if tag.isSpatial()]

    @property
    def is_video(self):
        return 't' in self.squeezed_axistags

    @property
    def is_volume(self):
        return len(self.spatial_tags) >= 3

    @property
    def is_flat(self):
        return len(self.spatial_tags) <= 2

    @property
    def is_scalar(self):
        return 'c' not in self.squeezed_axistags

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
                yield Image(slc._data)

    def raw(self):
        return self._data

    def cut_with(self, *, t=slice(None), c=slice(None), x=slice(None), y=slice(None), z=slice(None)):
        return self.cut(Slice5D(t=t, c=c, x=x, y=y, z=z))

    def cut(self, roi:Slice5D):
        slices = roi.to_slices(self.axiskeys)
        return self.__class__(self._data[slices])

    def set(self, value, *, t=slice(None), c=slice(None), x=slice(None), y=slice(None), z=slice(None)):
        #import pydevd; pydevd.settrace()
        slc = Slice5D(t=t, c=c, x=x, y=y, z=z)
        self.set_slice(value, slc=slc)

    def set_slice(self, value, *, slc:Slice5D):
        if isinstance(value, int):
            value = self.from_int(value)
        self.cut(slc)._data[...] = value._data

    def as_pil_images(self):
        return [img.as_pil_image() for img in self.imageIter()]

    def __eq__(self, other):
        if not isinstance(other, Array5D) or self.shape != other.shape:
            raise Exception(f"Comparing Array5D {self} with {other}")

        return np.all(self._data == other._data)

class Video3D(Array5D):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert self.is_video
        assert self.is_volume

    def frames(self):
        for frame in super().frames():
            yield Volume(frame._data)

class Volume(Array5D):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert not self.is_video
        assert self.is_volume

    def slices(self, key='z') -> Iterator['Image']:
        for slc in super().planes(key):
            yield Image(slc._data)

    def channels(self) -> Iterator['ScalarVolume']:
        for channel in super().channels():
            yield ScalarVolume(channel._data)

class ScalarVolume(Volume):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert self.is_scalar

    def planes(self, key='z') -> Iterator['ScalarImage']:
        for plane in super().planes(key):
            yield ScalarImage(plane._data)

class Video2D(Array5D):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert self.is_video
        assert self.is_flat

    def frames(self) -> Iterator['Image']:
        for frame in super().frames():
            yield Image(frame._data)

class Image(Array5D):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert self.is_flat
        assert not self.is_video

    @classmethod
    def open_image(cls, path:str):
        image_data = np.asarray(PilImage.open(path))
        return cls(vigra.Image(image_data), force_dtype=np.float32)

    def channels(self) -> Iterator['ScalarImage']:
        for channel in super().channels():
            yield ScalarImage(channel._data)

    def as_pil_image(self):
        return PilImage.fromarray(self._data.astype(np.uint8).squeeze())

class ScalarImage(Image):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert self.is_scalar

    def sample(self, data:Array5D):
        assert self.shape.with_coord(c=data.shape.c) == data.shape
        indices = tuple(zip(*np.nonzero(self._data)))
        samples_shape = Shape5D(x=len(indices), c=data.shape.c)
        samples = Array5D.allocate(samples_shape, data.dtype)

        for i, index in enumerate(indices):
            slc = Slice5D(**{k:v for k,v in zip(data.axiskeys, index)})
            slc  = slc.with_coord(c=slice(None))
            samples.set(data.cut(slc), x=i)
        return samples
