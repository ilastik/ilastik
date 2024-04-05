###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2024, the ilastik developers
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
import json
from typing import Any, List, Union

import h5py

from ilastik.applets.base.appletSerializer.serializerUtils import deserialize_string_from_h5


def deserialize_str_list_from_h5(str_list: h5py.Dataset) -> List[str]:
    return [x.decode() for x in str_list]


def deserialize_axistags_from_h5(ds: h5py.Dataset) -> dict[str, Union[float, int, str]]:
    return json.loads(deserialize_string_from_h5(ds))["axes"]


def deserialize_arraylike_from_h5(ds: h5py.Dataset) -> Any:
    return ds[()]
