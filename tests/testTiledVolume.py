import os
import sys
import nose
import numpy
import h5py

from lazyflow.utility.io.tiledVolume import TiledVolume
from lazyflow.utility import PathComponents
from lazyflow.roi import roiToSlice

import logging
logger = logging.getLogger(__file__)

# Data for this test can be generated with the helper script in lazyflow/bin/make_tiles.py
TILE_DIRECTORY = '/magnetic/png_tiles'
REFERENCE_DATA = '/magnetic/megaslices.h5/data'

# Example schema:
# """
# {
#     "_schema_name" : "tiled-volume-description",
#     "_schema_version" : 1.0,
# 
#     "name" : "My Tiled Data",
#     "format" : "png",
#     "dtype" : "uint8",
#     "bounds" : [50, 1020, 1020],
# 
#     "tile_shape_2d" : [200,200],
# 
#     "tile_url_format" : "http://localhost:8000/tile_z{z_start:05}_y{y_start:05}_x{x_start:05}.png",
#     "extend_slices" : [ [44, [45, 46, 47]],
#                         [40, [41]] ]
# }
# """

class TestTiledVolume(object):

    def setup(self):
        description_path = os.path.join(TILE_DIRECTORY, 'volume_description.json')
        if not os.path.exists( description_path ):
            raise nose.SkipTest
    
        if not os.path.exists( PathComponents(REFERENCE_DATA).externalPath ):
            raise nose.SkipTest
        
        self.tiled_volume = TiledVolume( description_path )
    
    def testBasic(self):
        roi = numpy.array( [(10, 150, 100), (30, 550, 550)] )
        result_out = numpy.zeros( roi[1] - roi[0], dtype=self.tiled_volume.description.dtype )
        self.tiled_volume.read( roi, result_out )
         
        ref_path_comp = PathComponents(REFERENCE_DATA)
        with h5py.File(ref_path_comp.externalPath, 'r') as f:
            ref_data = f[ref_path_comp.internalPath][:]
 
        expected = ref_data[roiToSlice(*roi)]
         
        numpy.save('/tmp/expected.npy', expected)
        numpy.save('/tmp/result_out.npy', result_out)
 
        # We can't expect the pixels to match exactly because compression was used to create the tiles...
        assert (expected == result_out).all()
 
    def testMissingTiles(self):
        # The test data should be missing slice 2
        roi = numpy.array( [(0, 150, 100), (10, 550, 550)] )
        result_out = numpy.zeros( roi[1] - roi[0], dtype=self.tiled_volume.description.dtype )
        self.tiled_volume.read( roi, result_out )
            
        ref_path_comp = PathComponents(REFERENCE_DATA)
        with h5py.File(ref_path_comp.externalPath, 'r') as f:
            ref_data = f[ref_path_comp.internalPath][:]
    
        # Slice 2 is missing
        expected = ref_data[roiToSlice(*roi)]
        expected[2] = 0
            
        #numpy.save('/tmp/expected.npy', expected)
        #numpy.save('/tmp/result_out.npy', result_out)
    
        # We can't expect the pixels to match exactly because compression was used to create the tiles...
        assert (expected == result_out).all()
   
    def testRemappedTiles(self):
        roi = numpy.array( [(40, 150, 100), (50, 550, 550)] )
        result_out = numpy.zeros( roi[1] - roi[0], dtype=self.tiled_volume.description.dtype )
        self.tiled_volume.read( roi, result_out )
           
        ref_path_comp = PathComponents(REFERENCE_DATA)
        with h5py.File(ref_path_comp.externalPath, 'r') as f:
            ref_data = f[ref_path_comp.internalPath][:]
   
        # Slice 2 is missing
        expected = ref_data[roiToSlice(*roi)]
        expected[5:8] = expected[4]
        expected[1] = expected[0]
           
        #numpy.save('/tmp/expected.npy', expected)
        #numpy.save('/tmp/result_out.npy', result_out)
   
        # We can't expect the pixels to match exactly because compression was used to create the tiles...
        assert (expected == result_out).all()

class TestCustomAxes(object):
    
    def setup(self):
        description_path = os.path.join(TILE_DIRECTORY, 'transposed_volume_description.json')
        if not os.path.exists( description_path ):
            raise nose.SkipTest
    
        if not os.path.exists( PathComponents(REFERENCE_DATA).externalPath ):
            raise nose.SkipTest
        
        self.tiled_volume = TiledVolume( description_path )
    
    def testCustomAxes(self):
        roi = numpy.array( [(10, 150, 100), (30, 550, 550)] )
        result_out = numpy.zeros( roi[1] - roi[0], dtype=self.tiled_volume.description.dtype )

        roi_t = (tuple(reversed(roi[0])), tuple(reversed(roi[1])))
        result_out_t = result_out.transpose()
        
        self.tiled_volume.read( roi_t, result_out_t )
         
        ref_path_comp = PathComponents(REFERENCE_DATA)
        with h5py.File(ref_path_comp.externalPath, 'r') as f:
            ref_data = f[ref_path_comp.internalPath][:]
 
        expected = ref_data[roiToSlice(*roi)]
         
        numpy.save('/tmp/expected.npy', expected)
        numpy.save('/tmp/result_out.npy', result_out)
 
        # We can't expect the pixels to match exactly because compression was used to create the tiles...
        assert (expected == result_out).all()

if __name__ == "__main__":
    # Logging is OFF by default when running from command-line nose, i.e.:
    # nosetests thisFile.py)
    # but ON by default if running this test directly, i.e.:
    # python thisFile.py
    handler = logging.StreamHandler(sys.stdout)
    logger.addHandler( handler )
    logger.setLevel(logging.DEBUG)

    tiledVolumeLogger = logging.getLogger("lazyflow.utility.io.tiledVolume")
    tiledVolumeLogger.addHandler( handler )
    tiledVolumeLogger.setLevel(logging.ERROR)

    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)
    if not ret: sys.exit(1)
