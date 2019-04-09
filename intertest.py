from collections import defaultdict

from ilastik.array5d import Image
from ilastik.feature_extractor import FeatureCollection
from ilastik.vigra_features import GaussianSmoothing, HessianOfGaussian


import vigra
import numpy as np

a = Image.open_image("/home/tomaz/ilastikTests/SampleData/c_cells/cropped/cropped1.png")

#import pydevd; pydevd.settrace()


#image_lists = {}
#computed_features = {}
#
#for feat_class in (HessianOfGaussian, GaussianSmoothing):
#    features = [feat_class(sigma=float(i)) for i in np.arange(1, 3, 0.1)]
#    computed_features[feat_class.__name__] = [f.compute(a) for f in features]



fc = FeatureCollection(GaussianSmoothing(sigma=1.5), HessianOfGaussian(sigma=1.2), GaussianSmoothing(sigma=1.7))
computed_feats = fc.compute(a)
