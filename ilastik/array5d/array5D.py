import numpy as np
import vigra
from vigra import VigraArray, AxisInfo, AxisTags

from .point5D import Point5D, Roi5D, Shape5D

class Array5D(VigraArray):
    @classmethod
    def view5D(cls, arr:np.ndarray):
        missing_infos = [getattr(AxisInfo, tag) for tag in Point5D.LABELS if tag not in  arr.axistags]
        slices = [vigra.newaxis(info) for info in missing_infos]
        slices = tuple([...] + slices)

        return cls(arr[slices], dtype=arr.dtype)

    @property
    def shape5D(self):
        shape_dict = {key:value for key, value in zip(self.axiskeys, self.shape)}
        return Shape5D(**shape_dict)

    @property
    def axiskeys(self):
        return [tag.key for tag in self.axistags]

    def cut(self, roi:Roi5D):
        slices = roi.to_slices(self.axiskeys)
        return self[slices]

    def cut_axiswise(self, *, t=slice(None), x=slice(None), y=slice(None), z=slice(None), c=slice(None)):
        slice_dict = {'t':t, 'x':x, 'y':y, 'z':z, 'c':c}

        ordered_slices = tuple([slice_dict[key] for key in self.axiskeys])
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
