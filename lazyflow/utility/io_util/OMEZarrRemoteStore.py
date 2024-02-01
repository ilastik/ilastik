import json
import logging
from typing import Optional

from zarr.core import Array as ZarrArray
from zarr.storage import FSStore

from lazyflow import rtype
from lazyflow.utility import Timer

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

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


class OMEZarrRemoteStore:
    """
    Adapter class to handle communication with a web source serving a dataset in OME-Zarr format.
    """

    def __init__(self, url: str = ""):
        with Timer() as timer:
            self.url = url
            self._store = FSStore(self.url, mode="r", **OME_ZARR_V_0_4_ARGS)
            self.ome_spec = json.loads(self._store[".zattrs"])
            if _get_ome_spec_version(self.ome_spec) == "0.1":
                self._store = FSStore(self.url, mode="r", **OME_ZARR_V_0_1_ARGS)
            logger.debug(f"Init store at {url} took {timer.seconds()*1000} ms.")

        self.axes = "tczyx"
        datasets = self.ome_spec["multiscales"][0]["datasets"]
        self.lowest_resolution_key = datasets[-1]["path"]
        self.highest_resolution_key = datasets[0]["path"]
        self._zarrays = {}
        self.scales = {}  # Becomes slot metadata -> must be serializable
        for scale in reversed(datasets):
            with Timer() as timer:
                zarray = ZarrArray(store=self._store, path=scale["path"])
                self.dtype = zarray.dtype.type
                self.scales[scale["path"]] = {
                    "resolution": list(zarray.shape[-1:-4:-1]),  # xyz
                    "chunks": zarray.chunks,
                    "shape": zarray.shape,
                }
                self._zarrays[scale["path"]] = zarray  # Not serializable -> can't be in self.scales
                logger.debug(f"Init scale {scale['path']} took {timer.seconds()*1000} ms.")

    def get_chunk_size(self, scale_key=""):
        scale_key = scale_key if scale_key else self.lowest_resolution_key
        return self.scales[scale_key]["chunks"]

    def get_shape(self, scale_key=""):
        scale_key = scale_key if scale_key else self.lowest_resolution_key
        return self.scales[scale_key]["shape"]

    def request(self, roi: rtype.Roi, scale_key=""):
        scale_key = scale_key if scale_key else self.lowest_resolution_key
        with Timer() as timer:
            data = self._zarrays[scale_key][roi.toSlice()]
            logger.debug(f"Request roi {roi} from scale {scale_key} took {timer.seconds()*1000} ms.")
        return data
