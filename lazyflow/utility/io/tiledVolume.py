import os
import numpy
import vigra
import tempfile
import shutil
from functools import partial
from StringIO import StringIO

## Instead of importing requests and PIL here, 
## use late imports (below) so people who don't use TiledVolume don't have to have them

# New dependency: requests is way more convenient than urllib or httplib
#import requests

# Use PIL instead of vigra since it allows us to open images in-memory
#from PIL import Image

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
        "bounds_zyx" : AutoEval(numpy.array),
        "shape_zyx" : AutoEval(numpy.array), # synonym for bounds_zyx (until we support offset_origin)
        "resolution_zyx" : AutoEval(numpy.array), 

        "tile_shape_2d_yx" : AutoEval(numpy.array),

        "username" : str,
        "password" : str,

        # This doesn't change how the data is read from the server,
        #  but instead specifies the indexing order of the numpy volumes produced.
        "output_axes" : str,

        "cache_tiles" : bool,

        # Offset not supported for now...
        #"origin_offset" : AutoEval(numpy.array),

        # For now, 3D-only, sliced across Z
        # TODO: support 5D.
        # Allow multiple url schemes: tiles might be addressed via pixel coordinates or row/column indexing
        # (z_index and z_start are synonyms here -- either is allowed)
        "tile_url_format" : FormattedField( requiredFields=[],
                                            optionalFields=["x_start", "y_start", "z_start",
                                                            "x_stop",  "y_stop",  "z_stop",
                                                            "x_index", "y_index", "z_index"] ),
        "extend_slices" : list
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
        
        # offset not supported yet...
        #if description.origin_offset is None:
        #    description.origin_offset = numpy.array( [0]*len(description.bounds_zyx) )
        #description.shape = description.bounds_zyx - description.origin_offset

        # for now, there's no difference between shape and bounds        
        if description.shape_zyx is not None and description.bounds_zyx is not None:
            assert all(description.shape_zyx == description.bounds_zyx)
        if description.shape_zyx is None:
            description.shape_zyx = tuple(description.bounds_zyx)
        if description.bounds_zyx is None:
            description.bounds_zyx = tuple(description.shape_zyx)

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

        shape_dict = dict( zip('zyx', self.description.bounds_zyx) )
        self.output_shape = tuple( shape_dict[k] for k in self.description.output_axes )

        self._slice_remapping = {}
        for source, destinations in self.description.extend_slices:
            for dest in destinations:
                self._slice_remapping[dest] = source

    def close(self):
        if self._session:
            self._session.close()

    def read(self, roi, result_out):
        """
        roi: (start, stop) tuples, ordered according to description.output_axes
        """
        output_axes = self.description.output_axes
        roi_transposed = zip(*roi)
        roi_dict = dict( zip(output_axes, roi_transposed) )
        roi = zip( *(roi_dict['z'], roi_dict['y'], roi_dict['x']) )

        # First, normalize roi and result to zyx order
        result_out = vigra.taggedView(result_out, output_axes)
        result_out = result_out.withAxes(*'zyx')
        
        assert numpy.array(roi).shape == (2,3), "Invalid roi for 3D volume: {}".format( roi )
        roi = numpy.array(roi)
        assert (result_out.shape == (roi[1] - roi[0])).all()
        
        tile_blockshape = (1,) + tuple(self.description.tile_shape_2d_yx)
        tile_starts = getIntersectingBlocks( tile_blockshape, roi )

        # We use a fresh tmp dir for each read to avoid conflicts between parallel reads
        tmpdir = tempfile.mkdtemp()
        
        pool = RequestPool()
        for tile_start in tile_starts:
            tile_roi_in = getBlockBounds( self.description.shape_zyx, tile_blockshape, tile_start )
            tile_roi_in = numpy.array(tile_roi_in)

            # This tile's portion of the roi
            intersecting_roi = getIntersection( roi, tile_roi_in )
            intersecting_roi = numpy.array( intersecting_roi )

            # Compute slicing within destination array and slicing within this tile
            destination_relative_intersection = numpy.subtract(intersecting_roi, roi[0])
            tile_relative_intersection = intersecting_roi - tile_roi_in[0]
            
            # Get a view to the output slice
            result_region = result_out[roiToSlice(*destination_relative_intersection)]
            
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

            # Quick sanity check
            assert rest_args['z_index'] == rest_args['z_start']

            retrieval_fn = partial( self._retrieve_tile, tmpdir, rest_args, tile_relative_intersection, result_region )

            PARALLEL_REQ = True
            if PARALLEL_REQ:
                pool.add( Request( retrieval_fn ) )
            else:
                # execute serially (leave the pool empty)
                retrieval_fn()
        
        pool.wait()
        
        # Clean up our temp files.
        shutil.rmtree(tmpdir)

    # For late imports
    requests = None
    PIL = None
    
    TEST_MODE = False # For testing purposes only. See below.    

    def _retrieve_tile(self, tmpdir, rest_args, tile_relative_intersection, data_out):
        # Late import
        if not TiledVolume.requests:
            import requests
            TiledVolume.requests = requests
        requests = TiledVolume.requests

        tile_url = self.description.tile_url_format.format( **rest_args )

        tmp_filename = 'z{z_start}_y{y_start}_x{x_start}'.format( **rest_args )
        tmp_filename += '.' + self.description.format
        tmp_filepath = os.path.join(tmpdir, tmp_filename) 

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
                    r = self._session.get(tile_url)
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
                r = self._session.get(tile_url)
            else:
                raise
                
        if r.status_code == requests.codes.not_found:
            logger.warn("NOTFOUND: {}".format( tile_url, tmp_filepath ))
            data_out[:] = 0
        else:
            USE_PIL = True
            if USE_PIL:
                # late import
                if not TiledVolume.PIL:
                    import PIL
                    import PIL.Image
                    TiledVolume.PIL = PIL
                PIL = TiledVolume.PIL

                img = numpy.asarray( PIL.Image.open(StringIO(r.content)) )
                assert img.ndim == 2
                # img has axes xy, but we want zyx
                img = img[None]
                #img = img.transpose()[None]
            else: 
                logger.debug("saving to {}".format( tmp_filepath ))
                with open(tmp_filepath, 'wb') as f:
                    CHUNK_SIZE = 10*1024
                    for chunk in r.iter_content(CHUNK_SIZE):
                        f.write(chunk)

                # Read the image from the disk with vigra
                img = vigra.impex.readImage(tmp_filepath, dtype='NATIVE')
                assert img.ndim == 3
                assert img.shape[-1] == 1
                
                # img has axes xyc, but we want zyx
                img = img.transpose()[None,0,:,:]
            
            # Copy just the part we need into the destination array
            assert img[roiToSlice(*tile_relative_intersection)].shape == data_out.shape
            data_out[:] = img[roiToSlice(*tile_relative_intersection)]
    
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
        n_threads = Request.global_thread_pool.num_workers
        adapter = requests.adapters.HTTPAdapter(pool_connections=n_threads, pool_maxsize=n_threads)
        adapter2 = requests.adapters.HTTPAdapter(pool_connections=n_threads, pool_maxsize=n_threads)
        session.mount('http://', adapter)
        session.mount('https://', adapter2)
        return session
