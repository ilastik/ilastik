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
from typing import Annotated, List, Tuple

import annotated_types
from pydantic import BaseModel, BeforeValidator, StringConstraints


from ilastik.experimental.parser._h5helpers import (
    deserialize_arraylike_from_h5,
    deserialize_axistags_from_h5,
)

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
