from collections import defaultdict

from ilastik.array5d import Image
from ilastik.features.feature_extractor import FeatureCollection
from ilastik.features.vigra_features import GaussianSmoothing, HessianOfGaussian


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
assert computed_feats.cut_with(c=slice(0,1)) == fc.features[0].compute(a.cut_with(c=0))
assert computed_feats.cut_with(c=slice(1,4)) == fc.features[1].compute(a.cut_with(c=0))
assert computed_feats.cut_with(c=slice(4,5)) == fc.features[2].compute(a.cut_with(c=0))

assert computed_feats.cut_with(c=slice(5,6)) == fc.features[0].compute(a.cut_with(c=1))
assert computed_feats.cut_with(c=slice(6,9)) == fc.features[1].compute(a.cut_with(c=1))
assert computed_feats.cut_with(c=slice(9,10)) == fc.features[2].compute(a.cut_with(c=1))

assert computed_feats.cut_with(c=slice(10,11)) == fc.features[0].compute(a.cut_with(c=2))
assert computed_feats.cut_with(c=slice(11,14)) == fc.features[1].compute(a.cut_with(c=2))
assert computed_feats.cut_with(c=slice(14,15)) == fc.features[2].compute(a.cut_with(c=2))

