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

raw_data = np.asarray(PilImage.open("/home/tomaz/ilastikTests/SampleData/c_cells/cropped/cropped1.png"))
raw_data = Array5D(vigra.taggedView(raw_data, axistags='yxc'))

scribblings = np.asarray(PilImage.open("/home/tomaz/ilastikTests/SampleData/c_cells/cropped/cropped1_fake_annotations.png"))
scribblings = Sampler(vigra.taggedView(scribblings, axistags='yx'))

annotation = Annotation(scribblings=scribblings, raw_data=raw_data)

fc = FeatureCollection(GaussianSmoothing(sigma=0.3))#, HessianOfGaussian(sigma=1.2), GaussianSmoothing(sigma=1.7))
classifier = PixelClassifier(feature_collection=fc, annotations=[annotation])
predictions = classifier.predict(raw_data)
pred_as_images = [img.as_pil_image() for img in predictions.images()]
