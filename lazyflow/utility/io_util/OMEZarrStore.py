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
# 		   http://ilastik.org/license.html
###############################################################################
import json
import logging
import os
from collections import OrderedDict
from typing import Dict
from urllib.parse import unquote_to_bytes

import jsonschema
import vigra
from zarr.core import Array as ZarrArray
from zarr.storage import FSStore, LRUStoreCache

from lazyflow import rtype
from lazyflow.utility import Timer
from lazyflow.utility.io_util.multiscaleStore import MultiscaleStore, DEFAULT_SCALE_KEY

logger = logging.getLogger(__name__)

OME_ZARR_V_0_4_KWARGS = dict(dimension_separator="/", normalize_keys=False)
OME_ZARR_V_0_1_KWARGS = dict(dimension_separator=".")


def _get_axistags_from_spec(ome_spec: Dict) -> vigra.AxisTags:
    if "axes" not in ome_spec:
        # v0.1 and v0.2 did not allow variable axes
        axis_keys = ["t", "c", "z", "y", "x"]
    else:
        ome_axes = ome_spec["axes"]
        assert isinstance(ome_axes, list), f"Expected axis information to be a list, received: {ome_axes}."
        if "name" not in ome_axes[0]:
            # v0.3: ['t', 'c', 'y', 'x']
            axis_keys = ome_axes
        else:
            # v0.4: spec["axes"] requires name, recommends type and unit; like:
            # [
            #   {'name': 'c', 'type': 'channel'},
            #   {'name': 'y', 'type': 'space', 'unit': 'nanometer'},
            #   {'name': 'x', 'type': 'space', 'unit': 'nanometer'}
            # ]
            axis_keys = [d["name"] for d in ome_axes]
    return vigra.defaultAxistags("".join(axis_keys))


class OMEZarrStore(MultiscaleStore):
    """
    Adapter class to handle communication with a source serving a dataset in OME-Zarr format.

    :param uri: URI of the OME-Zarr store.
    :param single_scale_mode:
        If True, only the first scale is loaded to determine the dtype. Used to shorten init time
        when DatasetInfo instantiates a standalone OpInputDataReader to get lane shape and dtype.
    """

    NAME = "OME-Zarr"
    URI_HINT = 'URL contains "zarr"'

    spec_schema = {
        "type": "object",
        "properties": {
            "multiscales": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "properties": {
                        "axes": {"type": "array"},
                        "datasets": {
                            "type": "array",
                            "minItems": 1,
                            "items": {
                                "type": "object",
                                "properties": {"path": {"type": "string"}},
                                "required": ["path"],
                            },
                        },
                        "version": {"type": "string"},
                    },
                    "required": ["datasets", "version"],
                },
            },
        },
        "required": ["multiscales"],
    }

    def __init__(self, uri: str = "", single_scale_mode: bool = False):
        if uri.startswith("file:"):
            # Zarr's FSStore implementation doesn't unescape file URLs before piping them to
            # the file system. We do it here the same way as in pathHelpers.uri_to_Path.
            # Primarily this is to deal with spaces in Windows paths (encoded as %20).
            uri = os.fsdecode(unquote_to_bytes(uri))
        with Timer() as timer:
            self.uri = uri
            uncached_store = FSStore(self.uri, mode="r", **OME_ZARR_V_0_4_KWARGS)
            try:
                self.ome_spec = json.loads(uncached_store[".zattrs"])
            except KeyError:
                raise ValueError("Expected a Zarr store, but could not find .zattrs file at the address.")
            if self.ome_spec.get("multiscales", [{}])[0].get("version") == "0.1":
                uncached_store = FSStore(self.uri, mode="r", **OME_ZARR_V_0_1_KWARGS)
            self._store = LRUStoreCache(uncached_store, max_size=None)
            logger.info(f"Initializing OME-Zarr store at {uri} took {timer.seconds()*1000} ms.")
        try:
            jsonschema.validate(self.ome_spec, self.spec_schema)
        except jsonschema.ValidationError:
            err = (
                f"Metadata for this store did not match OME-Zarr spec, "
                f"or reports no multiscale datasets.\nReceived:\n{self.ome_spec}."
            )
            raise ValueError(err)
        if len(self.ome_spec["multiscales"]) > 1:
            warn = (
                f"The OME-Zarr store contains more than one multiscale dataset. "
                f"The first dataset will be used.\nReceived metadata:\n{self.ome_spec}"
            )
            logger.warning(warn)
        multiscale_spec = self.ome_spec["multiscales"][0]
        axistags = _get_axistags_from_spec(multiscale_spec)
        datasets = multiscale_spec["datasets"]
        dtype = None
        gui_scale_metadata = OrderedDict()  # Becomes slot metadata -> must be serializable (no ZarrArray allowed)
        self._scale_data = {}
        for scale in datasets:  # OME-Zarr spec requires datasets ordered from high to low resolution
            with Timer() as timer:
                zarray = ZarrArray(store=self._store, path=scale["path"])
                dtype = zarray.dtype.type
                gui_scale_metadata[scale["path"]] = list(zarray.shape[-1:-4:-1])  # xyz
                self._scale_data[scale["path"]] = {
                    "zarray": zarray,
                    "chunks": zarray.chunks,
                    "shape": zarray.shape,
                }
                logger.info(f"Initializing scale {scale['path']} took {timer.seconds()*1000} ms.")
            if single_scale_mode:
                break  # One scale is enough to get dtype
        # Reverse so that GUI displays from low to high resolution
        gui_scale_metadata = OrderedDict(reversed(list(gui_scale_metadata.items())))
        super().__init__(
            dtype=dtype,
            axistags=axistags,
            multiscales=gui_scale_metadata,
            lowest_resolution_key=datasets[-1]["path"],
            highest_resolution_key=datasets[0]["path"],
        )

    @staticmethod
    def is_uri_compatible(uri: str) -> bool:
        return "zarr" in uri

    def get_chunk_size(self, scale_key=DEFAULT_SCALE_KEY):
        scale_key = scale_key if scale_key else self.lowest_resolution_key
        return self._scale_data[scale_key]["chunks"]

    def get_shape(self, scale_key=DEFAULT_SCALE_KEY):
        scale_key = scale_key if scale_key else self.lowest_resolution_key
        return self._scale_data[scale_key]["shape"]

    def request(self, roi: rtype.Roi, scale_key=DEFAULT_SCALE_KEY):
        scale_key = scale_key if scale_key else self.lowest_resolution_key
        data = self._scale_data[scale_key]["zarray"][roi.toSlice()]
        return data