import argparse
from typing import Dict, List, Any, Optional, Tuple, Mapping
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

from ndstructs import Array5D, Slice5D, Shape5D
from ndstructs.datasource import DataSource, N5DataSource, DataSourceSlice
from ndstructs.datasink import N5DataSink
from ndstructs.utils import JsonSerializable

from ilastik.classifiers.pixel_classifier import PixelClassifierDataSource
from ilastik.classifiers.ilp_pixel_classifier import IlpVigraPixelClassifier
from ilastik.features.ilp_filter import IlpFilter
from ilastik.annotations import Annotation
from lazyflow.distributed.TaskOrchestrator import TaskOrchestrator


class DisplayMode(enum.Enum):
    DEFAULT = "default"
    GRAYSCALE = "grayscale"
    RGBA = "rgba"
    RANDOM_COLORTABLE = "random-colortable"
    BINARY_MASK = "binary-mask"

    @property
    def ilp_data(self) -> str:
        return self.value

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
        self.nickname = nickname or self.datasouce.name
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
            "axisorder": self.datasource.axiskeys,
            "axistags": vigra.defaultAxistags(self.datasource.axiskeys).toJSON(),
            "datasetId": str(uuid.uuid1()),
            "dtype": str(self.datasource.dtype),
            "filePath": self.datasource.path.as_posix(),
            "fromstack": False,  # FIXME
            "location": self.legacy_location,
            "nickname": self.nickname,
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
    def __init__(self, raw_data: Optional[DataSourceInfo] = None, prediction_mask: Optional[DataSourceInfo] = None):
        self.raw_data = raw_data
        self.prediction_mask = prediction_mask

    @property
    def ilp_data(self) -> dict:
        return {
            "Raw Data": {} if self.raw_data is None else self.raw_data.ilp_data,
            "Prediction Mask": {} if self.prediction_mask is None else self.prediction_mask.ilp_data,
        }

    @classmethod
    def from_ilp_data(cls, data):
        raise NotImplementedError(cls.__name__ + ".from_ilp_data")


class PixelClassificationWorkflow2(JsonSerializable):
    """A Base class for INTERACTIVE pixel classification"""

    def __init__(
        self,
        *,
        lanes: List[DataLane],
        feature_extractors: List[IlpFilter],
        annotations: List[Annotation],
        classifier: Optional[IlpVigraPixelClassifier],
    ):
        self.lanes = lanes
        self.feature_extractors = feature_extractors
        self.annotations = annotations
        self.classifier = classifier
        if annotations and set(annot.raw_data for annot in annotations) != set(
            lane.raw_data.datasource for lane in lanes
        ):
            raise ValueError("Annotations should reference only data in the workflow's lanes")
        if classifier is None:
            self.tryUpdatePixelClassifier()

    @property
    def lanes_ilp_data(self) -> Dict[str, Any]:
        return {
            "Role Names": np.asarray([b"Raw Data", b"Prediction Mask"]),
            "StorageVersion": "0.2",
            "infos": {f"lane{lane_idx:04d}": lane.ilp_data for lane_idx, lane in enumerate(self.lanes)},
            "local_data": {},
        }

    @classmethod
    def lanes_from_ilp_data(cls, data) -> List[DataLane]:
        lanes: List[DataLane] = []
        for info in data["infos"].items:
            lanes.append(DataLane.from_ilp_data(info))
        return lanes

    @property
    def feature_extractor_ilp_data(self) -> Dict[str, Any]:
        if not self.feature_extractors:
            return {}
        out = {}
        feature_names = list(set(fe.__class__.__name__ for fe in self.feature_extractors))
        out["FeatureIds"] = np.asarray([fn.encode("utf8") for fn in feature_names])
        scales: List[float] = list(sorted(set(fe.ilp_scale for fe in self.feature_extractors)))
        out["Scales"] = np.asarray(scales)
        ComputeIn2d = np.zeros(len(feature_names), dtype=bool)
        SelectionMatrix = np.zeros((len(feature_names), len(scales)), dtype=bool)
        for fe in self.feature_extractors:
            name_idx = feature_names.index(fe.__class__.__name__)
            scale_idx = scales.index(fe.ilp_scale)
            SelectionMatrix[name_idx, scale_idx] = True
            ComputeIn2d[name_idx] = ComputeIn2d[name_idx] or (fe.axis_2d is not None)
        out["SelectionMatrix"] = SelectionMatrix
        out["ComputeIn2d"] = ComputeIn2d
        return out

    @classmethod
    def feature_extractors_from_ilp_data(cls, data: Mapping, num_input_channels: int) -> List[IlpFilter]:
        feature_names: List[str] = [feature_name.decode("utf-8") for feature_name in data["FeatureIds"][()]]
        compute_in_2d: List[bool] = list(data["ComputeIn2d"][()])
        scales: List[float] = list(data["Scales"][()])
        selection_matrix = data["SelectionMatrix"][()]  # feature name x scales

        feature_extractors = []
        for feature_idx, feature_name in enumerate(feature_names):
            feature_class = IlpFilter.REGISTRY[feature_name]
            for scale_idx, (scale, in_2d) in enumerate(zip(scales, compute_in_2d)):
                if selection_matrix[feature_idx][scale_idx]:
                    axis_2d = "z" if in_2d else None
                    extractor = feature_class.from_ilp_scale(
                        scale, axis_2d=axis_2d, num_input_channels=num_input_channels
                    )
                    feature_extractors.append(extractor)
        return feature_extractors

    @property
    def classifier_ilp_data(self) -> Dict[str, Any]:
        out = {
            "Bookmarks": {"0000": []},
            "LabelColors": {},  # FIXME
            "LabelNames": [],  # FIXME
            "PmapColors": [],  # FIXME
            "StorageVersion": "0.1",
        }
        if self.classifier is not None:
            out["ClassifierForests"] = self.classifier.ilp_data
            out["ClassifierFactory"] = self.classifier.ilp_classifier_factory
        else:
            out["ClassifierFactory"] = IlpVigraPixelClassifier.DEFAULT_ILP_CLASSIFIER_FACTORY

        lanewise_labels = {"labels000": {}}  # empty labels still produce this in classic ilastik
        for lane_idx, lane in enumerate(self.lanes):
            out_lane_data = {}
            for annot_idx, annot in enumerate(self.annotations):
                if annot.raw_data == lane.raw_data.datasource:
                    out_lane_data["block{annot_idx:04d}"] = annot.ilp_data
            out_lane_data[f"labels{lane_idx:03d}"] = out_lane_data
        out["LabelSets"] = lanewise_labels
        return out

    @property
    def ilp_data(self):
        return {
            "Input Data": self.lanes_ilp_data,
            "FeatureSelections": self.feature_extractor_ilp_data,
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
    def from_ilp_data(cls, data) -> "PixelClassificationWorkflow2":
        lanes = (cls.lanes_from_ilp_data(data["Input Data"]),)
        if len(lanes) == 0 or not any(lane.raw_data for lane in lanes):
            raise ValueError(f"Need at least one lane with Raw Data. Lanes: {lanes}")
        num_input_channels = lanes[0].raw_data.datasource.shape.c
        return cls(
            lanes=lanes,
            feature_extractors=cls.feature_extractors_from_ilp_data(
                data["FeatureSelections"], num_input_channels=num_input_channels
            ),
            classifier=IlpVigraPixelClassifier.from_ilp_data(data["PixelClassification"]["ClassifierForests"]),
            annotations=[],  # FIXME
        )

    def tryUpdatePixelClassifier(self) -> Optional[IlpVigraPixelClassifier]:
        if len(self.annotations) > 0 and len(self.feature_extractors) > 0:
            self.classifier = IlpVigraPixelClassifier.train(
                feature_extractors=feature_extractors, annotations=annotations
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
                if not extractor.is_applicable_to(lane.raw_data.datasource):
                    raise ValueError(f"Feature {extractor} is not applicable to {lane.raw_data.datasource}")
            self.feature_extractors.append(extractor)
        self.tryUpdatePixelClassifier()

    def removeFeatureExtractors(self, extractors: List[IlpFilter], updateClassifier: bool = True) -> None:
        for extractor in extractors:
            self.feature_extractors.pop(self.feature_extractors.index(extractor))
        self.tryUpdatePixelClassifier()

    def addAnnotations(self, annotations: List[Annotation]) -> None:
        for annot in annotations:
            if annot in self.annotations:
                raise ValueError(f"Annotation {annot} is already present in the workflow")
            self.annotations.push(annot)
        self.tryUpdatePixelClassifier()

    def removeAnnotations(self, annotations: List[Annotation]) -> None:
        for annot in annotations:
            self.annotations.pop(self.annotations.index(annot))
        self.tryUpdatePixelClassifier()

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
