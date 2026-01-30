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
from dataclasses import dataclass
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    import numpy
    import numpy.typing as npt


@dataclass
class VigraAxisTags:
    key: str
    typeFlags: int
    resolution: int
    description: str


@dataclass
class LabelBlock:
    axistags: List[VigraAxisTags]
    block_slice: str
    label_data: "npt.NDArray[numpy.int64]"
