import nose
import os
import sys
import tempfile
import h5py
from lazyflow.operators.ioOperators.opRESTfulVolumeReader import OpRESTfulVolumeReader
from lazyflow.graph import Graph

import logging
logger = logging.getLogger(__name__)
logger.addHandler( logging.StreamHandler( sys.stdout ) )
logger.setLevel(logging.INFO)
#logger.setLevel(logging.DEBUG)

class TestRESTfulVolume(object):

    def testBasic(self):
        if 'TRAVIS' in os.environ:
            raise nose.SkipTest
        testConfig0 = """
        {
            "_schema_name" : "RESTful-volume-description",
            "_schema_version" : 1.0,
        
            "name" : "Bock11-level0",
            "format" : "hdf5",
            "axes" : "zyx",
            "##NOTE":"The first z-slice of the bock dataset is 2917, so the origin_offset must be at least 2917",
            "origin_offset" : [2917, 50000, 50000],
            "###shape" : [1239, 135424, 119808],
            "shape" : [1239, 10000, 10000],
            "dtype" : "numpy.uint8",
            "url_format" : "http://openconnecto.me/emca/bock11/hdf5/0/{x_start},{x_stop}/{y_start},{y_stop}/{z_start},{z_stop}/",
            "hdf5_dataset" : "cube"
        }
        """
    
        testConfig4 = """
        {
            "_schema_name" : "RESTful-volume-description",
            "_schema_version" : 1.0,
        
            "name" : "Bock11-level4",
            "format" : "hdf5",
            "axes" : "zyx",
            "##NOTE":"The first z-slice of the bock dataset is 2917, so the origin_offset must be at least 2917",
            "origin_offset" : [2917, 0, 0],
            "shape" : [1239, 8704, 7680],
            "dtype" : "numpy.uint8",
            "url_format" : "http://openconnecto.me/emca/bock11/hdf5/4/{x_start},{x_stop}/{y_start},{y_stop}/{z_start},{z_stop}/",
            "hdf5_dataset" : "cube"
        }
        """
        descriptionFilePath = os.path.join(tempfile.mkdtemp(), 'desc.json')
        with open(descriptionFilePath, 'w') as descFile:
            descFile.write( testConfig4 )
        
        graph = Graph()
        op = OpRESTfulVolumeReader(graph=graph)
        op.DescriptionFilePath.setValue( descriptionFilePath )
        
        #data = op.Output[0:100, 50000:50200, 50000:50200].wait()
        data = op.Output[0:10, 4000:4100, 4000:4100].wait()
        
        # We expect a channel dimension to be added automatically...
        assert data.shape == ( 10, 100, 100, 1 )
    
        outputDataFilePath = os.path.join(tempfile.mkdtemp(), 'testOutput.h5')
        with h5py.File( outputDataFilePath, 'w' ) as outputDataFile:
            outputDataFile.create_dataset('volume', data=data)
    
        logger.debug( "Wrote data to {}".format(outputDataFilePath) )

            
if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
