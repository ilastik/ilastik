import json
import logging
from typing import Optional, Dict

import jsonschema
import vigra
from zarr.core import Array as ZarrArray
from zarr.storage import FSStore, LRUStoreCache

from lazyflow import rtype
from lazyflow.utility import Timer
from lazyflow.utility.io_util.multiscaleStore import MultiscaleStore, Multiscale, DEFAULT_LOWEST_SCALE_KEY

logger = logging.getLogger(__name__)

OME_ZARR_V_0_4_ARGS = {
    "dimension_separator": "/",
    "normalize_keys": False,
}
OME_ZARR_V_0_1_ARGS = {
    "dimension_separator": ".",
}


def _get_ome_spec_version(metadata: dict) -> Optional[str]:
    """
    https://github.com/ome/ome-zarr-py/blob/master/ome_zarr/format.py#L69
    Checks the metadata dict for a version

    Returns the version of the first object found in the metadata,
    checking for 'multiscales', 'plate', 'well' etc
    """
    multiscales = metadata.get("multiscales", [])
    if multiscales:
        dataset = multiscales[0]
        return dataset.get("version", None)
    for name in ["plate", "well", "image-label"]:
        obj = metadata.get(name, {})
        if obj:
            return obj.get("version", None)
    return None


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
    Adapter class to handle communication with a web source serving a dataset in OME-Zarr format.
    """

    NAME = "OME-Zarr"
    URL_HINT = 'URL contains "zarr"'

    spec_schema = {
        "type": "object",
        "properties": {
            "multiscales": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "axes": {"type": "array"},
                        "datasets": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {"path": {"type": "string"}},
                                "required": ["path"],
                            },
                        },
                    },
                    "required": ["datasets"],
                },
            },
        },
        "required": ["multiscales"],
    }

    def __init__(self, url: str = "", last_scale_only_mode: bool = False):
        with Timer() as timer:
            self.url = url
            uncached_store = FSStore(self.url, mode="r", **OME_ZARR_V_0_4_ARGS)
            try:
                self.ome_spec = json.loads(uncached_store[".zattrs"])
            except KeyError:
                raise ValueError("Expected a Zarr store, but could not find .zattrs file at the address.")
            if _get_ome_spec_version(self.ome_spec) == "0.1":
                uncached_store = FSStore(self.url, mode="r", **OME_ZARR_V_0_1_ARGS)
            self._store = LRUStoreCache(uncached_store, max_size=None)
            logger.info(f"Initializing OME-Zarr store at {url} took {timer.seconds()*1000} ms.")
        try:
            jsonschema.validate(self.ome_spec, self.spec_schema)
        except jsonschema.ValidationError:
            raise ValueError(f"Metadata for this dataset did not match OME-Zarr spec.\nReceived:\n{self.ome_spec}.")
        multiscale_spec = self.ome_spec["multiscales"][0]
        axistags = _get_axistags_from_spec(multiscale_spec)
        datasets = multiscale_spec["datasets"]
        assert len(datasets) > 0, "The OME-Zarr store contains no datasets."
        dtype = None
        gui_scale_metadata = {}  # Becomes slot metadata -> must be serializable (no ZarrArray allowed)
        self._scale_data = {}
        for scale in reversed(datasets):
            with Timer() as timer:
                zarray = ZarrArray(store=self._store, path=scale["path"])
                dtype = zarray.dtype.type
                gui_scale_metadata[scale["path"]] = Multiscale(
                    key=scale["path"], resolution=list(zarray.shape[-1:-4:-1])  # xyz
                )
                self._scale_data[scale["path"]] = {
                    "zarray": zarray,
                    "chunks": zarray.chunks,
                    "shape": zarray.shape,
                }
                logger.info(f"Initializing scale {scale['path']} took {timer.seconds()*1000} ms.")
            if last_scale_only_mode:
                break  # One scale is enough to get dtype
        super().__init__(
            dtype=dtype,
            axistags=axistags,
            multiscales=gui_scale_metadata,
            lowest_resolution_key=datasets[-1]["path"],
            highest_resolution_key=datasets[0]["path"],
        )

    @staticmethod
    def is_url_compatible(url: str) -> bool:
        return "zarr" in url

    def get_chunk_size(self, scale_key=DEFAULT_LOWEST_SCALE_KEY):
        scale_key = scale_key if scale_key else self.lowest_resolution_key
        return self._scale_data[scale_key]["chunks"]

    def get_shape(self, scale_key=DEFAULT_LOWEST_SCALE_KEY):
        scale_key = scale_key if scale_key else self.lowest_resolution_key
        return self._scale_data[scale_key]["shape"]

    def request(self, roi: rtype.Roi, scale_key=DEFAULT_LOWEST_SCALE_KEY):
        scale_key = scale_key if scale_key else self.lowest_resolution_key
        with Timer() as timer:
            data = self._scale_data[scale_key]["zarray"][roi.toSlice()]
            logger.info(f"Requesting roi {roi} from scale {scale_key} took {timer.seconds()*1000} ms.")
        return data
