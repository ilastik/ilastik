import numpy as np

from ilastik.array5d import Array5D, Slice5D, Shape5D, ScalarImage, Line, ScalarLine


class Sampler(ScalarImage):
    class ClassList(ScalarLine):
        pass

    class Samples(Line):
        pass

    def sample(self, data:Array5D):
        #FIXME: maybe don't allow Classlist and Samples to be created empty?
        assert self.shape.with_coord(c=data.shape.c) == data.shape
        indices = tuple(zip(*np.nonzero(self._data)))
        classes = self.ClassList.allocate(Shape5D(x=len(indices), c=1), self.dtype)

        samples_shape = Shape5D(x=len(indices), c=data.shape.c)
        samples = self.Samples.allocate(samples_shape, data.dtype)

        for i, index in enumerate(indices):
            slc = Slice5D(**{k:v for k,v in zip(data.axiskeys, index)})
            slc  = slc.with_coord(c=slice(None))
            classes.set(self.cut(slc), x=i)
            samples.set(data.cut(slc), x=i)
        return samples, classes
