import os
import numpy
import vigra
import tempfile
import shutil
from functools import partial

# New dependency: requests is way more convenient than urllib or httplib
import requests

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
        "bounds" : AutoEval(numpy.array),
        "shape" : AutoEval(numpy.array), # synonym for bounds (until we support offset_origin)

        "tile_shape_2d" : AutoEval(numpy.array),

        # Axis order is hard-coded zyx.
        "axes" : str, 

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
        #    description.origin_offset = numpy.array( [0]*len(description.bounds) )
        #description.shape = description.bounds - description.origin_offset
        
        description.bounds = description.bounds
        description.shape = tuple(description.bounds)
        assert description.axes is None or description.axes == "zyx", \
            "Only zyx order is allowed."
        description.axes = "zyx"

        if not description.extend_slices:
            description.extend_slices = []

    def __init__( self, descriptionFilePath ):
        self.description = TiledVolume.readDescription( descriptionFilePath )

        # Check for errors        
        #assert False not in map(lambda a: a in 'xyz', self.description.axes), \
        #    "Unknown axis type.  Known axes: xyz  Your axes:"\
        #    .format(self.description.axes)
        
        assert self.description.format in vigra.impex.listExtensions().split(), \
            "Unknown tile format: {}".format( self.description.format )
        
        assert self.description.tile_shape_2d.shape == (2,)
        assert self.description.bounds.shape == (3,)

        self._slice_remapping = {}
        for source, destinations in self.description.extend_slices:
            for dest in destinations:
                self._slice_remapping[dest] = source

    def read(self, roi, result_out):
        """
        roi: (start, stop) tuples in zyx order.
        """
        assert numpy.array(roi).shape == (2,3), "Invalid roi for 3D volume: {}".format( roi )
        roi = numpy.array(roi)
        assert (result_out.shape == (roi[1] - roi[0])).all()
        
        tile_blockshape = (1,) + tuple(self.description.tile_shape_2d)
        tile_starts = getIntersectingBlocks( tile_blockshape, roi )

        # We use a fresh tmp dir for each read to avoid conflicts between parallel reads
        tmpdir = tempfile.mkdtemp()
        
        pool = RequestPool()
        for tile_start in tile_starts:
            tile_roi_in = getBlockBounds( self.description.shape, tile_blockshape, tile_start )
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
                # leave the pool empty
                retrieval_fn()
        
        pool.wait()
        
        # Clean up our temp files.
        shutil.rmtree(tmpdir)

    def _retrieve_tile(self, tmpdir, rest_args, tile_relative_intersection, data_out): 
        tile_url = self.description.tile_url_format.format( **rest_args )

        tmp_filename = 'z{z_start}_y{y_start}_x{x_start}'.format( **rest_args )
        tmp_filename += '.' + self.description.format
        tmp_filepath = os.path.join(tmpdir, tmp_filename) 

        logger.debug("Retrieving {}, saving to {}".format( tile_url, tmp_filepath ))
        r = requests.get(tile_url)
        if r.status_code == requests.codes.not_found:
            data_out[:] = 0
        else:
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
            assert img[roiToSlice(*tile_relative_intersection)].shape == data_out.shape
        
            # Copy just the part we need into the destination array
            data_out[:] = img[roiToSlice(*tile_relative_intersection)]
