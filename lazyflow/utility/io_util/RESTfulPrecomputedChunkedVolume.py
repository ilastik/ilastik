import logging


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
        'type': 'object',
        'properties': {
            'type': {
                'type': 'string',
                'enum': ['image', 'segmentation']
            },
            'data_type': {
                'type': 'string',
                'enum': ['uint8', 'uint16', 'uint32', 'uint64', 'float32'],
            },
            'num_channels': {
                'type': "number"
            },
            'scales': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'key': {
                            'type': 'string'
                        },
                    }
                },
            },
        },
        'required': ['type', 'data_type', 'num_channels', 'scales']
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
        self._use_scale = '1_1_1'
        self.tmp_data_file = tmp_data_file
        self.volume_url = volume_url

        # Assuming axes and dtype will be the same in every scale
        # neuroglancer axes are always in this order; channel axis might singleton
        self.axes = 'czyx'
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
        pass

    def get_block_shape(self, scale=None):
        pass

    def get_resolution(self, scale=None):
        pass

    def get_voxel_offset(self, scale=None):
        pass

    def get_encoding(self, scale=None):
        pass

    def get_shape(self, scale=None):
        pass

    def download_info(self):
        pass

    def download_block(self, block_coordinates, scale=None):
        """downloads a single block at a given scale

        Args:
            block_coordinates (iterable): start of the block, 'czyx' axistags
              assumed
            scale (string): key to desired scale
        """
        pass

    def generate_url(self, block_coordinates, scale=None):
        """Generate url to access a specific block


        Args:
            block_coordinates (ndarray): 2d array of voxel coordinates at the
              given scale; zyx order assumed! No channel!
            scale (ndarray): Description

        Returns:
            string: string to access a secific block


        """
        pass


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    volume_url = 'http://localhost:8080/precomputed/cremi'
    cvol = RESTfulPrecomputedChunkedVolume(volume_url=volume_url)
