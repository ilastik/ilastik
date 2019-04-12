from collections import defaultdict

from PIL import Image as PilImage
from ilastik.labels.sampler import Sampler
from ilastik.array5d.array5D import Array5D, Image, ScalarImage
from ilastik.array5d.point5D import Point5D, Slice5D, Shape5D
from ilastik.features.feature_extractor import FeatureCollection
from ilastik.features.vigra_features import GaussianSmoothing, HessianOfGaussian
from ilastik.labels.annotation import Annotation
from ilastik.classifiers.pixel_classifier import PixelClassifier


import vigra
import numpy as np

a = Image.open_image("/home/tomaz/ilastikTests/SampleData/c_cells/cropped/cropped1.png")



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


labels = Sampler.allocate(Shape5D(x=10, y=10), dtype=np.uint8, value=0)
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

samps, classes = labels.sample(fake_features)

classes = list(classes.raw())
assert all(samps.cut_with(x=classes.index(123))._data.squeeze() == np.asarray((5,6,7)))
assert all(samps.cut_with(x=classes.index(100))._data.squeeze() == np.asarray((15,16,17)))
assert all(samps.cut_with(x=classes.index(23))._data.squeeze() == np.asarray((105,106,107)))


########################
raw_data = np.asarray(PilImage.open("/home/tomaz/ilastikTests/SampleData/c_cells/cropped/cropped1.png"))
raw_data = Array5D(vigra.Image(raw_data))

scribblings = np.asarray(PilImage.open("/home/tomaz/source/ilastik-meta/ilastik/tests/api/scribblings.png"))
scribblings = Sampler(vigra.Image(scribblings))

annotation = Annotation(scribblings=scribblings, image=raw_data)
samples, sample_classes = annotation.get_samples(fc)

computed_feats.linear_raw()

#####################3333

classifier = PixelClassifier(feature_collection=fc, annotations=[annotation])
