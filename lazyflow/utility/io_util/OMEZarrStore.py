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
from dataclasses import dataclass
import json
import logging
import math
import os
from collections import OrderedDict
from typing import Dict, List, Optional, Union, Literal, Tuple, Any
from urllib.parse import unquote_to_bytes

import jsonschema
import vigra
from aiohttp import ClientConnectorError
from zarr.core import Array as ZarrArray
from zarr.storage import FSStore, LRUStoreCache

from lazyflow import rtype
from lazyflow.utility import Timer, Memory
from lazyflow.utility.io_util.multiscaleStore import MultiscaleStore, DEFAULT_SCALE_KEY

logger = logging.getLogger(__name__)

OME_ZARR_V_0_4_KWARGS = dict(dimension_separator="/", normalize_keys=False)
OME_ZARR_V_0_1_KWARGS = dict(dimension_separator=".")

OME_ZARR_DATASET = Dict[Literal["path", "coordinateTransformations"], Any]  # single dataset (= scale)
OME_ZARR_MULTISCALE = Dict[  # single multiscales entry of a json-validated OME-Zarr zattrs (any version)
    # The spec allows for multiple multiscales, but in practice we only ever see one.
    Literal["axes", "datasets", "version", "coordinateTransformations", "name"],
    Union[List[Dict], List[OME_ZARR_DATASET], str],
]
OME_ZARR_SPEC = Dict[Literal["multiscales"], List[OME_ZARR_MULTISCALE]]  # json-validated OME-Zarr zattrs (any version)
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


class NotAnOMEZarrMultiscale(ValueError):
    pass


class InvalidTransformationError(ValueError):
    pass


@dataclass(frozen=True)
class OMEZarrCoordinateTransformation:
    """Used by OME-Zarr export to adjust export metadata according to input."""

    type: Literal["scale", "translation"]
    values: Optional[List[float]]

    @classmethod
    def from_json(cls, json_data: Dict) -> "OMEZarrCoordinateTransformation":
        """Expected dicts look like
        {
          "type": Literal["scale", "translation"]
          and EITHER "scale": List[number] OR "translation": List[number]
        }
        Unfortunately, the spec is internally inconsistent, so there is a chance that we may encounter
        a coordinateTransformation with a "path" key instead of "scale" or "translation"; and possibly
        coordinateTransformations with "type": "identity".
        Afaik, none of the more popular converters/writers do this.
        """
        if (
            json_data["type"] not in ("scale", "translation")
            or ("scale" not in json_data and "translation" not in json_data)
            or "path" in json_data
        ):
            raise InvalidTransformationError()
        # Could raise KeyError for real nonsense like {"type": "scale", "translation": [0, 0]}
        return cls(type=json_data["type"], values=json_data[json_data["type"]])


# tuple(scale_transform, Optional[translation_transform])
ValidTransformations = Tuple[OMEZarrCoordinateTransformation, Optional[OMEZarrCoordinateTransformation]]
TransformationsOrError = Union[ValidTransformations, InvalidTransformationError]


def _validate_transforms(
    coordinate_transformations: Optional[List[Dict[str, Union[str, List[float]]]]],
) -> Union[None, ValidTransformations, InvalidTransformationError]:
    """
    Resolves the OME-Zarr spec's inconsistency in the coordinateTransformations field.
    Avoids raising errors because valid metadata are not required to load and work with the data.
    Distinguishes between None and invalid transformations so that caller can warn on the latter.
    Returns:
    - None if input was None (allowed for multiscale_transformations)
    - Tuple of scale transform and optionally translation transform if valid
    - InvalidTransformationError if invalid (e.g. not None but also no scale transform present)
    Inattentive writers might produce invalid transforms, depending on what part of the spec they read.
    The Transformations spec [1] allows for "identity" transforms and arbitrary numbers of transforms,
    but the Multiscales spec [2] only allows exactly one "scale", optionally followed by one "translation"
    transform.
    The "official" validator's schema [3] implements neither of these rules exactly :) It instead allows
    for exactly one "scale" transform, plus an arbitrary number of "translation" transforms, in any order.
    But this, plus the example at the start of the OME-Zarr spec, make a clear enough indicator that
    "one scale + one optional translation" is the convention, and all public datasets conform to this.
    To be graceful, we'll accept the first scale and translation.
    [1] https://ngff.openmicroscopy.org/latest/index.html#trafo-md
    [2] https://ngff.openmicroscopy.org/latest/index.html#multiscale-md
    [3] https://github.com/ome/ngff/blob/1383ce6218539baf9fe4350c46d992f2dbfe7af1/0.4/schemas/image.schema#L167
    """
    if coordinate_transformations is None:
        return None
    if not isinstance(coordinate_transformations, list) or not coordinate_transformations:
        return InvalidTransformationError()
    scale_transform = translation_transform = None
    for t in coordinate_transformations:
        try:
            transform = OMEZarrCoordinateTransformation.from_json(t)
        except (InvalidTransformationError, KeyError):
            continue
        if scale_transform is None and transform.type == "scale":
            scale_transform = transform
        if translation_transform is None and transform.type == "translation":
            translation_transform = transform
    return (scale_transform, translation_transform) if scale_transform else InvalidTransformationError()


@dataclass(frozen=True)
class OMEZarrMultiscaleMeta:
    """
    Specifically for metadata that ilastik does _not_ use internally.
    It is used for porting metadata from an OME-Zarr input to export.
    """

    axis_units: OrderedDict[Literal["t", "c", "z", "y", "x"], Optional[str]]  # { axis_key: axis_unit }
    multiscale_name: Optional[str]
    multiscale_transformations: Optional[TransformationsOrError]
    dataset_transformations: OrderedDict[str, TransformationsOrError]  # { scale_key: transformations }

    @classmethod
    def from_multiscale_spec(cls, multiscale_spec: OME_ZARR_MULTISCALE) -> "OMEZarrMultiscaleMeta":
        if "axes" in multiscale_spec and "name" in multiscale_spec["axes"][0]:
            # In v0.4 OME-Zarr attrs, we might also receive units for each axis
            axis_units = OrderedDict([(a["name"], a.get("unit")) for a in multiscale_spec["axes"]])
        else:
            axis_units = OrderedDict([(tag.key, None) for tag in _axistags_from_multiscale(multiscale_spec)])
        invalid_transformations = []  # Ensure dataset transformations are never None (either valid or error)
        return cls(
            axis_units=axis_units,
            multiscale_name=multiscale_spec.get("name"),
            multiscale_transformations=_validate_transforms(multiscale_spec.get("coordinateTransformations")),
            dataset_transformations=OrderedDict(
                [
                    (
                        scale["path"],
                        _validate_transforms(scale.get("coordinateTransformations", invalid_transformations)),
                    )
                    for scale in multiscale_spec["datasets"]
                ]
            ),
        )


def _axistags_from_multiscale(multiscale: OME_ZARR_MULTISCALE) -> vigra.AxisTags:
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


def _get_multiscale_for_dataset(ome_spec: OME_ZARR_SPEC, dataset_subpath: str) -> OME_ZARR_MULTISCALE:
    for multiscale in ome_spec["multiscales"]:
        if any(d["path"] == dataset_subpath for d in multiscale["datasets"]):
            return multiscale
    raise KeyError(f"Could not find metadata entry for sub-path {dataset_subpath} in metadata:\n{ome_spec}.")


def _get_zarr_cache_max_size() -> int:
    caches_max = Memory.getAvailableRamCaches()
    # Given that the only benefit of this cache is to prevent downloading the same file repeatedly for multiple
    # blocks, it shouldn't need to be huge. 1/8 might be a reasonable default for now.
    # Should see if we can implement a managed cache on top of this and use cacheMemoryManager to share the global pool.
    permissible_fraction_max = 0.125
    return math.floor(caches_max * permissible_fraction_max)


def _fetch_and_validate_ome_zarr_spec(uri: str) -> OME_ZARR_SPEC:
    """Fetch uri/.zattrs and validate it against OME-Zarr spec."""
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
            raise NotAnOMEZarrMultiscale(
                f"Expected an OME-Zarr store, but could not find metadata at {uri}/.zattrs."
            ) from e
        else:
            raise e
    try:
        jsonschema.validate(spec, SPEC_SCHEMA)
    except jsonschema.ValidationError as e:
        err_msg = (
            "Metadata for this store did not match OME-Zarr spec, "
            "or reports no multiscale datasets. Details below."
            f"\nMetadata read from {uri}/.zattrs."
            f"\n\nProblematic metadata entry: {e.json_path}"
            f"\nProblem: {e.message}"
            f"\nRequired properties: {e.schema}"
            f"\nFull metadata received:\n{spec}"
        )
        raise NotAnOMEZarrMultiscale(err_msg)
    return spec


def _introspect_for_multiscales_root(uri: str) -> Tuple[OME_ZARR_SPEC, str, Optional[str]]:
    """URI may point to an OME-Zarr multiscale root or to a specific scale.
    Try to find OME-Zarr spec first at URI, then search parent directories.
    Returns spec and root URI of the validated multiscales spec, and scale sub-URI (if any)"""
    uri = uri.rstrip("/")
    try:
        return _fetch_and_validate_ome_zarr_spec(uri), uri, None
    except NotAnOMEZarrMultiscale:
        parent_dirs = uri.split("/")[:-1]
        for i, parent in enumerate(reversed(parent_dirs)):
            uri_to_parent = "/".join(uri.split("/")[: -(i + 1)])
            try:
                return (
                    _fetch_and_validate_ome_zarr_spec(uri_to_parent),
                    uri_to_parent,
                    uri[len(uri_to_parent) :].lstrip("/"),
                )
            except NotAnOMEZarrMultiscale:
                continue
        raise  # If no multiscales spec found at URI or any parent, raise the original exception


class OMEZarrStore(MultiscaleStore):
    """
    Adapter class to handle communication with a source serving a dataset in OME-Zarr format.

    :param uri:  This may be a URI pointing to
        - an OME-Zarr multiscale root (e.g. "file:///path/to/my.ome.zarr"),
        - or to a specific scale (e.g. "file:///path/to/my.ome.zarr/s1")
    :param target_scale:
        In case a store has multiple multiscales, this determines which multiscale to use.
        In single_scale_mode, this also determines which scale to load.
        If uri points to a specific scale, but target_scale is also given, target_scale is used.
    :param single_scale_mode:
        If True, only the first scale is loaded to determine the dtype. Used to shorten init time
        when DatasetInfo instantiates a standalone OpInputDataReader to get lane shape and dtype.
    """

    NAME = "OME-Zarr"
    URI_HINT = 'URL contains "zarr"'

    def __init__(self, uri: str, target_scale: Optional[str] = None, single_scale_mode: bool = False):
        self._ome_spec, self.base_uri, self.scale_sub_path = _introspect_for_multiscales_root(uri)
        selected_scale = target_scale or self.scale_sub_path
        if len(self._ome_spec["multiscales"]) > 1 and not selected_scale:
            warn = (
                "The OME-Zarr store contains more than one multiscale dataset. "
                "The first multiscale will be used."
                "\nYou can select another multiscale by entering a URL pointing "
                "directly to one of its dataset paths."
                f"\nReceived metadata:\n{self._ome_spec}"
            )
            logger.warning(warn)
        multiscale_spec = (
            _get_multiscale_for_dataset(self._ome_spec, selected_scale)
            if selected_scale
            else self._ome_spec["multiscales"][0]
        )
        axistags = _axistags_from_multiscale(multiscale_spec)
        datasets = multiscale_spec["datasets"]
        if multiscale_spec["version"] == "0.1":
            uncached_store = FSStore(self.base_uri, mode="r", **OME_ZARR_V_0_1_KWARGS)
        else:
            uncached_store = FSStore(self.base_uri, mode="r", **OME_ZARR_V_0_4_KWARGS)
        # There is an additional block cache in front of OpOMEZarrMultiscaleReader, so e.g. when
        # the user scrolls across z back and forth, this does not trigger requests to the store.
        # But blocks can be misaligned with file size in the store. This cache can prevent downloading
        # the same file repeatedly for multiple blocks.
        self._store = LRUStoreCache(uncached_store, max_size=_get_zarr_cache_max_size())
        dtype = None
        scale_metadata = OrderedDict()  # Becomes slot metadata -> must be serializable (no ZarrArray allowed)
        self._scale_data = {}
        if single_scale_mode:  # One scale is enough to get dtype
            datasets = [d for d in datasets if d["path"] == selected_scale] if selected_scale else datasets[:1]
        for scale in datasets:  # OME-Zarr spec requires datasets ordered from high to low resolution
            with Timer() as timer:
                scale_key = scale["path"]
                # Loading a ZarrArray at this path is necessary to obtain the scale dimensions for the GUI
                zarray = ZarrArray(store=self._store, path=scale_key)
                dtype = zarray.dtype.type
                scale_metadata[scale_key] = OrderedDict(zip([tag.key for tag in axistags], zarray.shape))
                self._scale_data[scale_key] = {
                    "zarray": zarray,
                    "chunks": zarray.chunks,
                    "shape": zarray.shape,
                }
                logger.info(f"Initializing scale {scale_key} took {timer.seconds()*1000} ms.")
        self.ome_meta_for_export = OMEZarrMultiscaleMeta.from_multiscale_spec(multiscale_spec)
        super().__init__(
            dtype=dtype,
            axistags=axistags,
            multiscales=scale_metadata,
            lowest_resolution_key=list(scale_metadata.keys())[-1],
            highest_resolution_key=list(scale_metadata.keys())[0],
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
