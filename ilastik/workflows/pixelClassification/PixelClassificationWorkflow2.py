import argparse
from typing import Dict, List, Any, Optional, Tuple, Mapping, Iterable, Sequence, Set
from numbers import Number
import ast
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import uuid
import enum
import pickle

import h5py
import vigra
import numpy as np

from ndstructs import Array5D, Slice5D, Shape5D, Point5D
from ndstructs.datasource import DataSource, N5DataSource, DataSourceSlice
from ndstructs.datasink import N5DataSink
from ndstructs.utils import JsonSerializable

from ilastik.classifiers.pixel_classifier import PixelClassifierDataSource
from ilastik.classifiers.ilp_pixel_classifier import IlpVigraPixelClassifier
from ilastik.features.ilp_filter import IlpFilter
from ilastik.annotations import Annotation, Color
from lazyflow.distributed.TaskOrchestrator import TaskOrchestrator


class DisplayMode(enum.Enum):
    DEFAULT = "default"
    GRAYSCALE = "grayscale"
    RGBA = "rgba"
    RANDOM_COLORTABLE = "random-colortable"
    BINARY_MASK = "binary-mask"

    @property
    def ilp_data(self) -> str:
        return self.value.encode("utf8")

    @classmethod
    def from_ilp_data(cls, data: bytes) -> "DisplayMode":
        data_str = data.decode("utf-8")
        for item in cls:
            if item.value == data_str:
                return item
        raise ValueError(f"Can't deserialize value {data} into a DisplayMode")


class DataSourceInfo(JsonSerializable):
    def __init__(
        self,
        *,
        datasource: DataSource,
        nickname: str = "",
        fromstack: bool = False,
        allowLabels: bool = True,
        datasetId: str = "",
        display_mode: DisplayMode = DisplayMode.DEFAULT,
        normalizeDisplay: bool = True,
        drange: Optional[Tuple[Number, Number]] = None,
    ):
        self.datasource = datasource
        self.nickname = nickname or self.datasource.name
        self.fromstack = fromstack
        self.allowLabels = allowLabels
        self.datasetId = datasetId or str(uuid.uuid1())
        self.display_mode = display_mode
        self.normalizeDisplay = normalizeDisplay
        self.drange = drange

    @property
    def legacy_location(self) -> str:
        return "FileSystem"  # FIXME

    @property
    def ilp_data(self) -> dict:
        return {
            "allowLabels": True,
            "axisorder": self.datasource.axiskeys.encode("utf8"),
            "axistags": vigra.defaultAxistags(self.datasource.axiskeys).toJSON().encode("utf8"),
            "datasetId": str(uuid.uuid1()).encode("utf8"),
            "dtype": str(self.datasource.dtype).encode("utf8"),
            "filePath": self.datasource.path.as_posix().encode("utf8"),
            "fromstack": False,  # FIXME
            "location": self.legacy_location.encode("utf8"),
            "nickname": self.nickname.encode("utf8"),
            "shape": self.datasource.shape.to_tuple(self.datasource.axiskeys),
            "display_mode": self.display_mode.ilp_data,
            "normalizeDisplay": self.normalizeDisplay,
            "drange": self.drange,
        }

    @classmethod
    def from_ilp_data(cls, data) -> "DataSourceInfo":
        if "axistags" in data:
            axistags = AxisTags.fromJSON(data["axistags"][()].decode("utf-8"))
            axiskeys = "".join(tag.key for tag in axistags)
        elif "axisorder" in data:  # legacy support
            axiskeys = data["axisorder"][()].decode("utf-8")
        filePath = data["filePath"][()].decode("utf-8")
        params = {
            "datasource": DataSource.create(filePath, axiskeys=axiskeys),
            "allowLabels": data["allowLabels"][()],
            "nickname": data["nickname"][()].decode("utf-8"),
        }
        if "normalizeDisplay" in data:
            params["normalizeDisplay"] = bool(data["normalizeDisplay"][()])
        if "drange" in data:
            params["drange"] = tuple(data["drange"])
        if "display_mode" in data:
            params["display_mode"] = data["display_mode"][()].decode("utf-8")
        return cls(**params)


class DataLane:
    def __init__(
        self,
        *,
        RawData: Optional[DataSourceInfo] = None,
        PredictionMask: Optional[DataSourceInfo] = None,
        annotations: Sequence[Annotation] = (),
    ):
        self.RawData = RawData
        self.PredictionMask = PredictionMask
        self.annotations = []
        for annot in annotations:
            self.add_annotation(annot)

    def add_annotation(self, annotation: Annotation):
        if self.RawData is None:
            self.RawData = DataSourceInfo(datasource=datasource)
        if annotation in self.annotations:
            raise ValueError("Annotation already exists in this lane")
        if self.RawData.datasource != annotation.raw_data:
            raise ValueError(f"Annotation {annotation} should be on top of the lane RawData: {self.RawData}")
        self.annotations.append(annotation)

    def remove_annotation(self, annotation: Annotation):
        self.annotations.remove(annotation)

    @classmethod
    def from_ilp_data(cls, data):
        raise NotImplementedError(cls.__name__ + ".from_ilp_data")

    @property
    def ilp_data(self) -> dict:
        return {
            "Raw Data": {} if self.RawData is None else self.RawData.ilp_data,
            "Prediction Mask": {} if self.PredictionMask is None else self.PredictionMask.ilp_data,
        }

    @classmethod
    def dump_as_ilp_data_selection_data(cls, lanes: Sequence["DataLane"]) -> Dict[str, Any]:
        return {
            "Role Names": np.asarray([b"Raw Data", b"Prediction Mask"]),
            "StorageVersion": "0.2",
            "infos": {f"lane{lane_idx:04d}": lane.ilp_data for lane_idx, lane in enumerate(lanes)},
            "local_data": {},
        }

    @classmethod
    def dump_as_ilp_label_data(cls, lanes: Sequence["DataLane"]) -> Dict[str, Any]:
        out = {}
        color_map = Color.create_color_map(annot.color for lane in lanes for annot in lane.annotations)
        out["LabelSets"] = labelSets = {"labels000": {}}  # empty labels still produce this in classic ilastik
        for lane_idx, lane in enumerate(lanes):
            label_data = Annotation.dump_as_ilp_data(lane.annotations, color_map=color_map)
            labelSets[f"labels{lane_idx:03d}"] = label_data
        out["LabelColors"] = np.asarray([color.rgba[:-1] for color in color_map.keys()], dtype=np.int64)
        out["PmapColors"] = out["LabelColors"]
        out["LabelNames"] = np.asarray([color.name.encode("utf8") for color in color_map.keys()])
        return out


class PixelClassificationWorkflow2(JsonSerializable):
    """A Base class for INTERACTIVE pixel classification"""

    def __init__(
        self,
        *,
        lanes: Sequence[DataLane] = (),
        feature_extractors: Sequence[IlpFilter] = (),
        classifier: Optional[IlpVigraPixelClassifier] = None,
    ):
        self.lanes = lanes or []
        self.feature_extractors = feature_extractors or []
        self.classifier = classifier

        if classifier is None:
            self.tryUpdatePixelClassifier()

    @classmethod
    def from_ilp_data(cls, data) -> "PixelClassificationWorkflow2":
        lanes = (cls.lanes_from_ilp_data(data["Input Data"]),)
        if len(lanes) == 0 or not any(lane.RawData for lane in lanes):
            raise ValueError(f"Need at least one lane with Raw Data. Lanes: {lanes}")
        num_input_channels = lanes[0].RawData.datasource.shape.c
        return cls(
            lanes=lanes,
            feature_extractors=cls.feature_extractors_from_ilp_data(
                data["FeatureSelections"], num_input_channels=num_input_channels
            ),
            classifier=IlpVigraPixelClassifier.from_ilp_data(data["PixelClassification"]["ClassifierForests"]),
            annotations=[],  # FIXME
        )

    @property
    def annotations(self) -> Sequence[Annotation]:
        annotations = []
        for lane in self.lanes:
            annotations += lane.annotations
        return annotations

    @property
    def num_annotations(self) -> int:
        return sum(len(lane.annotations) for lane in self.lanes)

    def tryUpdatePixelClassifier(self) -> Optional[IlpVigraPixelClassifier]:
        if self.num_annotations > 0 and len(self.feature_extractors) > 0:
            self.classifier = IlpVigraPixelClassifier.train(
                feature_extractors=self.feature_extractors, annotations=self.annotations
            )
        else:
            self.classifier = None
        return self.classifier

    def clearFeatureExtractors(self) -> None:
        self.feature_extractors = []

    def addFeatureExtractors(self, extractors: List[IlpFilter], updateClassifier: bool = True) -> None:
        for extractor in extractors:
            if extractor in self.feature_extractors:
                raise ValueError(f"Feature Extractor {extractor} is already present in this Workflow")
            for lane in self.lanes:
                if not extractor.is_applicable_to(lane.RawData.datasource):
                    raise ValueError(f"Feature {extractor} is not applicable to {lane.RawData.datasource}")
            self.feature_extractors.append(extractor)
        self.tryUpdatePixelClassifier()

    def removeFeatureExtractors(self, extractors: List[IlpFilter], updateClassifier: bool = True) -> None:
        for extractor in extractors:
            self.feature_extractors.pop(self.feature_extractors.index(extractor))
        self.tryUpdatePixelClassifier()

    def lane_for_annotation(self, annot: Annotation):
        for lane in self.lanes:
            if lane.RawData.datasource == annot.raw_data:
                return lane
        raise KeyError(f"No lane has annotation's datasource {annot.raw_data}")

    def add_annotations(self, annotations: List[Annotation]) -> None:
        for annot in annotations:
            try:
                lane = self.lane_for_annotation(annot)
            except KeyError:
                lane = DataLane(RawData=DataSourceInfo(datasource=annot.raw_data))
                self.lanes.append(lane)
            lane.add_annotation(annot)
        self.tryUpdatePixelClassifier()

    def remove_annotations(self, annotations: List[Annotation]) -> None:
        for annot in annotations:
            self.lane_for_annotation(annot).remove_annotation(annot)
        self.tryUpdatePixelClassifier()

    @property
    def classifier_ilp_data(self) -> Dict[str, Any]:
        out = {
            "Bookmarks": {"0000": []},
            "StorageVersion": "0.1",
            "ClassifierFactory": IlpVigraPixelClassifier.DEFAULT_ILP_CLASSIFIER_FACTORY,
        }
        if self.classifier is not None:
            out["ClassifierForests"] = self.classifier.ilp_data
            out["ClassifierFactory"] = self.classifier.ilp_classifier_factory
        out.update(DataLane.dump_as_ilp_label_data(self.lanes))
        return out

    @property
    def ilp_data(self):
        return {
            "Input Data": DataLane.dump_as_ilp_data_selection_data(self.lanes),
            "FeatureSelections": IlpFilter.dump_as_ilp_data(self.feature_extractors),
            "PixelClassification": self.classifier_ilp_data,
            "Prediction Export": {
                "OutputFilenameFormat": "{dataset_dir}/{nickname}_{result_type}",
                "OutputFormat": "hdf5",
                "OutputInternalPath": "exported_data",
                "StorageVersion": "0.1",
            },
            "currentApplet": 0,
            "ilastikVersion": b"1.3.2post1",  # FIXME
            "time": b"Wed Mar 11 15:40:37 2020",  # FIXME
            "workflowName": b"Pixel Classification",
        }

    @classmethod
    def headless(cls):
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
        workflow = cls.from_ilp(ilp)
        classifier = IlpVigraPixelClassifier.from_ilp_group(ilp["PixelClassification/ClassifierForests"])
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


# PixelClassificationWorkflow2.headless()
