import ast
import time
from pathlib import Path
from typing import Any, Union
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
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
from ilastik.classifiers.pixel_classifier import PixelClassifier, ScikitLearnPixelClassifier, Predictions
from ilastik.classifiers.ilp_pixel_classifier import IlpVigraPixelClassifier
from lazyflow.utility.timer import Timer
import argparse

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

parser.add_argument(
    "--num-workers", required=False, type=int, default=8, help="Number of process workers to run predictions"
)
parser.add_argument("--orchestrator", required=True, choices=["mpi", "thread-pool"])
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

import pickle

pickled_classifier = pickle.dumps(classifier)
classifier = pickle.loads(pickled_classifier)

predictions = classifier.allocate_predictions(datasource.roi)

slc_generator = (raw_tile for raw_tile in datasource.roi.split(datasource.tile_shape))

t = Timer()
if args.orchestrator == "mpi":
    from lazyflow.distributed.TaskOrchestrator import TaskOrchestrator

    orchestrator = TaskOrchestrator()
    if orchestrator.rank != 0:

        def do_predict(slc: Slice5D, rank: int):
            print(f">>>>>>>> Predicting on {slc}")
            data_source_slice = DataSourceSlice(datasource, **slc.to_dict())
            prediction_tile = classifier.predict(data_source_slice)
            print(f">>>>>>>> Predicting on {slc}")
            return prediction_tile

        orchestrator.start_as_worker(do_predict)
        exit(0)
    with t:

        def collect_predictions(prediction_tile: Predictions):
            predictions.set(prediction_tile)

        orchestrator.orchestrate(slc_generator, collector=collect_predictions)
elif args.orchestrator == "thread-pool":
    with t:

        def do_predict(datasource_slc: DataSourceSlice):
            print(f">>>>>>>> Predicting on {datasource_slc.roi}")
            pred_tile = classifier.predict(datasource_slc)
            print(f"<<<<<<<< DONE Predicting on {datasource_slc.roi}")
            predictions.set(pred_tile)

        with ThreadPoolExecutor(max_workers=args.num_workers) as executor:
            for datasource_slc in DataSourceSlice(datasource).split():
                executor.submit(do_predict, datasource_slc)
else:
    raise NotImplementedError(f"Please implement orchestraiton for {args.orchestrator}")

#    executor = ProcessPoolExecutor(initializer=worker_initializer, initargs=(classifier,))
#    #worker_initializer(classifier)
#    futures = [executor.submit(do_prediction, raw_tile) for raw_tile in datasource.roi.split(datasource.tile_shape)]
#    #futures = [do_prediction(raw_tile) for raw_tile in datasource.roi.split(datasource.tile_shape)]
#    #executor.shutdown(wait=True)
#    for f in futures:
#        result = f.result()
#        predictions.set(result)
#        #predictions.set(f)
print(f"Prediction with {classifier.__class__.__name__} took {t.seconds()}")
predictions.as_uint8().show_channels()
