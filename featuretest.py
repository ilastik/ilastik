import pytest
import numpy as np
import time
from concurrent.futures import ThreadPoolExecutor
import cProfile

from ndstructs import Array5D, Slice5D, Shape5D
from ndstructs.datasource import DataSource, N5DataSource, BackedSlice5D
from ilastik.features.fastfilters import (
    GaussianSmoothing,
    HessianOfGaussianEigenvalues,
    GaussianGradientMagnitude,
    LaplacianOfGaussian,
    DifferenceOfGaussians,
    StructureTensorEigenvalues
)
from ilastik.annotations import Annotation
from ilastik.classifiers.pixel_classifier import PixelClassifier, StrictPixelClassifier

datasource = DataSource.create("/home/tomaz/SampleData/n5tests/317_8_CamKII_tTA_lacZ_Xgal_s123_1.4.n5/data")#, tile_shape=Shape5D.hypercube(1024))
#datasource = DataSource.create("/home/tomaz/SampleData/c_cells/cropped/huge/cropped1.png")
#print(datasource.full_shape)
print(datasource.tile_shape)

extractors = (
    GaussianSmoothing(sigma=0.3, axis_2d='z'),
    HessianOfGaussianEigenvalues(scale=1.0, axis_2d='z'),
    GaussianGradientMagnitude(sigma=0.3, axis_2d='z'),
    LaplacianOfGaussian(scale=0.3, axis_2d='z'),
    DifferenceOfGaussians(sigma0=0.3, sigma1=1.0 * 0.66, axis_2d='z'),
    StructureTensorEigenvalues(innerScale=1.0, outerScale=1.0 * 0.5, axis_2d='z'),
)

annotations = (
    Annotation.from_png("/home/tomaz/SampleData/c_cells/cropped/cropped1_10_annotations_offset_by_188_124.png",
                        raw_data=datasource),
)

classifier = PixelClassifier(feature_extractors=extractors, annotations=annotations)

print("Classifier created!!")


predictions = classifier.allocate_predictions(datasource.roi)
with ThreadPoolExecutor(max_workers=8) as executor:
    tiles = list(BackedSlice5D(datasource).get_tiles())
    for raw_tile in tiles:
        def predict_tile(raw_tile):
            tile_prediction, tile_features = classifier.predict(raw_tile)
            #predictions.set(tile_prediction)
            print(f"Tile {raw_tile} done! {time.time()}")
        executor.submit(predict_tile, raw_tile)

