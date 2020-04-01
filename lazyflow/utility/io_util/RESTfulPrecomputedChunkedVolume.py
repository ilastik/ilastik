###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2017, the ilastik developers
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
import jsonschema
import logging
import requests

import numpy

import lazyflow.roi


logger = logging.getLogger(__file__)


class RESTfulPrecomputedChunkedVolume(object):
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

    info_schema = {
        "type": "object",
        "properties": {
            "type": {"type": "string", "enum": ["image", "segmentation"]},
            "data_type": {"type": "string", "enum": ["uint8", "uint16", "uint32", "uint64", "float32"]},
            "num_channels": {"type": "number"},
            "scales": {"type": "array", "items": {"type": "object", "properties": {"key": {"type": "string"}}}},
        },
        "required": ["type", "data_type", "num_channels", "scales"],
    }

    def __init__(self, volume_url, tmp_data_file=None, n_threads=4):
        """
        Args:
            volume_url (string): base url of the precomputed volume.
              {base_url}/info should be reachable. The info file holds the json
              description of the volume. Will be validated against
              `self.info_schema`.
            tmp_data_file (string, optional): Data will be downloaded to a
              temporary hdf5 file. If `None`, a file will be generated in the
              temp-folder.
            n_threads (int, optional): number of concurrent downloads
        """
        # might come in handy if one wants to process data on a different scale.
        # ilastik can only process data at a single scale.
        self._scale_info = None
        self._json_info = None
        self._use_scale = "1_1_1"
        self.tmp_data_file = tmp_data_file
        self.volume_url = volume_url

        # Assuming axes and dtype will be the same in every scale
        # neuroglancer axes are always in this order; channel axis might singleton
        self.axes = "czyx"
        self.dtype = None
        self.n_channels = None

        if volume_url is not None:
            self._init_config()

    def _init_config(self, volume_url=None, volume_description=None):
        """Downloads and checks the volume info file

        Args:
            volume_url (string, optional): volume_url (see `self.__init__`). If
              supplied, the given volume is checked and set as volume for the
              instance. If not, `self.volume_url` is used.
        """
        if volume_url is not None:
            self.volume_url = volume_url

        if volume_description is None and self.volume_url is not None:
            self.download_info()
        else:
            self._json_info = volume_description

        jsonschema.validate(self._json_info, self.info_schema)
        _scale_info = {x["key"]: x for x in self._json_info["scales"]}

        # save json contents
        self._scale_info = _scale_info

        self._use_scale, resolution = self.determine_lowest_scale(_scale_info)

        self.available_scales = self._scale_info.keys()

        self.dtype = self._json_info["data_type"]
        self.npdtype = numpy.dtype(self.dtype)
        self.n_channels = self._json_info["num_channels"]

    @staticmethod
    def determine_lowest_scale(scales_info_dict):
        scales = scales_info_dict.keys()
        resolutions = [(scale, scales_info_dict[scale]["resolution"]) for scale in scales]
        # sort by x value of the resolution
        resolutions.sort(key=lambda x: x[1][0])
        lowest_scale = resolutions[0]
        logger.debug(f"using lowest scale {lowest_scale[0]}")
        return lowest_scale

    def get_block_shape(self, scale=None):
        if scale is None:
            scale = self._use_scale
        n_channels = self.n_channels
        block_shape = numpy.array([n_channels] + self._scale_info[scale]["chunk_sizes"][0][::-1])
        return block_shape

    def get_resolution(self, scale=None):
        if scale is None:
            scale = self._use_scale
        resolution = numpy.array(self._scale_info[scale]["resolution"][::-1])
        return resolution

    def get_voxel_offset(self, scale=None):
        if scale is None:
            scale = self._use_scale
        voxel_offset = numpy.array([0] + self._scale_info[scale]["voxel_offset"][::-1])
        return voxel_offset

    def get_encoding(self, scale=None):
        if scale is None:
            scale = self._use_scale
        encoding = self._scale_info[scale]["encoding"]
        return encoding

    def get_shape(self, scale=None):
        if scale is None:
            scale = self._use_scale
        n_channels = self.n_channels
        shape = numpy.array([n_channels] + self._scale_info[scale]["size"][::-1])
        return shape

    def download_info(self):
        logger.debug(f"getting volume from {self.volume_url}/info")
        r = requests.get(f"{self.volume_url}/info")

        # check if success:
        if r.status_code != 200:
            raise ValueError(f"Could not find info file at {self.volume_url}, status code {r.status_code}!")

        self._json_info = json.loads(r.content)

    def download_block(self, block_coordinates, scale=None):
        """downloads a single block at a given scale

        Args:
            block_coordinates (iterable): start of the block, 'czyx' axistags
              assumed
            scale (string): key identifying the scale to be used
        """
        if scale is None:
            scale = self._use_scale

        url, blockshape = self.generate_url(block_coordinates, scale)
        try:
            content = self.downloading(url)
        except requests.exceptions.ConnectionError:
            return numpy.zeros(shape=blockshape, dtype=self.dtype)
        return self.decode_content(content, encoding=self.get_encoding(scale), shape=blockshape, dtype=self.dtype)

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

    def generate_url(self, block_coordinates, scale=None):
        """Generate url to access a specific block


        Args:
            block_coordinates (ndarray): 2d array of voxel coordinates at the
              given scale; czyx
            scale (string): key identifying the scale to be used

        Returns:
            string: URL to access the block with the given block coordinates
        """
        if scale is None:
            scale = self._use_scale

        # block shape without channel
        shape = self.get_shape(scale)
        block_shape = self.get_block_shape(scale)
        coordinates = block_coordinates

        if not numpy.allclose(numpy.remainder(coordinates, block_shape), 0):
            raise ValueError(
                f"Supplied coordinates ({coordinates}) not a valid block- " "start for block shape {block_shape}."
            )

        base_url = self.volume_url
        min_values = coordinates
        max_values = min_values + block_shape
        max_values = numpy.min([shape, max_values], axis=0)
        downloaded_block_shape = max_values - min_values
        # ignore c -> [1::]
        min_z, min_y, min_x = min_values[1::]
        max_z, max_y, max_x = max_values[1::]

        url = f"{base_url}/{scale}/{min_x}-{max_x}_{min_y}-{max_y}_{min_z}-{max_z}"
        return url, downloaded_block_shape


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    volume_url = "http://localhost:8080/precomputed/cremi"
    cvol = RESTfulPrecomputedChunkedVolume(volume_url=volume_url)
    print(f"dtype: {cvol.dtype}")
    print(f"scales: {cvol.available_scales}")
    print(f"block_shape: {cvol.get_block_shape()}")
    print(f"shape: {cvol.get_shape()}")
    block_start = [1, 128, 64, 256]
    print(f"download_url for block {block_start}: {cvol.generate_url(block_start)}")
