import os
import numpy
import vigra
from functools import partial
from StringIO import StringIO

## Instead of importing requests and PIL here, 
## use late imports (below) so people who don't use TiledVolume don't have to have them

# New dependency: requests is way more convenient than urllib or httplib
#import requests

# Use PIL instead of vigra since it allows us to open images in-memory
#from PIL import Image

from lazyflow.utility.timer import Timer 
from lazyflow.utility.jsonConfig import JsonConfigParser, AutoEval, FormattedField
from lazyflow.roi import getIntersectingBlocks, getBlockBounds, roiToSlice, getIntersection

from lazyflow.request import Request, RequestPool

import logging
logger = logging.getLogger(__name__)

class TiledVolume(object):
    """
    Given a directory of image tiles that make up a volume, produces numpy array volumes for arbitrary roi requests.
    """
    #: These fields describe the schema of the description file.
    #: See the source code comments for a description of each field.    
    DescriptionFields = \
    {
        "_schema_name" : "tiled-volume-description",
        "_schema_version" : 1.0,

        "name" : str,
        "format" : str,
        "dtype" : AutoEval(),
        "bounds_zyx" : AutoEval(numpy.array), # Maximum coordinates (+1)
        
        "view_origin_zyx" : AutoEval(numpy.array), # Optional offset for output 'view'
        "view_shape_zyx" : AutoEval(numpy.array), # Shape of the output 'view'.  If not provided, defaults to bounds - origin

        "resolution_zyx" : AutoEval(numpy.array), 
        "tile_shape_2d_yx" : AutoEval(numpy.array),
        
        "is_rgb" : bool, # Indicates that we must convert to grayscale

        "username" : str,
        "password" : str,

        # This doesn't change how the data is read from the server,
        #  but instead specifies the indexing order of the numpy volumes produced.
        "output_axes" : str,

        "cache_tiles" : bool,

        # Offset not supported for now...
        #"origin_offset" : AutoEval(numpy.array),

        # For now we support 3D-only, sliced across Z (TODO: Support 5D?)

        # We allow multiple url schemes: tiles might be addressed via pixel coordinates or row/column indexing
        # (z_index and z_start are synonyms here -- either is allowed)
        # Example: pixel-wise tile names:
        #   "tile_url_format" : "http://my.tiles.org/my_tiles/{z_start}-{z_stop}/{y_start}-{y_stop}/{x_start}-{x_stop}.jpg"
        # Example: row/column-wise tile names
        #   "tile_url_format" : "http://my.tiles.org/my_tiles/{z_index}/{y_index}/{x_index}.jpg"

        # Also, local tile sources (filesystem, not http) are okay:
        # "tile_url_format" : "/my_hard_disk/my_tiles/{z_index}/{y_index}/{x_index}.jpg"
        "tile_url_format" : FormattedField( requiredFields=[],
                                            optionalFields=["x_start", "y_start", "z_start",
                                                            "x_stop",  "y_stop",  "z_stop",
                                                            "x_index", "y_index", "z_index",
                                                            "raveler_z_base"] ), # Special keyword for Raveler session directories.  See notes below.
        
        "invert_y_axis" : bool, # For raveler volumes, the y-axis coordinate is inverted.
        
        # A list of lists, mapping src slices to destination slices (for "filling in" missing slices)
        # Example If slices 101,102,103 are missing data, you might want to simply repeat the data from slice 100:
        # "extend_slices" : [ [100, [101, 102, 103]] ]
        "extend_slices" : list,
        
        # Some tiled volumes have complicated mappings from "real" or "global" coordinates to url/filepath coordinates.
        # This field will be eval()'d before the tile is retrieved
        # For example, if the slices were named according to their position in nanometers instead of pixels, this might do the trick:
        # "z_translation_function" : "lambda z: 40*z"
        "z_translation_function" : str,

        # Optional data transform.  For example:
        # "data_transform_function" : "lambda a: a == 0",
        "data_transform_function" : str
    }
    DescriptionSchema = JsonConfigParser( DescriptionFields )

    @classmethod
    def readDescription(cls, descriptionFilePath):
        # Read file
        description = TiledVolume.DescriptionSchema.parseConfigFile( descriptionFilePath )
        cls.updateDescription(description)
        return description

    @classmethod
    def updateDescription(cls, description):
        """
        Some description fields are optional.
        If they aren't provided in the description JSON file, then this function provides 
        them with default values, based on the other description fields.
        """
        # Augment with default parameters.
        logger.debug(str(description))

        if description.view_origin_zyx is None:
            description.view_origin_zyx = numpy.array( [0]*len(description.bounds_zyx) )
        
        if description.view_shape_zyx is None:
            description.view_shape_zyx = description.bounds_zyx - description.view_origin_zyx

        if not description.output_axes:
            description.output_axes = "zyx"
        assert description.output_axes is None or set(description.output_axes) == set("zyx"), \
            "Axis order must include x,y,z (and nothing else)"

        if not description.extend_slices:
            description.extend_slices = []
        
        if description.cache_tiles is None:
            description.cache_tiles = False

    def __init__( self, descriptionFilePath ):
        self.description = TiledVolume.readDescription( descriptionFilePath )
        self._session = None

        assert self.description.format in vigra.impex.listExtensions().split(), \
            "Unknown tile format: {}".format( self.description.format )
        
        assert self.description.tile_shape_2d_yx.shape == (2,)
        assert self.description.bounds_zyx.shape == (3,)
        assert self.description.view_shape_zyx.shape == (3,)

        shape_dict = dict( zip('zyx', self.description.view_shape_zyx) )
        self.output_shape = tuple( shape_dict[k] for k in self.description.output_axes )

        self._slice_remapping = {}
        for source, destinations in self.description.extend_slices:
            for dest in destinations:
                self._slice_remapping[dest] = source

    def close(self):
        if self._session:
            self._session.close()

    def read(self, view_roi, result_out):
        """
        roi: (start, stop) tuples, ordered according to description.output_axes
             roi should be relative to the view
        """
        output_axes = self.description.output_axes
        roi_transposed = zip(*view_roi)
        roi_dict = dict( zip(output_axes, roi_transposed) )
        view_roi = zip( *(roi_dict['z'], roi_dict['y'], roi_dict['x']) )

        # First, normalize roi and result to zyx order
        result_out = vigra.taggedView(result_out, output_axes)
        result_out = result_out.withAxes(*'zyx')
        
        assert numpy.array(view_roi).shape == (2,3), "Invalid roi for 3D volume: {}".format( view_roi )
        view_roi = numpy.array(view_roi)
        assert (result_out.shape == (view_roi[1] - view_roi[0])).all()
        
        # User gave roi according to the view output.
        # Now offset it find global roi.
        roi = view_roi + self.description.view_origin_zyx
        
        tile_blockshape = (1,) + tuple(self.description.tile_shape_2d_yx)
        tile_starts = getIntersectingBlocks( tile_blockshape, roi )

        pool = RequestPool()
        for tile_start in tile_starts:
            tile_roi_in = getBlockBounds( self.description.bounds_zyx, tile_blockshape, tile_start )
            tile_roi_in = numpy.array(tile_roi_in)

            # This tile's portion of the roi
            intersecting_roi = getIntersection( roi, tile_roi_in )
            intersecting_roi = numpy.array( intersecting_roi )

            # Compute slicing within destination array and slicing within this tile
            destination_relative_intersection = numpy.subtract(intersecting_roi, roi[0])
            tile_relative_intersection = intersecting_roi - tile_roi_in[0]
            
            # Get a view to the output slice
            result_region = result_out[roiToSlice(*destination_relative_intersection)]
            
            rest_args = self._get_rest_args(tile_blockshape, tile_roi_in)
            if self.description.tile_url_format.startswith('http'):
                retrieval_fn = partial( self._retrieve_remote_tile, rest_args, tile_relative_intersection, result_region )
            else:
                retrieval_fn = partial( self._retrieve_local_tile, rest_args, tile_relative_intersection, result_region )            

            PARALLEL_REQ = True
            if PARALLEL_REQ:
                pool.add( Request( retrieval_fn ) )
            else:
                # execute serially (leave the pool empty)
                retrieval_fn()

        if PARALLEL_REQ:
            with Timer() as timer:
                pool.wait()
            logger.info("Loading {} tiles took a total of {}".format( len(tile_starts), timer.seconds() ))

    def _get_rest_args(self, tile_blockshape, tile_roi_in):
        """
        For a single tile, return a dict of all possible parameters that can be substituted 
        into the tile_url_format string from the volume json description file.
        
        tile_blockshape: The 3D blockshape of the tile 
                         (since tiles are only 1 slice thick, the blockshape always begins with 1).
        tile_roi_in: The ROI within the total volume for a particular tile.
                     (Note that the size of the ROI is usually, but not always, the same as tile_blockshape.
                     Near the volume borders, the tile_roi_in may be smaller.)
        """
        # Special feature: 
        # Some slices are missing, in which case we provide fake data from a different slice.
        # Overwrite the rest args to pull data from an alternate source tile.
        z_start = tile_roi_in[0][0]
        if z_start in self._slice_remapping:
            new_source_slice = self._slice_remapping[z_start]
            tile_roi_in[0][0] = new_source_slice
            tile_roi_in[1][0] = new_source_slice+1

        tile_index = numpy.array(tile_roi_in[0]) / tile_blockshape
        rest_args = { 'z_start' : tile_roi_in[0][0],
                      'z_stop'  : tile_roi_in[1][0],
                      'y_start' : tile_roi_in[0][1],
                      'y_stop'  : tile_roi_in[1][1],
                      'x_start' : tile_roi_in[0][2],
                      'x_stop'  : tile_roi_in[1][2],
                      'z_index' : tile_index[0],
                      'y_index' : tile_index[1],
                      'x_index' : tile_index[2] }

        # Apply special z_translation_function
        if self.description.z_translation_function is not None:
            z_update_func = eval(self.description.z_translation_function)
            rest_args['z_index'] = rest_args['z_start'] = z_update_func(rest_args['z_index'])
            rest_args['z_stop'] = 1 + rest_args['z_start']

        # Quick sanity check
        assert rest_args['z_index'] == rest_args['z_start']

        # Special arg for Raveler session directories:
        # For files with Z < 1000, no extra directory level
        # For files with Z >= 1000, there is an extra directory level,
        #  in which case the extra '/' is INCLUDED here in the rest arg.
        raveler_z_base = (rest_args['z_index'] // 1000) * 1000
        if raveler_z_base == 0:
            rest_args['raveler_z_base'] = ""
        else:
            rest_args['raveler_z_base'] = str(raveler_z_base) + '/'

        return rest_args

    def _retrieve_local_tile(self, rest_args, tile_relative_intersection, data_out):
        tile_path = self.description.tile_url_format.format( **rest_args )
        logger.debug("Opening {}".format( tile_path ))

        if not os.path.exists(tile_path):
            logger.error("Tile does not exist: {}".format( tile_path ))
            data_out[...] = 0
            return

        # Read the image from the disk with vigra
        img = vigra.impex.readImage(tile_path, dtype='NATIVE')
        assert img.ndim == 3
        if self.description.is_rgb:
            # "Convert" to grayscale -- just take first channel.
            img = img[...,0:1]
        assert img.shape[-1] == 1, "Image has more channels than expected.  "\
                                   "If it is RGB, be sure to set the is_rgb flag in your description json."
        
        # img has axes xyc, but we want zyx
        img = img.transpose()[None,0,:,:]

        if self.description.invert_y_axis:
            # More special Raveler support:
            # Raveler's conventions for the Y-axis are the reverse for everyone else's.
            img = img[:, ::-1, :]

        # Copy just the part we need into the destination array
        assert img[roiToSlice(*tile_relative_intersection)].shape == data_out.shape
        data_out[:] = img[roiToSlice(*tile_relative_intersection)]

        # If there's a special transform, apply it now.
        if self.description.data_transform_function is not None:
            transform = eval(self.description.data_transform_function)
            data_out[:] = transform(data_out)

    # For late imports
    requests = None
    PIL = None
    
    TEST_MODE = False # For testing purposes only. See below.    

    def _retrieve_remote_tile(self, rest_args, tile_relative_intersection, data_out):
        # Late import
        if not TiledVolume.requests:
            import requests
            TiledVolume.requests = requests
        requests = TiledVolume.requests

        tile_url = self.description.tile_url_format.format( **rest_args )
        logger.debug("Retrieving {}".format( tile_url ))
        try:
            if self._session is None:
                self._session = self._create_session()

                # Provide authentication if we have the details.
                if self.description.username and self.description.password:
                    self._session.auth = (self.description.username, self.description.password)

            success = False
            tries = 0
            while not success:
                try:
                    # Note: We give timeout as a tuple, which requires a recent version of requests.
                    #       If you get an exception about that, upgrade your requests module.
                    r = self._session.get(tile_url, timeout=(3.0, 20.0))
                    success = True
                except requests.ConnectionError:
                    # This special 'pass' is here because we keep running into exceptions like this: 
                    #   ConnectionError: HTTPConnectionPool(host='neurocean.int.janelia.org', port=6081): 
                    #   Max retries exceeded with url: /ssd-3-tiles/abd1.5/43/24_25_0.jpg 
                    #   (Caused by <class 'httplib.BadStatusLine'>: '')
                    # So now we loop a few times and only give up if something is really wrong.
                    if tries == 5:
                        raise # give up
                    tries += 1
        except:
            # During testing, the server we're pulling from might be in our own process.
            # Apparently that means that it is not very responsive, leading to exceptions.
            # As a cheap workaround, just try one more time.
            if self.TEST_MODE:
                import time
                time.sleep(0.01)
                r = self._session.get(tile_url, timeout=(3.0, 20.0))
            else:
                raise
                
        if r.status_code == requests.codes.not_found:
            logger.warn("NOTFOUND: {}".format( tile_url ))
            data_out[:] = 0
        else:
            # late import
            if not TiledVolume.PIL:
                import PIL
                import PIL.Image
                TiledVolume.PIL = PIL
            PIL = TiledVolume.PIL

            img = numpy.asarray( PIL.Image.open(StringIO(r.content)) )
            if self.description.is_rgb:
                # "Convert" to grayscale -- just take first channel.
                assert img.ndim == 3
                img = img[...,0]
            assert img.ndim == 2, "Image seems to be of the wrong dimension.  "\
                                  "If it is RGB, be sure to set the is_rgb flag in your description json."
            # img has axes xy, but we want zyx
            img = img[None]

            if self.description.invert_y_axis:
                # More special Raveler support:
                # Raveler's conventions for the Y-axis are the reverse for everyone else's.
                img = img[:, ::-1, :]
        
            # Copy just the part we need into the destination array
            assert img[roiToSlice(*tile_relative_intersection)].shape == data_out.shape
            data_out[:] = img[roiToSlice(*tile_relative_intersection)]
            
            # If there's a special transform, apply it now.
            if self.description.data_transform_function is not None:
                transform = eval(self.description.data_transform_function)
                data_out[:] = transform(data_out)
    
    @classmethod
    def _create_session(cls):
        """
        Generate a requests.Session object to use for this TiledVolume.
        Using a session allows us to benefit from a connection pool 
          instead of establishing a new connection for every request.
        """
        # Late import
        if not TiledVolume.requests:
            import requests
            TiledVolume.requests = requests
        requests = TiledVolume.requests

        session = requests.Session()

        # Replace the session http adapters with ones that use larger connection pools
        n_threads = max(1, Request.global_thread_pool.num_workers)
        adapter = requests.adapters.HTTPAdapter(pool_connections=n_threads, pool_maxsize=n_threads)
        adapter2 = requests.adapters.HTTPAdapter(pool_connections=n_threads, pool_maxsize=n_threads)
        session.mount('http://', adapter)
        session.mount('https://', adapter2)
        return session

