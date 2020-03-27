import ast
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from lazyflow.distributed.TaskOrchestrator import TaskOrchestrator
import cProfile

from ndstructs import Array5D, Slice5D, Shape5D, Point5D
from ndstructs.datasource import DataSource, N5DataSource, DataSourceSlice
from ilastik.features.feature_extractor import FeatureExtractor
from ilastik.features import (
    GaussianSmoothing,
    HessianOfGaussianEigenvalues,
    GaussianGradientMagnitude,
    LaplacianOfGaussian,
    DifferenceOfGaussians,
    StructureTensorEigenvalues,
)
from ilastik.annotations import Annotation
from ilastik.classifiers.pixel_classifier import PixelClassifier, ScikitLearnPixelClassifier
from ilastik.classifiers.ilp_pixel_classifier import IlpVigraPixelClassifier
from lazyflow.utility.timer import Timer
import argparse

from ilastik.workflows.pixelClassification.pixel_classification_workflow_2 import (
    PixelClassificationWorkflow2,
    DataLane,
    DataSourceInfo,
)
from ilastik import Project


classifier_registry = {
    IlpVigraPixelClassifier.__name__: IlpVigraPixelClassifier,
    ScikitLearnPixelClassifier.__name__: ScikitLearnPixelClassifier,
}


def make_label_offset(value):
    coords = ast.literal_eval(value)
    if not isinstance(coords, dict):
        raise ValueError("Label offset must be  dict with keys in xyztc")
    return Point5D.zero(**coords)


parser = argparse.ArgumentParser(description="Apply inheritance by template")
parser.add_argument(
    "--classifier-class", required=True, choices=list(classifier_registry.keys()), help="Which pixel classifier to use"
)
parser.add_argument("--data-url", required=True, help="Url to the test data")
parser.add_argument(
    "--label-urls", required=True, nargs="+", help="Url to the uint8, single-channel label images", type=Path
)
parser.add_argument(
    "--label-offsets",
    required=True,
    nargs="+",
    help="Url to the uint8, single-channel label images",
    type=make_label_offset,
)
parser.add_argument(
    "--tile-size", required=False, type=int, default=None, help="Side of the raw data tile to use when predicting"
)
args = parser.parse_args()


# features = list(FeatureExtractor.from_ilp("/home/tomaz/unicore_stuff/UnicoreProject.ilp"))
# print(features)
# tile_shape = args.tile_size if args.tile_size is None else Shape5D.hypercube(args.tile_size)
datasource = DataSource.create(Path(args.data_url))
# print(datasource.full_shape)
print(f"Processing {datasource}")

extractors = [
    GaussianSmoothing.from_ilp_scale(scale=0.3, axis_2d="z", num_input_channels=datasource.shape.c),
    HessianOfGaussianEigenvalues.from_ilp_scale(scale=0.7, axis_2d="z", num_input_channels=datasource.shape.c),
    GaussianGradientMagnitude.from_ilp_scale(scale=0.7, axis_2d="z", num_input_channels=datasource.shape.c),
    LaplacianOfGaussian.from_ilp_scale(scale=0.7, axis_2d="z", num_input_channels=datasource.shape.c),
    DifferenceOfGaussians.from_ilp_scale(scale=0.7, axis_2d="z", num_input_channels=datasource.shape.c),
    StructureTensorEigenvalues.from_ilp_scale(scale=1.0, axis_2d="z", num_input_channels=datasource.shape.c),
]

annotations = []
for label_url, label_offset in zip(args.label_urls, args.label_offsets):
    annotations += list(Annotation.from_file(label_url, raw_data=datasource, location=label_offset))


t = Timer()
with t:
    classifier = classifier_registry[args.classifier_class].train(
        feature_extractors=extractors, annotations=annotations, random_seed=0
    )
print(f"Training {classifier.__class__.__name__} took {t.seconds()}")

pix_classi = PixelClassificationWorkflow2(feature_extractors=extractors, classifier=None)  # classifier
pix_classi.add_annotations(annotations)

data = pix_classi.ilp_data
proj, _ = Project.from_ilp_data(data)
print(proj.file.filename)
proj.close()

predictions = classifier.allocate_predictions(datasource.roi)
t = Timer()
with t:

    def predict_tile(raw_tile):
        tile_prediction = classifier.predict(raw_tile)
        predictions.set(tile_prediction)
        print(f"Tile {raw_tile} done! {time.time()}")

    for raw_tile in DataSourceSlice(datasource).split():
        predict_tile(raw_tile)
print(f"Prediction with {classifier.__class__.__name__} took {t.seconds()}")
predictions.as_uint8().show_channels()
