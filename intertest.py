from concurrent.futures import ThreadPoolExecutor
import json
import vigra
import numpy as np
import pickle
from PIL import Image as PilImage
import time


from ilastik.array5d.array5D import Array5D, Image, ScalarImage
from ilastik.array5d.point5D import Point5D, Slice5D, Shape5D
from ilastik.features.feature_extractor import FeatureExtractorCollection
from ilastik.features.vigra_features import GaussianSmoothing, HessianOfGaussian
from ilastik.annotations import Annotation
from ilastik.classifiers.pixel_classifier import PixelClassifier, StrictPixelClassifier
from ilastik.data_source import FlatDataSource


p = Point5D(x=1, y=2, z=3, t=4, c=5)
assert Point5D.from_json(p.to_json()) == p

slc = Slice5D(x=slice(100, 200), y=slice(200, 300))
#assert Slice5D.from_json(slc.to_json()) == slc


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



apop_raw = FlatDataSource("/home/tomaz/ilastikTests/SampleData/2d_cells_apoptotic_1c/2d_cells_apoptotic_1c.png")
apop_annotations = (
    Annotation.from_png("/home/tomaz/ilastikTests/SampleData/2d_cells_apoptotic_1c/full_image_annotations.png",
                        raw_data=apop_raw),
)

t = time.time()
apop_classifier = StrictPixelClassifier(feature_extractor=fc, annotations=apop_annotations, random_seed=456)
print(f"Ended training at {time.time() - t}")

t = time.time()
apop_predictions = apop_classifier.allocate_predictions(apop_raw)

with ThreadPoolExecutor() as executor:
    for raw_tile in apop_raw.get_tiles():
        def predict_tile(raw_tile):
            tile_prediction, tile_features = apop_classifier.predict(raw_tile)
            apop_predictions.set(tile_prediction)
        executor.submit(predict_tile, raw_tile)

print(f"Ended predictions in {time.time() - t}")

#apop_predictions, apop_features = apop_classifier.predict(apop_raw)
apop_predictions.show()


print(f"Features cache info: {fc.compute.cache_info()}")
#print(f"Classifier cache info: {StrictPixelClassifier.get.cache_info()}")

