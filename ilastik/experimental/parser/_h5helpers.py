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
import numbers
from typing import Any, List, Union

import h5py

from ilastik.applets.base.appletSerializer.serializerUtils import deserialize_string_from_h5


def deserialize_str_list_from_h5(str_list: h5py.Dataset) -> List[str]:
    return [x.decode() for x in str_list]


def deserialize_axistags_from_h5(ds: h5py.Dataset) -> dict[str, Union[float, int, str]]:
    return json.loads(deserialize_string_from_h5(ds))["axes"]


def deserialize_arraylike_from_h5(ds: h5py.Dataset) -> Any:
    return ds[()]


def ensure_encoded(val: Union[str, bytes]) -> bytes:
    if isinstance(val, str):
        val = val.encode("utf-8")

    return val


def write_level(group, dict_repr):
    for k, v in dict_repr.items():
        if isinstance(v, dict):
            new_group = group.create_group(k)

            write_level(new_group, v)
            continue
        # TODO: check optional inputs, these should be empty dicts, not None
        if v is None:
            new_group = group.create_group(k)
            continue

        if isinstance(v, (str, bytes)):
            group.create_dataset(name=k, data=ensure_encoded(v))
        elif isinstance(v, (list, tuple)):
            data = []
            for val in v:
                if isinstance(val, (str, bytes)):
                    data.append(ensure_encoded(val))
                else:
                    data.append(val)

            group.create_dataset(name=k, data=v)
        elif isinstance(v, numbers.Number):
            group.create_dataset(name=k, data=v)
        else:
            raise ValueError(f"No clue how to serialize {v} of {type(v)=} to hdf5.")

    return group
