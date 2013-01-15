import os
import sys
import shutil
import tempfile
import numpy
import h5py
from lazyflow.roi import sliceToRoi    
from lazyflow.utility.io.RESTfulVolume import RESTfulVolume

import logging
logger = logging.getLogger(__name__)
logger.addHandler( logging.StreamHandler( sys.stdout ) )
logger.setLevel(logging.INFO)

## Uncomment to enable debug logging for this test.
#logger.setLevel(logging.DEBUG)
#logging.getLogger("lazyflow.utility.io.RESTfulVolume").addHandler( logging.StreamHandler( sys.stdout ) )
#logging.getLogger("lazyflow.utility.io.RESTfulVolume").setLevel(logging.DEBUG)

class TestRESTfulVolume(object):
    
    def testBasic(self):
        """
        Requires access to the Internet...
        """
        testConfig0 = """
        {
            "_schema_name" : "RESTful-volume-description",
            "_schema_version" : 1.0,
        
            "name" : "Bock11-level0",
            "format" : "hdf5",
            "axes" : "zyx",
            "##NOTE":"The first z-slice of the bock dataset is 2917, so the origin_offset must be at least 2917",
            "origin_offset" : [2917, 50000, 50000],
            "bounds" : [4156, 135424, 119808],
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
            "origin_offset" : [2917, 50000, 50000],
            "bounds" : [4156, 8704, 7680],
            "dtype" : "numpy.uint8",
            "url_format" : "http://openconnecto.me/emca/bock11/hdf5/4/{x_start},{x_stop}/{y_start},{y_stop}/{z_start},{z_stop}/",
            "hdf5_dataset" : "cube"
        }
        """
        
        # Create the description file.
        tempDir = tempfile.mkdtemp()
        descriptionFilePath = os.path.join(tempDir, 'desc.json')
        with open(descriptionFilePath, 'w') as descFile:
            descFile.write( testConfig0 )

        # Create the volume object
        volume = RESTfulVolume( descriptionFilePath )

        #slicing = numpy.s_[0:100, 4000:4200, 4000:4200]
        slicing = numpy.s_[0:25, 50000:50050, 50000:50075]
        roi = sliceToRoi( slicing, volume.description.shape )
        outputFile = os.path.join(tempDir, 'volume.h5')
        datasetPath = outputFile + '/cube'
        logger.debug("Downloading subvolume to: {}".format( datasetPath ))
        volume.downloadSubVolume(roi, datasetPath)        

        with h5py.File(outputFile, 'r') as hdf5File:
            data = hdf5File['cube']
            assert data.shape == ( 25, 50, 75 )

        shutil.rmtree(tempDir)
            
if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
