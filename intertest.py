import json
import vigra
import numpy as np
import pickle
from PIL import Image as PilImage


from ilastik.array5d.array5D import Array5D, Image, ScalarImage
from ilastik.array5d.point5D import Point5D, Slice5D, Shape5D
from ilastik.features.feature_extractor import FeatureExtractorCollection
from ilastik.features.vigra_features import GaussianSmoothing, HessianOfGaussian
from ilastik.annotations import Annotation
from ilastik.classifiers.pixel_classifier import PixelClassifier, StrictPixelClassifier
from ilastik.data_source import FlatDataSource

def save_test_images(data:Array5D, prefix:str):
    pil_images = [c.as_pil_image() for img in data.as_uint8().images() for c in img.channels()]
    for idx, pi in enumerate(pil_images):
        path = f"/tmp/intertest_{prefix}_{idx}.png"
        pi.save(path)
        import os; os.system(f"gimp {path}")

p = Point5D(x=1, y=2, z=3, t=4, c=5)
assert json.loads(p.to_json()) == p.to_dict()
assert Point5D.from_json(json.loads(p.to_json())) == p

slc = Slice5D(x=slice(100, 200), y=slice(200, 300))
#assert Slice5D.from_json(json.loads(slc.to_json())) == slc


#cutout_test_file = "/home/tomaz/ilastikTests/SampleData/c_cells/cropped/cropped1_numbered_tiles.png"
#cutout_source = FlatDataSource(cutout_test_file, x=slice(20, 50), y=slice(20, 50))
#cutout = cutout_source.retrieve()
#raw_cutout = np.asarray(PilImage.open(cutout_test_file))[20:50, 20:50]
#assert np.all(raw_cutout == cutout.raw('yx'))
#
#
#raw_data1 = FlatDataSource("/home/tomaz/ilastikTests/SampleData/c_cells/cropped/cropped1.png")
##assert FlatDataSource.from_json(json.loads(raw_data1.to_json())) == raw_data1
##assert pickle.loads(pickle.dumps(raw_data1)) == raw_data1
#
fc = FeatureExtractorCollection((GaussianSmoothing(sigma=0.3),  HessianOfGaussian(sigma=1.5), GaussianSmoothing(sigma=1.5)))
#
#annotations = (
#    Annotation.from_png("/home/tomaz/SampleData/c_cells/cropped/cropped1_10_annotations_offset_by_188_124.png",
#                        raw_data=raw_data1, location=Point5D.zero(x=188, y=124)),
#    Annotation.from_png("/home/tomaz/ilastikTests/SampleData/c_cells/cropped/cropped1_15_annotations_offset_by_624_363.png",
#                        raw_data=raw_data1, location=Point5D.zero(x=624, y=363))
#)
#
#classifier = StrictPixelClassifier.get(feature_extractor=fc, annotations=annotations, random_seed=123)
#predictions, features = classifier.predict(raw_data1)
#save_test_images(predictions, 'full')
#
#
#
#raw_data2 = FlatDataSource("/home/tomaz/ilastikTests/SampleData/c_cells/cropped/cropped2.png", x=slice(100,200), y=slice(100,200))
#classifier2 = StrictPixelClassifier.get(feature_extractor=fc, annotations=annotations, random_seed=123)
#predictions2, features2 = classifier.predict(raw_data2)
#save_test_images(predictions2, 'sliced')



apoptotic_raw_data = FlatDataSource("/home/tomaz/ilastikTests/SampleData/2d_cells_apoptotic_1c/2d_cells_apoptotic_1c.png")
apoptotic_annotations = (
    Annotation.from_png("/home/tomaz/ilastikTests/SampleData/2d_cells_apoptotic_1c/full_image_annotations.png",
                        raw_data=apoptotic_raw_data),
)
apoptotic_classifier = StrictPixelClassifier(feature_extractor=fc, annotations=apoptotic_annotations, random_seed=456)
apoptotic_predictions, apoptotic_features = apoptotic_classifier.predict(apoptotic_raw_data)
save_test_images(apoptotic_predictions, 'apoptotic')


print(f"Features cache info: {fc.compute.cache_info()}")
#print(f"Classifier cache info: {StrictPixelClassifier.get.cache_info()}")

