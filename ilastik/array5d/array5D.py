import numpy as np
import vigra
from vigra import VigraArray, AxisInfo, AxisTags

from .point5D import Point5D, Roi5D, Shape5D

class Array5D(VigraArray):
    @classmethod
    def view5D(cls, arr:vigra.VigraArray):
        missing_infos = [getattr(AxisInfo, tag) for tag in Point5D.LABELS if tag not in  arr.axistags]
        slices = [vigra.newaxis(info) for info in missing_infos]
        slices = tuple([...] + slices)

        return cls(arr[slices], dtype=arr.dtype)

    @classmethod
    def allocate(cls, shape:Shape5D, axistags:str=None):
        axistags = axistags or Point5D.LABELS
        #FIXME: maybe create a AxisTags5D class?
        assert len(axistags) == len(Point5D.LABELS)
        arr = np.empty(shape.to_tuple(axistags))
        tagged = vigra.taggedView(arr, axistags=axistags)
        return cls.view5D(tagged)

    @property
    def shape5D(self):
        shape_dict = {key:value for key, value in zip(self.axiskeys, self.shape)}
        return Shape5D(**shape_dict)

    def _create_slicing(self, *, t=slice(None), c=slice(None), x=slice(None), y=slice(None), z=slice(None)):
        slice_dict = {'t':t, 'x':x, 'y':y, 'z':z, 'c':c}
        ordered_slices = tuple([slice_dict[key] for key in self.axiskeys])
        return ordered_slices

    def assign_to_z_plane(self, t:int=0, z:int, data):
        import pydevd; pydevd.settrace()
        slices = self._create_slicing(t=t, z=z)
        self[slices] = data

    def view_z_plane(self, t:int=0, z:int):
        slicing = self._create_slicing(t=slice(t, t+1), z=slice(z, z+1))
        return self[slicing]

    @property
    def axiskeys(self):
        return [tag.key for tag in self.axistags]

    def cut(self, roi:Roi5D):
        slices = roi.to_slices(self.axiskeys)
        return self[slices]

    def cut_axiswise(self, *, t=slice(None), x=slice(None), y=slice(None), z=slice(None), c=slice(None)):
       return self[ordered_slices]

    @classmethod
    def open_image(cls, path):
        from PIL import Image
        image_data = np.asarray(Image.open(path))
        return cls.view5D(vigra.taggedView(image_data))

    def as_image_data(self):
        return self.cut_axiswise(x=slice(None), y=slice(None), c=slice(None)).squeeze()

    def as_image(self):
        from PIL import Image
        return Image.fromarray(self.as_image_data())
