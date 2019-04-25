from collections import defaultdict

from PIL import Image as PilImage
from ilastik.array5d.array5D import Array5D, Image, ScalarImage
from ilastik.array5d.point5D import Point5D, Slice5D, Shape5D
from ilastik.features.feature_extractor import FeatureCollection
from ilastik.features.vigra_features import GaussianSmoothing, HessianOfGaussian
from ilastik.annotations import Annotation
from ilastik.classifiers.pixel_classifier import PixelClassifier
from ilastik.data_source import FlatDataSource


import vigra
import numpy as np

raw_data1 = FlatDataSource("/home/tomaz/ilastikTests/SampleData/c_cells/cropped/cropped1.png")
scribblings1 = FlatDataSource("/home/tomaz/ilastikTests/SampleData/c_cells/cropped/cropped1_fake_annotations.png")
scribblings2 = FlatDataSource("/home/tomaz/ilastikTests/SampleData/c_cells/cropped/cropped1_fake_annotations_bottom_left.png")

annotations = [
    Annotation(scribblings1.astype(np.uint32), axiskeys='yx', raw_data=raw_data1),
    Annotation(scribblings2.astype(np.uint32), axiskeys='yx', raw_data=raw_data1)
]

fc = FeatureCollection(GaussianSmoothing(sigma=0.3), HessianOfGaussian(sigma=1.2), GaussianSmoothing(sigma=1.7))
classifier = PixelClassifier(feature_collection=fc, annotations=annotations)
predictions = classifier.predict(raw_data1)

pil_images = [c.as_pil_image() for img in predictions.as_uint8().images() for c in img.channels()]



raw_data2 = np.asarray(PilImage.open("/home/tomaz/ilastikTests/SampleData/c_cells/cropped/cropped2.png"))
raw_data2 = Array5D(raw_data2, axiskeys='yxc')
predictions2 = classifier.predict(raw_data2)
pil_images2 = [c.as_pil_image() for img in predictions2.as_uint8().images() for c in img.channels()]
