###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2026, the ilastik developers
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
import json
from typing import Annotated, Any, List, Tuple, Union

import annotated_types
import h5py
from pydantic import BaseModel, BeforeValidator, StringConstraints

from ilastik.applets.base.appletSerializer.serializerUtils import deserialize_string_from_h5


def deserialize_str_list_from_h5(str_list: h5py.Dataset) -> List[str]:
    return [x.decode() for x in str_list]


def deserialize_axistags_from_h5(ds: h5py.Dataset) -> dict[str, Union[float, int, str]]:
    return json.loads(deserialize_string_from_h5(ds))["axes"]


def deserialize_arraylike_from_h5(ds: h5py.Dataset) -> Any:
    return ds[()]


NDShape = Annotated[Tuple[int, ...], annotated_types.Len(2, 6)]
LaneName = Annotated[str, StringConstraints(pattern=r"lane\d{4}")]


class VigraAxisTags(BaseModel):
    key: str
    typeFlags: int
    resolution: int
    description: str


class DatasetInfo(BaseModel):
    axistags: Annotated[List[VigraAxisTags], BeforeValidator(deserialize_axistags_from_h5)]
    shape: Annotated[
        NDShape, BeforeValidator(lambda x: tuple(x.tolist())), BeforeValidator(deserialize_arraylike_from_h5)
    ]
