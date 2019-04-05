import numpy as np
import vigra
from vigra import VigraArray, AxisInfo, AxisTags

from .point5D import Point5D, Slice5D, Shape5D

class Array5D:
    @classmethod
    def from_flat_image(cls, arr:np.ndarray):
        return cls(vigra.Image(arr, dtype=arr.dtype))

    def __init__(self, arr:vigra.VigraArray):
        missing_infos = [getattr(AxisInfo, tag) for tag in Point5D.LABELS if tag not in  arr.axistags]
        slices = tuple([vigra.newaxis(info) for info in missing_infos] + [...])
        self._data = arr[slices]

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.tagged_shape}>"

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
    def axiskeys(self):
        return [tag.key for tag in self.axistags]

    @property
    def shape(self):
        return self._data.shape

    @property
    def tagged_shape(self):
        return {key:value for key, value in zip(self.axiskeys, self.shape)}

    @property
    def shape_5d(self):
        return Shape5D(**self.tagged_shape)

    def _create_slicing(self, *, t=slice(None), c=slice(None), x=slice(None), y=slice(None), z=slice(None)):
        slice_dict = {'t':t, 'x':x, 'y':y, 'z':z, 'c':c}

        ordered_slices = []
        for key in self.axiskeys:
            slc = slice_dict[key]
            if isinstance(slc, int):
                slc = slice(slc, slc+1)
            ordered_slices.append(slc)

        return tuple(ordered_slices)

    def timeIter(self):
        for timepoint in self._data.timeIter():
            yield self.__class__(timepoint)

    def sliceIter(self, key='z'):
        for slc in self._data.sliceIter(key):
            yield self.__class__(slc)

    def as_xyc(self) -> np.ndarray:
        assert self.shape_5d.t == 1 and self.shape_5d.z == 1
        return self._data.squeeze()

    def cut(self, roi:Slice5D):
        slices = roi.to_slices(self.axiskeys)
        return self.__class__(self._data[slices])

    @classmethod
    def open_image(cls, path):
        from PIL import Image
        image_data = np.asarray(Image.open(path))
        return cls.from_flat_image(image_data)

    def as_images(self):
        from PIL import Image
        return [Image.fromarray(tp.as_xyc()) for tp in self.timeIter()]

class ImageXYC:
    def __init__(self, arr:np.array):
        assert(2 <= len(arr.shape) <= 3)
        self._data = vigra.Image(arr, dtype=arr.dtype)

    

