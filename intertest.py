from ilastik.array5d import Array5D, Slice5D, Point5D, Shape5D
from ilastik.feature_extractor import GaussianSmoothing, HessianOfGaussian


import vigra
import numpy as np

a = Array5D.open_image("/home/tomaz/ilastikTests/SampleData/c_cells/cropped/cropped1.png")

#import pydevd; pydevd.settrace()


image_lists = {}

for feat in (GaussianSmoothing, HessianOfGaussian):
    features = [GaussianSmoothing(sigma=float(i)) for i in np.arange(1, 3, 0.1)]
    image_lists[feat.__name__] =[f.compute(a).as_images()[0] for f in features]
