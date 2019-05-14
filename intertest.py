import json
import vigra
import numpy as np


from ilastik.array5d.array5D import Array5D, Image, ScalarImage
from ilastik.array5d.point5D import Point5D, Slice5D, Shape5D
from ilastik.features.feature_extractor import FeatureCollection
from ilastik.features.vigra_features import GaussianSmoothing, HessianOfGaussian
from ilastik.annotations import Annotation
from ilastik.classifiers.pixel_classifier import PixelClassifier, StrictPixelClassifier
from ilastik.data_source import FlatDataSource

p = Point5D(x=1, y=2, z=3, t=4, c=5)
assert json.loads(p.to_json()) == p.to_dict()
assert Point5D.from_json(json.loads(p.to_json())) == p

slc = Slice5D(x=slice(100, 200), y=slice(200, 300))
assert Slice5D.from_json(json.loads(slc.to_json())) == slc


raw_data1 = FlatDataSource("/home/tomaz/ilastikTests/SampleData/c_cells/cropped/cropped1.png")
assert FlatDataSource.from_json(json.loads(raw_data1.to_json())) == raw_data1

annotations = [
    Annotation.from_png("/home/tomaz/ilastikTests/SampleData/c_cells/cropped/cropped1_fake_annotations.png", raw_data1),
    Annotation.from_png("/home/tomaz/ilastikTests/SampleData/c_cells/cropped/cropped1_fake_annotations_bottom_left.png", raw_data1)
]

fc = FeatureCollection(GaussianSmoothing(sigma=0.3), HessianOfGaussian(sigma=1.2), GaussianSmoothing(sigma=1.7))
classifier = StrictPixelClassifier(feature_extractor=fc, annotations=annotations)
predictions, features = classifier.predict(raw_data1.all())

pil_images = [c.as_pil_image() for img in predictions.as_uint8().images() for c in img.channels()]



raw_data2 = FlatDataSource("/home/tomaz/ilastikTests/SampleData/c_cells/cropped/cropped2.png")
predictions2, features2 = classifier.predict(raw_data2.spec(x=slice(100,200), y=slice(100,200)))
pil_images2 = [c.as_pil_image() for img in predictions2.as_uint8().images() for c in img.channels()]
