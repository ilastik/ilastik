###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2025, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#          http://ilastik.org/license.html
###############################################################################
# pyright: strict
from collections import OrderedDict
from pathlib import Path
from typing import Annotated, Dict, List, Literal, Optional, Tuple

import annotated_types
import h5py
import numpy
import numpy.typing as npt
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, StringConstraints

from ilastik.applets.base.appletSerializer.legacyClassifiers import (
    deserialize_classifier,
    deserialize_classifier_factory,
)
from ilastik.applets.base.appletSerializer.serializerUtils import deserialize_string_from_h5
from ilastik.experimental.parser._h5helpers import (
    deserialize_arraylike_from_h5,
    deserialize_axistags_from_h5,
    deserialize_label_block_from_h5,
    deserialize_str_list_from_h5,
)
from ilastik.experimental.parser.types.base import LabelBlock, VigraAxisTags
from lazyflow.classifiers import LazyflowVectorwiseClassifierABC, LazyflowVectorwiseClassifierFactoryABC

BlockName = Annotated[str, StringConstraints(pattern=r"block\d{4}")]
LaneName = Annotated[str, StringConstraints(pattern=r"lane\d{4}")]
LaneNameLabel = Annotated[str, StringConstraints(pattern=r"labels\d{3}")]
LaneNameNoPrefix = Annotated[str, StringConstraints(pattern=r"\d{4}")]
NDShape = Annotated[Tuple[int, ...], annotated_types.Len(2, 6)]

RELATIVE_CLASS = "RelativeFilesystemDatasetInfo"
ABSOLUTE_CLASS = "FilesystemDatasetInfo"


class ILPLocationAware(BaseModel):
    def model_post_init(self, __context):
        self._ilp_file = __context["ilp_file"]

    @property
    def ilp(self):
        return self._ilp_file


class ILPBase(BaseModel):
    def model_dump_hdf5(
        self,
        h5group: h5py.Group,
        *,
        mode: Literal["hdf5"] = "hdf5",
        include=None,
        exclude=None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: bool = True,
    ) -> h5py.Group:
        python_model = super().model_dump(
            mode="python",
            include=include,
            exclude=exclude,
            by_alias=True,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            round_trip=round_trip,
            warnings=warnings,
        )

        write_level(h5group, python_model)
        return h5group


class DatasetInfo(BaseModel):
    axistags: Annotated[List[VigraAxisTags], BeforeValidator(deserialize_axistags_from_h5)]
    allow_labels: Annotated[bool, BeforeValidator(lambda x: bool(x))] = Field(alias="allowLabels")
    classname: Annotated[
        Literal["ProjectInternalDatasetInfo", "FilesystemDatasetInfo", "RelativeFilesystemDatasetInfo"],
        BeforeValidator(deserialize_string_from_h5),
    ] = Field(alias="__class__")
    dataset_id: Annotated[str, BeforeValidator(deserialize_string_from_h5)] = Field(alias="datasetId")
    display_mode: Annotated[
        Literal["default", "grayscale", "rgba", "random-colortable", "alpha-modulated", "binary-mask"],
        BeforeValidator(deserialize_string_from_h5),
    ]
    file_path: Annotated[Path, BeforeValidator(deserialize_string_from_h5)] = Field(alias="filePath")
    location: Annotated[Literal["FileSystem", "ProjectInternal"], BeforeValidator(deserialize_string_from_h5)]
    nickname: Annotated[str, BeforeValidator(deserialize_string_from_h5)]
    normalize_display: Annotated[bool, BeforeValidator(lambda x: bool(x))] = Field(alias="normalizeDisplay")
    scale_locked: Annotated[bool, BeforeValidator(lambda x: bool(x))] = Field(default=False)
    shape: Annotated[
        NDShape, BeforeValidator(lambda x: tuple(x.tolist())), BeforeValidator(deserialize_arraylike_from_h5)
    ]
    working_scale: Annotated[str, BeforeValidator(deserialize_string_from_h5)] = Field(default="")


class InputData(BaseModel):
    role_names: Annotated[List[str], BeforeValidator(deserialize_str_list_from_h5)] = Field(alias="Role Names")
    infos: OrderedDict[
        LaneName, Dict[str, Annotated[Optional[DatasetInfo], BeforeValidator(lambda x: None if len(x) == 0 else x)]]
    ]

    @property
    def _last_lane(self):
        last_lane_name = next(reversed(self.infos))
        return self.infos[last_lane_name]

    @property
    def axis_order(self) -> str:
        """Returns the axis keys of the last lane as a string"""
        last_lane = self._last_lane
        base_role_name = self.role_names[0]  # should usually be 'Raw Data'
        base_info = last_lane[base_role_name]
        assert base_info
        return "".join(ax.key for ax in base_info.axistags)

    @property
    def num_channels(self) -> int:
        """Returns the number for channels in the last lane"""
        last_lane = self._last_lane
        base_role_name = self.role_names[0]  # should usually be 'Raw Data'
        base_info = last_lane[base_role_name]
        assert base_info
        n_channels = 1
        for ind, at in enumerate(base_info.axistags):
            if at.key == "c":
                n_channels = base_info.shape[ind]
                break
        return n_channels

    @property
    def spatial_axes(self):
        return "".join(ax for ax in self.axis_order if ax in "xyz")


class FeatureMatrix(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )
    compute_in_2d: Annotated[npt.NDArray[numpy.bool_], BeforeValidator(deserialize_arraylike_from_h5)] = Field(
        alias="ComputeIn2d"
    )
    feature_ids: Annotated[List[str], BeforeValidator(deserialize_arraylike_from_h5)] = Field(alias="FeatureIds")
    scales: Annotated[List[float], BeforeValidator(deserialize_arraylike_from_h5)] = Field(alias="Scales")
    selections: Annotated[npt.NDArray[numpy.bool_], BeforeValidator(deserialize_arraylike_from_h5)] = Field(
        alias="SelectionMatrix"
    )
    storage_version: Annotated[str, BeforeValidator(deserialize_string_from_h5)] = Field(alias="StorageVersion")


class PixelClassification(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    bookmarks: OrderedDict[LaneNameNoPrefix, Annotated[bytes, BeforeValidator(lambda x: x[()].tobytes())]] = Field(
        alias="Bookmarks"
    )
    """Values of this dict are pickled list probably, not really used in ilastik currently, deserializing as binary string"""
    classifier: Annotated[
        LazyflowVectorwiseClassifierABC,
        BeforeValidator(deserialize_classifier),
    ] = Field(alias="ClassifierForests")
    classifier_factory: Annotated[
        LazyflowVectorwiseClassifierFactoryABC, BeforeValidator(deserialize_classifier_factory)
    ] = Field(alias="ClassifierFactory")
    label_colors: Annotated[npt.NDArray[numpy.int64], BeforeValidator(deserialize_arraylike_from_h5)] = Field(
        alias="LabelColors"
    )
    label_names: List[str] = Field(alias="LabelNames")
    label_sets: OrderedDict[
        LaneNameLabel, OrderedDict[BlockName, Annotated[LabelBlock, BeforeValidator(deserialize_label_block_from_h5)]]
    ] = Field(alias="LabelSets")
    pmap_colors: Annotated[npt.NDArray[numpy.int64], BeforeValidator(deserialize_arraylike_from_h5)] = Field(
        alias="PmapColors"
    )
    storage_version: Annotated[str, BeforeValidator(deserialize_string_from_h5)] = Field(alias="StorageVersion")

    @property
    def label_count(self) -> int:
        return len(self.label_names)
