import pytest
import numpy as np
import time
import h5py
import z5py
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from lazyflow.distributed.TaskOrchestrator import TaskOrchestrator
import cProfile

from ndstructs import Array5D, Slice5D, Shape5D
from ndstructs.datasource import DataSource, N5DataSource, BackedSlice5D
from ilastik.features.feature_extractor import FeatureExtractor
from ilastik.features.fastfilters import (
    GaussianSmoothing,
    HessianOfGaussianEigenvalues,
    GaussianGradientMagnitude,
    LaplacianOfGaussian,
    DifferenceOfGaussians,
    StructureTensorEigenvalues,
)
from ilastik.annotations import Annotation
from ilastik.classifiers.pixel_classifier import (
    PixelClassifier,
    StrictPixelClassifier,
    ScikitLearnPixelClassifier,
    VigraPixelClassifier,
)

features = list(FeatureExtractor.from_ilp("/home/tomaz/unicore_stuff/UnicoreProject.ilp"))
# print(features)

# datasource = DataSource.create("/home/tomaz/SampleData/n5tests/317_8_CamKII_tTA_lacZ_Xgal_s123_1.4.n5/data")#, tile_shape=Shape5D.hypercube(1024))
# datasource = DataSource.create("/home/tomaz/SampleData/c_cells/cropped/huge/cropped1.png")
datasource = DataSource.create("/home/tomaz/SampleData/c_cells/cropped/cropped1.png")
# print(datasource.full_shape)
print(datasource.tile_shape)

extractors = (
    GaussianSmoothing(sigma=0.3, axis_2d="z"),
    HessianOfGaussianEigenvalues(scale=1.0, axis_2d="z"),
    GaussianGradientMagnitude(sigma=0.3, axis_2d="z"),
    LaplacianOfGaussian(scale=0.3, axis_2d="z"),
    DifferenceOfGaussians(sigma0=0.3, sigma1=1.0 * 0.66, axis_2d="z"),
    StructureTensorEigenvalues(innerScale=1.0, outerScale=1.0 * 0.5, axis_2d="z"),
)

annotations = (
    Annotation.from_png(
        "/home/tomaz/SampleData/c_cells/cropped/cropped1_10_annotations_offset_by_188_124.png", raw_data=datasource
    ),
)

classifier = ScikitLearnPixelClassifier(feature_extractors=extractors, annotations=annotations, random_seed=0)
print("Classifier created!!")

data_slice = BackedSlice5D(datasource)
expected_predictions_shape = classifier.get_expected_roi(data_slice).shape

predictions = classifier.allocate_predictions(datasource.roi)
# with ProcessPoolExecutor(max_workers=16) as executor:
for raw_tile in BackedSlice5D(datasource).split():

    def predict_tile(raw_tile):
        tile_prediction, tile_features = classifier.predict(raw_tile)
        predictions.set(tile_prediction)
        print(f"Tile {raw_tile} done! {time.time()}")

    predict_tile(raw_tile)
    # executor.submit(predict_tile, raw_tile)


predictions.as_uint8().show_channels()
