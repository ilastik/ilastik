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
    def allocate(cls, shape:Shape5D, dtype, axistags:str=Point5D.LABELS):
        #FIXME: maybe create a AxisTags5D class?
        assert len(axistags) == len(Point5D.LABELS)
        arr = np.empty(shape.to_tuple(axistags), dtype=dtype)
        tagged = vigra.taggedView(arr, axistags=axistags)
        return cls(tagged)

    @property
    def dtype(self):
        return self._data.dtype

    @property
    def axistags(self):
        return self._data.axistags

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
    def axiskeys(self):
        return [tag.key for tag in self.axistags]

    @property
    def _shape(self):
        return self._data.shape

    @property
    def shape(self) -> Shape5D:
        return Shape5D(**{key:value for key, value in zip(self.axiskeys, self._shape)})

    def timeIter(self):
        for timepoint in self._data.timeIter():
            yield Array5D(timepoint)

    def sliceIter(self, key='z'):
        for slc in self._data.sliceIter(key):
            yield Array5D(slc)

    def channelIter(self):
        for channel in self._data.channelIter():
            yield self.__class__(channel)

    def imageIter(self, through_axis='z'):
        for volume in self.timeIter():
            for z_slice in volume.sliceIter(through_axis):
                yield Image(z_slice._data)

    def raw(self):
        return self._data

    def cut_with(self, *, t=slice(None), c=slice(None), x=slice(None), y=slice(None), z=slice(None)):
        return self.cut(Slice5D(t=t, c=c, x=x, y=y, z=z))

    def cut(self, roi:Slice5D):
        slices = roi.to_slices(self.axiskeys)
        return self.__class__(self._data[slices])

    def as_pil_images(self):
        return [img.as_pil_image() for img in self.imageIter()]

class Video3D(Array5D):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert self.is_video
        assert self.is_volume

    def timeIter(self):
        for tp in self._data.timeIter():
            yield Volume(self._data)

class Volume(Array5D):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert not self.is_video
        assert self.is_volume

    def sliceIter(self, key='z'):
        for slc in super().sliceIter(key):
            yield Image(slc._data)

    def channelIter(self):
        for channel in super().channelIter():
            yield ScalarVolume(channel._data)

class ScalarVolume(Volume):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert self.is_scalar

    def sliceIter(self, key='z'):
        for slc in super().sliceIter(key):
            yield ScalarImage(slc._data)

class Video2D(Array5D):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert self.is_video
        assert self.is_flat

    def timeIter(self):
        for frame in super().timeIter():
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

    def channelIter(self):
        for channel in self._data.channelIter():
            yield ScalarImage(channel)

    def as_pil_image(self):
        return PilImage.fromarray(self._data.astype(np.uint8).squeeze())

class ScalarImage(Image):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert self.is_scalar
