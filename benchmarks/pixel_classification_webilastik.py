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
from ilastik.classifiers.pixel_classifier import PixelClassifier, ScikitLearnPixelClassifier, VigraPixelClassifier
from lazyflow.utility.timer import Timer
import argparse

classifier_registry = {
    VigraPixelClassifier.__name__: VigraPixelClassifier,
    ScikitLearnPixelClassifier.__name__: ScikitLearnPixelClassifier,
}


parser = argparse.ArgumentParser(description="Apply inheritance by template")
parser.add_argument(
    "--classifier-class", required=True, choices=list(classifier_registry.keys()), help="Which pixel classifier to use"
)
parser.add_argument("--data-url", required=True, help="Url to the test data")
parser.add_argument("--label-urls", required=True, nargs="+", help="Url to the uint8, single-channel label images")
parser.add_argument(
    "--tile-size", required=False, type=int, default=None, help="Side of the raw data tile to use when predicting"
)
args = parser.parse_args()


# features = list(FeatureExtractor.from_ilp("/home/tomaz/unicore_stuff/UnicoreProject.ilp"))
# print(features)
tile_shape = args.tile_size if args.tile_size is None else Shape5D.hypercube(args.tile_size)
datasource = DataSource.create(args.data_url, tile_shape=tile_shape)
# print(datasource.full_shape)
print(f"Processing {datasource}")

extractors = (
    GaussianSmoothing(sigma=0.3, axis_2d="z"),
    HessianOfGaussianEigenvalues(scale=1.0, axis_2d="z"),
    GaussianGradientMagnitude(sigma=0.3, axis_2d="z"),
    LaplacianOfGaussian(scale=0.3, axis_2d="z"),
    DifferenceOfGaussians(sigma0=0.3, sigma1=1.0 * 0.66, axis_2d="z"),
    StructureTensorEigenvalues(innerScale=1.0, outerScale=1.0 * 0.5, axis_2d="z"),
)

annotations = tuple(Annotation.from_png(label_url, raw_data=datasource) for label_url in args.label_urls)
t = Timer()
with t:
    classifier = classifier_registry[args.classifier_class](
        feature_extractors=extractors, annotations=annotations, random_seed=0
    )
print(f"Training {classifier.__class__.__name__} took {t.seconds()}")

predictions = classifier.allocate_predictions(datasource.roi)
t = Timer()
with t:

    def predict_tile(raw_tile):
        tile_prediction, tile_features = classifier.predict(raw_tile)
        predictions.set(tile_prediction)
        print(f"Tile {raw_tile} done! {time.time()}")

    for raw_tile in BackedSlice5D(datasource).split():
        predict_tile(raw_tile)
print(f"Prediction with {classifier.__class__.__name__} took {t.seconds()}")
predictions.as_uint8().show_channels()
