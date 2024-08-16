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
import math
import os
from collections import OrderedDict
from typing import Dict, Optional, Literal, List
from urllib.parse import unquote_to_bytes

import jsonschema
import vigra
from aiohttp import ClientConnectorError
from zarr.core import Array as ZarrArray
from zarr.storage import FSStore, LRUStoreCache

from lazyflow import rtype
from lazyflow.utility import Timer, Memory
from lazyflow.utility.io_util.multiscaleStore import MultiscaleStore, DEFAULT_SCALE_KEY

OME_ZARR_SPEC = Dict[Literal["multiscales"], List[Dict]]  # Placeholder to denote a validated OME-Zarr spec / zattrs
SPEC_SCHEMA = {
    "type": "object",
    "properties": {
        "multiscales": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "properties": {
                    "axes": {
                        "type": "array",
                        "minItems": 2,
                        "maxItems": 5,
                        "items": {
                            "oneOf": [
                                {"type": "string"},
                                {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                    },
                                    "required": ["name"],
                                },
                            ]
                        },
                    },
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

logger = logging.getLogger(__name__)

OME_ZARR_V_0_4_KWARGS = dict(dimension_separator="/", normalize_keys=False)
OME_ZARR_V_0_1_KWARGS = dict(dimension_separator=".")


def get_ome_zarr_spec(uri: str) -> OME_ZARR_SPEC:
    """Fetches uri/.zattrs and validates it against OME-Zarr spec.
    Extracted from __init__ so that OpOMEZarrMultiscaleReader can use it to determine the multiscale_index
    that corresponds to a given dataset path."""
    if uri.startswith("file:"):
        # Zarr's FSStore implementation doesn't unescape file URLs before piping them to
        # the file system. We do it here the same way as in pathHelpers.uri_to_Path.
        # Primarily this is to deal with spaces in Windows paths (encoded as %20).
        uri = os.fsdecode(unquote_to_bytes(uri))
    store = FSStore(uri, mode="r")
    try:
        with Timer() as timer:
            spec = json.loads(store[".zattrs"])
            logger.info(f"Reading OME-Zarr metadata from {uri}/.zattrs took {timer.seconds()*1000} ms.")
    except Exception as e:
        # Connection problems on FSSpec side raise a ClientConnectorError wrapped in a KeyError
        if isinstance(e.__context__, ClientConnectorError):
            raise ConnectionError(f"Could not connect to {e.__context__.host}:{e.__context__.port}.") from e
        elif isinstance(e, KeyError):
            raise ValueError("Expected a Zarr store, but could not find .zattrs file at the address.") from e
        else:
            raise e
    try:
        jsonschema.validate(spec, SPEC_SCHEMA)
    except jsonschema.ValidationError as e:
        err_msg = (
            "Metadata for this store did not match OME-Zarr spec, "
            "or reports no multiscale datasets. Details below."
            f"\n\nProblematic metadata entry: {e.json_path}"
            f"\nProblem: {e.message}"
            f"\nRequired properties: {e.schema}"
            f"\nFull metadata received:\n{spec}"
        )
        raise ValueError(err_msg)
    return spec


def get_multiscale_index_for_sub_path(ome_spec: OME_ZARR_SPEC, sub_path: str) -> int:
    for i, scale in enumerate(ome_spec["multiscales"]):
        if any(d["path"] == sub_path for d in scale["datasets"]):
            return i
    raise KeyError(f"Could not find metadata entry corresponding to {sub_path=}.")


def get_axistags_for_sub_path(ome_spec: OME_ZARR_SPEC, sub_path: str) -> vigra.AxisTags:
    multiscale_index = get_multiscale_index_for_sub_path(ome_spec, sub_path)
    return _get_axistags_for_multiscale(ome_spec, multiscale_index)


def _get_axistags_for_multiscale(ome_spec: OME_ZARR_SPEC, multiscale_index: int) -> vigra.AxisTags:
    multiscale = ome_spec["multiscales"][multiscale_index]
    if "axes" in multiscale:
        ome_axes = multiscale["axes"]
        if "name" in ome_axes[0]:
            # v0.4: spec["axes"] requires name, recommends type and unit; like:
            # [
            #   {'name': 'c', 'type': 'channel'},
            #   {'name': 'y', 'type': 'space', 'unit': 'nanometer'},
            #   {'name': 'x', 'type': 'space', 'unit': 'nanometer'}
            # ]
            axis_keys = [d["name"] for d in ome_axes]
        else:
            # v0.3: ['t', 'c', 'y', 'x']
            axis_keys = ome_axes
    else:
        # v0.1 and v0.2 did not allow variable axes
        axis_keys = ["t", "c", "z", "y", "x"]
    return vigra.defaultAxistags("".join(axis_keys))


def _get_zarr_cache_max_size() -> int:
    caches_max = Memory.getAvailableRamCaches()
    # Given that the only benefit of this cache is to prevent downloading the same file repeatedly for multiple
    # blocks, it shouldn't need to be huge. 1/8 might be a reasonable default for now.
    # Should see if we can implement a managed cache on top of this and use cacheMemoryManager to share the global pool.
    permissible_fraction_max = 0.125
    return math.floor(caches_max * permissible_fraction_max)


class OMEZarrStore(MultiscaleStore):
    """
    Adapter class to handle communication with a source serving a dataset in OME-Zarr format.
    An OME-Zarr store can contain multiple multiscale collections (entries in the list under the
    "multiscales" key of the zattrs spec dict), each of which can contain multiple scales (datasets).

    :param uri: URI of the OME-Zarr store.
    :param multiscale_index: Which multiscale collection within the store to load. Default None (load first collection).
    :param single_scale_mode:
        If True, only metadata of the first scale is requested from server. Used to shorten init time when DatasetInfo
        instantiates a standalone OpInputDataReader to get lane shape and dtype. Default False (load all scales).
    """

    NAME = "OME-Zarr"
    URI_HINT = 'URL contains "zarr"'

    def __init__(self, uri: str, multiscale_index: Optional[int] = None, single_scale_mode: bool = False):
        self.ome_spec = get_ome_zarr_spec(uri)
        self.uri = uri
        if len(self.ome_spec["multiscales"]) > 1 and multiscale_index is None:
            warn = (
                f"The OME-Zarr store contains more than one multiscale dataset. "
                f"The first dataset will be used.\nReceived metadata:\n{self.ome_spec}"
            )
            logger.warning(warn)
        multiscale_index = multiscale_index or 0
        multiscale_spec = self.ome_spec["multiscales"][multiscale_index]
        axistags = _get_axistags_for_multiscale(self.ome_spec, multiscale_index)
        datasets = multiscale_spec["datasets"]
        if multiscale_spec["version"] == "0.1":
            uncached_store = FSStore(self.uri, mode="r", **OME_ZARR_V_0_1_KWARGS)
        else:
            uncached_store = FSStore(self.uri, mode="r", **OME_ZARR_V_0_4_KWARGS)
        # There is an additional block cache in front of OpOMEZarrMultiscaleReader, so e.g. when
        # the user scrolls across z back and forth, this does not trigger requests to the store.
        # But blocks can be misaligned with file size in the store. This cache can prevent downloading
        # the same file repeatedly for multiple blocks.
        self._store = LRUStoreCache(uncached_store, max_size=_get_zarr_cache_max_size())
        dtype = None
        gui_scale_metadata = OrderedDict()  # Becomes slot metadata -> must be serializable (no ZarrArray allowed)
        self._scale_data = {}
        if single_scale_mode:
            datasets = datasets[:1]  # One scale is enough to get dtype
        for scale in datasets:  # OME-Zarr spec requires datasets ordered from high to low resolution
            with Timer() as timer:
                scale_key = scale["path"]
                # Loading a ZarrArray at this path is necessary to obtain the scale dimensions for the GUI.
                # As a bonus, this also validates all scale["path"] strings passed outside this class.
                zarray = ZarrArray(store=self._store, path=scale_key)
                dtype = zarray.dtype.type
                gui_scale_metadata[scale_key] = list(zarray.shape[-1:-4:-1])  # xyz
                self._scale_data[scale_key] = {
                    "zarray": zarray,
                    "chunks": zarray.chunks,
                    "shape": zarray.shape,
                }
                logger.info(f"Initializing scale {scale_key} took {timer.seconds()*1000} ms.")
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
        scale_key = scale_key if scale_key != DEFAULT_SCALE_KEY else self.lowest_resolution_key
        return self._scale_data[scale_key]["chunks"]

    def get_shape(self, scale_key=DEFAULT_SCALE_KEY):
        scale_key = scale_key if scale_key != DEFAULT_SCALE_KEY else self.lowest_resolution_key
        return self._scale_data[scale_key]["shape"]

    def request(self, roi: rtype.Roi, scale_key=DEFAULT_SCALE_KEY):
        scale_key = scale_key if scale_key != DEFAULT_SCALE_KEY else self.lowest_resolution_key
        data = self._scale_data[scale_key]["zarray"][roi.toSlice()]
        return data

    def get_zarr_array(self, scale_key: str):
        """
        Intended exclusively for use through ilastik-API.
        Internally, ilastik and lazyflow should never directly access the ZarrArray.
        """
        if scale_key not in self._scale_data:
            msg = f"No scale named {scale_key} in this store. Please inspect `.multiscales` to see available scales."
            raise KeyError(msg)
        return self._scale_data[scale_key]["zarray"]
