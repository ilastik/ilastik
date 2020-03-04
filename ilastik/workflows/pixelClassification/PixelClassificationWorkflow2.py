import argparse
import ast
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

import h5py
from ndstructs import Array5D, Slice5D, Shape5D
from ndstructs.datasource import DataSource, N5DataSource, DataSourceSlice
from ndstructs.datasink import N5DataSink

from ilastik.classifiers.pixel_classifier import VigraPixelClassifier, PixelClassifierDataSource
from lazyflow.distributed.TaskOrchestrator import TaskOrchestrator


class PixelClassificationWorkflow2:
    @classmethod
    def main(cls):
        parser = argparse.ArgumentParser(description="Headless Pixel Classification Workflow")
        parser.add_argument("--project", required=True, type=Path)
        parser.add_argument("--raw-data", required=True, nargs="+", type=Path, help="Raw Data to be processed")
        parser.add_argument("--roi-x", default=None, type=lambda s: slice(ast.literal_eval(s)))
        parser.add_argument("--roi-y", default=None, type=lambda s: slice(ast.literal_eval(s)))
        parser.add_argument("--roi-z", default=None, type=lambda s: slice(ast.literal_eval(s)))
        parser.add_argument("--roi-t", default=None, type=lambda s: slice(ast.literal_eval(s)))
        parser.add_argument("--roi-c", default=None, type=lambda s: slice(ast.literal_eval(s)))
        args = parser.parse_args()

        ilp = h5py.File(args.project, "r")
        # import pydevd; pydevd.settrace()
        classifier = VigraPixelClassifier.from_ilp_group(ilp["PixelClassification/ClassifierForests"])
        for raw_path in args.raw_data:
            datasource = DataSource.create(raw_path.as_posix())
            predictions_datasource = PixelClassifierDataSource(classifier=classifier, raw_datasource=datasource)
            data_slice = DataSourceSlice(
                datasource=predictions_datasource, x=args.roi_x, y=args.roi_y, z=args.roi_z, t=args.roi_t, c=args.roi_c
            )
            dataset_path = Path(raw_path.stem + "_Probabilities.n5/exported_data")
            sink = N5DataSink(path=dataset_path, data_slice=data_slice)
            for tile in data_slice.split():
                print(f"Processing tile {tile}")
                sink.process(tile)

            n5ds = N5DataSource(dataset_path)
            n5ds.retrieve(Slice5D.all()).as_uint8().show_channels()


PixelClassificationWorkflow2.main()
