from collections import defaultdict

from ilastik.array5d import Image, ScalarImage
from ilastik.array5d import Point5D, Slice5D, Shape5D
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


labels = ScalarImage.allocate(Shape5D(x=10, y=10), dtype=np.uint8, value=0)
fake_features = Image.allocate(Shape5D(x=10, y=10, c=3), dtype=np.uint8, value=0)

labels.set(123, x=1, y=1)
labels.set(100, x=2, y=2)
labels.set(23, x=3, y=3)

fake_features.set(5, x=1, y=1, c=0)
fake_features.set(6, x=1, y=1, c=1)
fake_features.set(7, x=1, y=1, c=2)

fake_features.set(15, x=2, y=2, c=0)
fake_features.set(16, x=2, y=2, c=1)
fake_features.set(17, x=2, y=2, c=2)

fake_features.set(105, x=3, y=3, c=0)
fake_features.set(106, x=3, y=3, c=1)
fake_features.set(107, x=3, y=3, c=2)

samps = labels.sample(fake_features)
assert all(samps.cut_with(x=0)._data.squeeze() == np.asarray((5,6,7)))
assert all(samps.cut_with(x=1)._data.squeeze() == np.asarray((15,16,17)))
assert all(samps.cut_with(x=2)._data.squeeze() == np.asarray((105,106,107)))
