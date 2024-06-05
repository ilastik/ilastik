###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2024, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the Lesser GNU General Public License
# as published by the Free Software Foundation; either version 2.1
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# See the files LICENSE.lgpl2 and LICENSE.lgpl3 for full text of the
# GNU Lesser General Public License version 2.1 and 3 respectively.
# This information is also available on the ilastik web site at:
#          http://ilastik.org/license/
###############################################################################
import json
import logging
from collections import OrderedDict

import jsonschema
import numpy
import requests
import vigra

from lazyflow.utility.io_util.multiscaleStore import MultiscaleStore, DEFAULT_LOWEST_SCALE_KEY

logger = logging.getLogger(__file__)


class RESTfulPrecomputedChunkedVolume(MultiscaleStore):
    """Class to access "precomputed" data in the neuroglancer style

    Precomputed volumes are saved chunk-wise, potentially at various scales.
    The description can be found at `http://url.to/image/info`, which is a json
    file. Information can be found here:

    https://github.com/google/neuroglancer/tree/master/src/neuroglancer/datasource/precomputed

    Does not inherit from RESTfulVolume as no functions could be shared.

    Note: didn't use cloud-volume (github.com/seung-lab/cloud-volume) because it
      introduces a lot of dependencies and fixed, different versions of packages
      we already use. If, however, we want to do more than just read a volume,
      we should consider switching, before implementing everything ourselves.

    Note: all code, except the setup code, will assume 'czyx' order of
      coordinates, shapes, rois.
    """

    NAME = "Neuroglancer Precomputed"
    URL_HINT = 'URL starts with "precomputed://"'

    info_schema = {
        "type": "object",
        "properties": {
            "type": {"type": "string", "enum": ["image", "segmentation"]},
            "data_type": {"type": "string", "enum": ["uint8", "uint16", "uint32", "uint64", "float32"]},
            "num_channels": {"type": "number"},
            "scales": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "key": {"type": "string"},
                        "resolution": {"type": "array", "items": {"type": "number"}},
                    },
                },
            },
        },
        "required": ["type", "data_type", "num_channels", "scales"],
    }

    def __init__(self, volume_url: str, n_threads=4):
        """
        Args:
            volume_url (string): base url of the precomputed volume.
              {base_url}/info should be reachable. The info file holds the json
              description of the volume. Will be validated against
              `self.info_schema`.
            n_threads (int, optional): number of concurrent downloads
        """
        axistags = vigra.defaultAxistags("czyx")  # neuroglancer axes are always czyx; channel might be singleton
        self._json_info = {}
        self.volume_url = volume_url
        self.base_url = volume_url.lstrip("precomputed://")
        self.n_channels = None

        self.download_info()
        jsonschema.validate(self._json_info, self.info_schema)

        dtype = self._json_info["data_type"]
        # Scales are ordered from original to most-downscaled in Precomputed spec
        lowest_resolution_key = self._json_info["scales"][-1]["key"]
        highest_resolution_key = self._json_info["scales"][0]["key"]
        # Reverse so that the ScaleComboBox shows the options ordered from most-downscaled to original
        gui_scale_metadata = OrderedDict(
            [(scale["key"], scale["resolution"]) for scale in reversed(self._json_info["scales"])]
        )
        self._scales = {scale["key"]: scale for scale in self._json_info["scales"]}
        self.n_channels = self._json_info["num_channels"]

        super().__init__(dtype, axistags, gui_scale_metadata, lowest_resolution_key, highest_resolution_key)

    @staticmethod
    def is_url_compatible(url: str) -> bool:
        return url.startswith("precomputed://")

    def get_chunk_size(self, scale=DEFAULT_LOWEST_SCALE_KEY):
        scale = scale if scale != DEFAULT_LOWEST_SCALE_KEY else self.lowest_resolution_key
        n_channels = self.n_channels
        block_shape = numpy.array([n_channels] + self._scales[scale]["chunk_sizes"][0][::-1])
        return block_shape

    def get_voxel_offset(self, scale=DEFAULT_LOWEST_SCALE_KEY):
        scale = scale if scale != DEFAULT_LOWEST_SCALE_KEY else self.lowest_resolution_key
        voxel_offset = numpy.array([0] + self._scales[scale]["voxel_offset"][::-1])
        return voxel_offset

    def get_encoding(self, scale=DEFAULT_LOWEST_SCALE_KEY):
        scale = scale if scale != DEFAULT_LOWEST_SCALE_KEY else self.lowest_resolution_key
        encoding = self._scales[scale]["encoding"]
        return encoding

    def get_shape(self, scale=DEFAULT_LOWEST_SCALE_KEY):
        scale = scale if scale != DEFAULT_LOWEST_SCALE_KEY else self.lowest_resolution_key
        n_channels = self.n_channels
        shape = numpy.array([n_channels] + self._scales[scale]["size"][::-1])
        return shape

    def download_info(self):
        logger.debug(f"getting volume from {self.base_url}/info")
        r = requests.get(f"{self.base_url}/info")

        # check if success:
        if r.status_code != 200:
            raise ValueError(f"Could not find info file at {self.base_url}, status code {r.status_code}!")

        self._json_info = json.loads(r.content)

    def download_block(self, block_coordinates, scale=DEFAULT_LOWEST_SCALE_KEY):
        """downloads a single block at a given scale

        Args:
            block_coordinates (iterable): start of the block, 'czyx' axistags
              assumed
            scale (int): index of the scale to be used
        """
        scale = scale if scale != DEFAULT_LOWEST_SCALE_KEY else self.lowest_resolution_key
        url, block_shape = self.generate_url(block_coordinates, scale)
        try:
            content = self.downloading(url)
        except requests.exceptions.ConnectionError:
            logger.warning(f"Could not download block from {url}. Returning empty image instead.")
            return numpy.zeros(shape=block_shape, dtype=self.dtype)
        return self.decode_content(content, encoding=self.get_encoding(scale), shape=block_shape, dtype=self.dtype)

    @classmethod
    def decode_content(cls, content, encoding, shape, dtype):
        """converts to numpy array according to self.encoding

        Args:
            content (string): encoding type: {'raw', 'jpg'}
              raw: is gz
        """
        logger.debug(f"decoding encoding {encoding}; dtype {dtype}")
        if encoding == "raw":
            raw = content
            arr = numpy.fromstring(raw, dtype=dtype).reshape(shape)
            return arr
        else:
            raise NotImplementedError(f"encoding {encoding} not supported :(")

    @staticmethod
    def downloading(url):
        logger.debug(f"requesting {url}")
        r = requests.get(url)
        return r.content

    def generate_url(self, block_coordinates, scale=DEFAULT_LOWEST_SCALE_KEY):
        """Generate url to access a specific block


        Args:
            block_coordinates (ndarray): 2d array of voxel coordinates at the
              given scale; czyx
            scale (int): index of the scale to be used

        Returns:
            string: URL to access the block with the given block coordinates
        """
        scale = scale if scale != DEFAULT_LOWEST_SCALE_KEY else self.lowest_resolution_key
        # block shape without channel
        shape = self.get_shape(scale)
        chunk_size = self.get_chunk_size(scale)
        coordinates = block_coordinates

        if not numpy.allclose(numpy.remainder(coordinates, chunk_size), 0):
            raise ValueError(
                f"Supplied coordinates ({coordinates}) not a valid block- start for block shape {chunk_size}."
            )

        base_url = self.base_url
        min_values = coordinates
        max_values = min_values + chunk_size
        max_values = numpy.min([shape, max_values], axis=0)
        downloaded_block_shape = max_values - min_values
        min_z, min_y, min_x = min_values[1:]  # ignore c
        max_z, max_y, max_x = max_values[1:]

        url = f"{base_url}/{scale}/{min_x}-{max_x}_{min_y}-{max_y}_{min_z}-{max_z}"
        return url, downloaded_block_shape

    def get_scales_list_legacy(self):
        """Returns the list of scales as they were used in ilastik 1.4.1b13."""
        return list(reversed(self._json_info["scales"]))


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    volume_url = "precomputed://http://localhost:8080/precomputed/cremi"
    cvol = RESTfulPrecomputedChunkedVolume(volume_url=volume_url)
    print(f"dtype: {cvol.dtype}")
    print(f"scales: {len(cvol.multiscales)}")
    print(f"block_shape: {cvol.get_chunk_size()}")
    print(f"shape: {cvol.get_shape()}")
    block_start = [1, 128, 64, 256]
    print(f"download_url for block {block_start}: {cvol.generate_url(block_start)}")
