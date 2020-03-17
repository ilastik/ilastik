from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from typing import List, Iterator, Tuple, Dict, Iterable, Sequence
from dataclasses import dataclass
from collections.abc import Mapping as BaseMapping
from numbers import Number

import numpy as np
from ndstructs import Slice5D, Point5D, Shape5D
from ndstructs import Array5D, Image, ScalarData, StaticLine, LinearData
from ilastik.features.feature_extractor import FeatureExtractor, FeatureData
from ndstructs.datasource import DataSource, DataSourceSlice
from ndstructs.utils import JsonSerializable, from_json_data
from PIL import Image as PilImage


class Color:
    def __init__(self, r: int = 0, g: int = 0, b: int = 0, a: int = 255):
        self.r = r
        self.g = g
        self.b = b
        self.a = a

    @classmethod
    def from_channels(cls, channels: List[Number]) -> "Color":
        if len(channels) == 0 or len(channels) > 4:
            raise ValueError(f"Cannnot create color from {channels}")
        if len(channels) == 1:
            gray = channels[0]
            return cls(r=gray, g=gray, b=gray)
        return cls(*channels)

    @property
    def rgba(self) -> Tuple[int, int, int, int]:
        return (self.r, self.g, self.b, self.a)

    @property
    def q_rgba(self) -> int:
        return sum(c * (16 ** (3 - idx)) for idx, c in enumerate(self.rgba))

    def __hash__(self):
        return hash(self.rgba)

    def __eq__(self, other):
        return not isinstance(other, Color) or self.rgba == other.rgba


class FeatureSamples(FeatureData, StaticLine):
    """A multi-channel array with a single spacial dimension, with eac channel
    representing a feature calculated on top of a annotated pixel"""

    @classmethod
    def create(cls, annotation: "Annotation", data: FeatureData):
        samples = data.sample_channels(annotation.as_mask())
        return cls.fromArray5D(samples)


class AnnotationOutOfBounds(Exception):
    def __init__(self, annotation_roi: Slice5D, raw_data: DataSource):
        super().__init__(f"Annotation roi {roi} exceeds bounds of raw_data {raw_data}")


class Annotation(ScalarData):
    """User annotation attached to the raw data onto which they were drawn"""

    def __hash__(self):
        return hash((self._data.tobytes(), self.color))

    def __eq__(self, other):
        if isinstance(other, Annotation):
            return False
        return self.color == other.color and np.all(self._data == other._data)

    def __init__(
        self, arr: np.ndarray, *, axiskeys: str, location: Point5D = Point5D.zero(), color: Color, raw_data: DataSource
    ):
        super().__init__(arr.astype(bool), axiskeys=axiskeys, location=location)
        if not raw_data.roi.contains(self.roi):
            raise AnnotationOutOfBounds(annotation_roi=self.roi, raw_data=raw_data)
        self.color = color
        self.raw_data = raw_data

    def rebuild(self, arr: np.ndarray, axiskeys: str, location: Point5D = None) -> "Annotation":
        location = self.location if location is None else location
        return self.__class__(arr, axiskeys=axiskeys, location=location, color=self.color, raw_data=self.raw_data)

    @classmethod
    def from_file(cls, path: str, raw_data: DataSource, location: Point5D = Point5D.zero()) -> Iterable["Annotation"]:
        labels = DataSource.create(path)
        label_data = labels.retrieve(Slice5D.all())
        for color_array in label_data.unique_colors().colors:
            single_color_labels = label_data.color_filtered(color_array)
            axiskeys = "tzyxc"
            color = Color.from_channels(color_array.raw("c"))
            yield cls(single_color_labels.raw(axiskeys), axiskeys=axiskeys, location=location, raw_data=raw_data)

    @classmethod
    def interpolate_from_points(cls, color: Color, voxels: List[Point5D], raw_data: DataSource):
        start = Point5D.min_coords(voxels)
        stop = Point5D.max_coords(voxels) + 1  # +1 because slice.stop is exclusive, but max_point isinclusive
        scribbling_roi = Slice5D.create_from_start_stop(start=start, stop=stop)
        if scribbling_roi.shape.c != 1:
            raise ValueError(f"Annotations must not span multiple channels: {voxels}")
        scribblings = Array5D.allocate(scribbling_roi, dtype=np.dtype(bool), value=False)

        anchor = voxels[0]
        for voxel in voxels:
            for interp_voxel in anchor.interpolate_until(voxel):
                scribblings.paint_point(point=interp_voxel, value=True)
            anchor = voxel

        return cls(scribblings._data, axiskeys=scribblings.axiskeys, color=color, raw_data=raw_data, location=start)

    @classmethod
    def from_json_data(cls, data):
        return from_json_data(cls.interpolate_from_points, data)

    def json_data(self):
        data = super().json_data
        data["color"] = color
        data["voxels"] = [vx.json_data for vx in self.voxels]
        return data

    def get_feature_samples(self, feature_extractor: FeatureExtractor) -> FeatureSamples:
        all_feature_samples = []
        annotated_roi = self.roi.with_full_c()

        with ThreadPoolExecutor() as executor:
            for data_tile in DataSourceSlice(self.raw_data).clamped(annotated_roi).get_tiles():

                def make_samples(data_tile):
                    annotation_tile = self.clamped(data_tile)
                    feature_tile = feature_extractor.compute(data_tile).clamped(annotation_tile.roi.with_full_c())

                    feature_samples = FeatureSamples.create(annotation_tile, feature_tile)
                    assert feature_samples.shape.c == feature_extractor.get_expected_shape(data_tile.shape).c
                    all_feature_samples.append(feature_samples)

                executor.submit(make_samples, data_tile)
        return all_feature_samples[0].concatenate(*all_feature_samples[1:])

    @property
    def ilp_data(self) -> dict:
        axiskeys = self.raw_data.axiskeys
        return {
            "__data__": self.raw(axiskeys),
            "__attrs__": {
                "blockSlice": "[" + ",".join(f"{slc.start}:{slc.stop}" for slc in self.roi.to_slices(axiskeys)) + "]"
            },
        }

    def __repr__(self):
        return f"<Annotation {self.shape} for raw_data: {self.raw_data}>"
