import os
import sys
import shutil
import tempfile
import numpy
import h5py
from lazyflow.roi import sliceToRoi    

import logging
logger = logging.getLogger(__name__)
logger.addHandler( logging.StreamHandler( sys.stdout ) )
logger.setLevel(logging.INFO)
#logger.setLevel(logging.DEBUG)

from lazyflow.blockwiseFileset import BlockwiseFileset
from lazyflow.RESTfulBlockwiseFileset import RESTfulBlockwiseFileset

class TestRESTFullBlockwiseFilset(object):
    
    @classmethod
    def setupClass(cls):
        cls.tempDir = tempfile.mkdtemp()
        logger.debug("Working in {}".format( cls.tempDir ))

        # Create the two sub-descriptions
        Bock11VolumeDescription = """
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
            "hdf5_dataset" : "/cube"
        }
        """

        blockwiseFilesetDescription = \
        """
        {
            "_schema_name" : "blockwise-fileset-description",
            "_schema_version" : 1.0,

            "name" : "bock11-blocks",
            "format" : "hdf5",
            "axes" : "zyx",
            "shape" : [40,40,40],
            "dtype" : "numpy.uint8",
            "block_shape" : [20, 20, 20],
            "block_file_name_format" : "block-{roiString}.h5/cube"
        }
        """
        
        # Combine them into the composite description (see RESTfulBlockwiseFileset.DescriptionFields)
        compositeDescription = \
        """
        {{
            "_schema_name" : "RESTful-blockwise-fileset-description",
            "_schema_version" : 1.0,

            "remote_description" : {remote_description},
            "local_description" : {local_description}        
        }}
        """.format( remote_description=Bock11VolumeDescription, local_description=blockwiseFilesetDescription )
        
        # Create the description file
        cls.descriptionFilePath = os.path.join(cls.tempDir, "description.json")
        with open(cls.descriptionFilePath, 'w') as f:
            f.write(compositeDescription)

    @classmethod
    def teardownClass(cls):
        # If the user is debugging, don't clear the files we're testing with.
        if logger.level > logging.DEBUG:
            shutil.rmtree(cls.tempDir)
        
    def test_1_SingleDownload(self):
        volume = RESTfulBlockwiseFileset( self.descriptionFilePath )

        slicing = numpy.s_[0:20, 0:20, 0:20]
        roi = sliceToRoi(slicing, volume.description.shape)        
        data = volume.readData( roi )
        assert data.shape == (20,20,20)

        assert volume.getBlockStatus( ([0,0,0]) ) == BlockwiseFileset.BLOCK_AVAILABLE

    def test_2_MultiDownload(self):
        volume = RESTfulBlockwiseFileset( self.descriptionFilePath )

        slicing = numpy.s_[0:25, 10:30, 0:20]
        roi = sliceToRoi(slicing, volume.description.shape)        
        data = volume.readData( roi )
        assert data.shape == (25,20,20)

        assert volume.getBlockStatus( ([0,0,0]) ) == BlockwiseFileset.BLOCK_AVAILABLE
        assert volume.getBlockStatus( ([20,0,0]) ) == BlockwiseFileset.BLOCK_AVAILABLE
        assert volume.getBlockStatus( ([20,20,0]) ) == BlockwiseFileset.BLOCK_AVAILABLE
        assert volume.getBlockStatus( ([0,20,0]) ) == BlockwiseFileset.BLOCK_AVAILABLE

    def test_3_UseCachedFiles(self):
        """
        If we remove the url format, we shouln't have any trouble accessing files that have already been downloaded.
        """
        volume = RESTfulBlockwiseFileset( self.descriptionFilePath )
        url_format = volume._remoteVolume.description.url_format
        volume._remoteVolume.description.url_format = ""
        
        try:
            slicing = numpy.s_[0:25, 10:30, 0:20]
            roi = sliceToRoi(slicing, volume.description.shape)        
            data = volume.readData( roi )
            assert data.shape == (25,20,20)
    
            assert volume.getBlockStatus( ([0,0,0]) ) == BlockwiseFileset.BLOCK_AVAILABLE
            assert volume.getBlockStatus( ([20,0,0]) ) == BlockwiseFileset.BLOCK_AVAILABLE
            assert volume.getBlockStatus( ([20,20,0]) ) == BlockwiseFileset.BLOCK_AVAILABLE
            assert volume.getBlockStatus( ([0,20,0]) ) == BlockwiseFileset.BLOCK_AVAILABLE

        finally:
            # Restore the correct url format
            volume._remoteVolume.description.url_format = url_format

if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)




