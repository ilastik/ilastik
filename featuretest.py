import pytest
import numpy as np


from ndstructs import Array5D, Slice5D
from ndstructs.datasource import ArrayDataSource
from ilastik.features.fastfilters import GaussianSmoothing
import fastfilters

data = Array5D.from_file("/home/tomaz/SampleData/c_cells/cropped/cropped1.png")
r_channel = data.cut(Slice5D(c=1))

features = fastfilters.gaussianSmoothing(r_channel.raw("yx").astype(np.float32), sigma=1.2)


#datasource = ArrayDataSource(data=data)
#extractor = GaussianSmoothing(sigma=1.2)
#features = extractor.compute(datasource)
