import os
import sys
import shutil
import tempfile

import numpy
import h5py

from lazyflow.utility import PathComponents
from lazyflow.utility.io.blockwiseFileset import BlockwiseFileset
from lazyflow.roi import sliceToRoi, roiToSlice, getIntersectingBlocks

import logging
logger = logging.getLogger(__name__)
#logger.addHandler(logging.StreamHandler(sys.stdout))
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

logger.setLevel(logging.INFO)
#logger.setLevel(logging.DEBUG)

class TestBlockwiseFileset(object):
    
    @classmethod
    def setupClass(cls):
        testConfig = \
        """
        {
            "_schema_name" : "blockwise-fileset-description",
            "_schema_version" : 1.0,
            "name" : "synapse_small",
            "format" : "hdf5",
            "axes" : "txyzc",
            "shape" : [1,400,400,200,1],
            "dtype" : "numpy.uint8",
            "compression" : "lzf",
            "block_shape" : [1, 50, 50, 50, 100],
            "block_file_name_format" : "cube{roiString}.h5/volume/data"
        }
        """
        cls.tempDir = tempfile.mkdtemp()
        cls.description_path = os.path.join(cls.tempDir, "description.json")
        with open(cls.description_path, 'w') as f:
            f.write(testConfig)
    
        logger.debug( "Loading config file..." )
        cls.bfs = BlockwiseFileset( cls.description_path, 'a' )
        cls.dataShape = tuple(cls.bfs.description.shape)
    
        logger.debug( "Creating random test data..." )
        cls.data = numpy.random.randint(255, size=cls.dataShape ).astype(numpy.uint8)
        
    @classmethod
    def teardownClass(cls):
        if not cls.bfs._closed:
            cls.bfs.close()
        assert not cls.bfs.purgeAllLocks(), "Some lockfiles were left lingering."
        shutil.rmtree(cls.tempDir)

    def test_1_BasicWrite(self):
        """
        This 'test' writes  all blocks of the dataset.
        SIDE EFFECT: This test is run first because the other tests use the dataset that it produces.
        """
        logger.debug( "Writing test data..." )
        totalRoi = ([0,0,0,0,0], self.dataShape)
        self.bfs.writeData( totalRoi, self.data )

        # All blocks are now available.
        allBlockStarts = getIntersectingBlocks( self.bfs.description.block_shape, totalRoi )
        for blockStart in allBlockStarts:
            self.bfs.setBlockStatus(blockStart, BlockwiseFileset.BLOCK_AVAILABLE)

    def test_2_ReadAll(self):
        logger.debug( "Reading data..." )
        read_data = numpy.zeros( tuple(self.dataShape), dtype=numpy.uint8 )
        self.bfs.readData( ([0,0,0,0,0], self.dataShape), read_data )
        
        logger.debug( "Checking data..." )
        assert (self.data == read_data).all(), "Data didn't match."
    
    def test_3_ReadSome(self):
        logger.debug( "Reading data..." )
        slicing = numpy.s_[:, 50:150, 50:150, 50:150, :]
        roi = sliceToRoi( slicing, self.dataShape )
        roiShape = roi[1] - roi[0]
        read_data = numpy.zeros( tuple(roiShape), dtype=numpy.uint8 )
        
        self.bfs.readData( roi, read_data )
        
        logger.debug( "Checking data..." )
        assert self.data[slicing].shape == read_data.shape
        assert (self.data[slicing] == read_data).all(), "Data didn't match."
    
    def test_4_ManySmallReadsFromOneBlock(self):
        logger.debug( "Starting small reads..." )

        for _ in range(100):
            x = numpy.random.randint(49) + 1
            y = numpy.random.randint(49) + 1
            z = numpy.random.randint(49) + 1
            slicing = numpy.s_[:, 0:x, 0:y, 0:z, :]
            roi = sliceToRoi( slicing, self.dataShape )
            roiShape = roi[1] - roi[0]
            read_data = numpy.zeros( tuple(roiShape), dtype=numpy.uint8 )
        
            self.bfs.readData( roi, read_data )
        
            assert self.data[slicing].shape == read_data.shape
            assert (self.data[slicing] == read_data).all(), "Data didn't match."

    def test_5_TestExportRoi(self):
        roi = ( (0, 25, 25, 25, 0), (1, 75, 75, 75, 1) )
        exportDir = tempfile.mkdtemp()
        datasetPath = self.bfs.exportRoiToHdf5( roi, exportDir )
        path_parts = PathComponents( datasetPath )

        try:        
            assert path_parts.externalDirectory == exportDir, "Dataset was not exported to the correct directory"
            
            expected_data = self.data[ roiToSlice(*roi) ]
            with h5py.File(path_parts.externalPath, 'r') as f:
                read_data = f[path_parts.internalPath][...]
    
            assert read_data.shape == expected_data.shape, "Exported data had wrong shape"
            assert read_data.dtype == expected_data.dtype, "Exported data had wrong dtype"
            assert (read_data == expected_data).all(), "Exported data did not match expected data"
        
        finally:
            shutil.rmtree(exportDir)

    def test_6_TestExportSubset(self):
        roi = ( (0, 0, 50, 100, 0), (1, 100, 200, 200, 1) )
        exportDir = tempfile.mkdtemp()
        self.bfs.close()
        self.bfs.reopen( 'r' )
        exported_description_path = self.bfs.exportSubset( roi, exportDir )

        try:        
            exported_bfs = BlockwiseFileset( exported_description_path, 'r' )
            assert os.path.exists( exported_description_path ), "Couldn't even find the exported description file."

            read_data = exported_bfs.readData( roi )
            expected_data = self.data[ roiToSlice(*roi) ]
    
            assert read_data.shape == expected_data.shape, "Exported data had wrong shape"
            assert read_data.dtype == expected_data.dtype, "Exported data had wrong dtype"
            assert (read_data == expected_data).all(), "Exported data did not match expected data"
        
        finally:
            shutil.rmtree(exportDir)
        
    def test_7_ManySmallWritesToOneBlock(self):
        self.bfs.close()
        self.bfs.reopen( 'a' )
        for _ in range(100):
            x = numpy.random.randint(49) + 1
            y = numpy.random.randint(49) + 1
            z = numpy.random.randint(49) + 1
            slicing = numpy.s_[:, 0:x, 0:y, 0:z, :]
            roi = sliceToRoi( slicing, self.dataShape )
            roiShape = roi[1] - roi[0]
            
            random_data = numpy.random.random( roiShape )
            self.bfs.writeData( roi, random_data )
            self.bfs.setBlockStatusesForRoi( roi, BlockwiseFileset.BLOCK_AVAILABLE )

    def test_8_CloseBfs(self):
        self.bfs.close()

    def test_9_TestView(self):
        """
        Load some of the dataset again; this time with an offset view.
        Note: The original blockwise fileset must be closed before this test starts.
        """
        # Create a copy of the original description, but specify a translated (and smaller) view
        desc = BlockwiseFileset.readDescription(self.description_path)
        desc.view_origin = [0, 300, 200, 100, 0]
        desc.view_shape = [1, 50, 50, 50, 1]
        offsetConfigPath = self.description_path + '_offset'
        BlockwiseFileset.writeDescription(offsetConfigPath, desc)
        
        # Open the fileset using the special description file
        bfs = BlockwiseFileset( offsetConfigPath, 'r' )
        try:
            assert (bfs.description.view_origin == desc.view_origin).all()
            assert (bfs.description.view_shape == desc.view_shape).all()
            
            # Read some data
            logger.debug( "Reading data..." )
            disk_slicing = numpy.s_[:, 300:350, 200:250, 100:150, :]
            view_slicing = numpy.s_[:, 0:50, 0:50, 0:50, :]
            roi = sliceToRoi( view_slicing, self.dataShape )
            roiShape = roi[1] - roi[0]
            read_data = numpy.zeros( tuple(roiShape), dtype=numpy.uint8 )
            
            bfs.readData( roi, read_data )
            
            # The data we read should match the correct part of the original dataset.
            logger.debug( "Checking data..." )
            assert self.data[disk_slicing].shape == read_data.shape
            assert (self.data[disk_slicing] == read_data).all(), "Data didn't match."
        
        finally:
            bfs.close()

class TestObjectBlockwiseFileset(object):
    """
    Test with arrays of dtype=object.
    """

    @classmethod
    def setupClass(cls):
        testConfig = \
        """
        {
            "_schema_name" : "blockwise-fileset-description",
            "_schema_version" : 1.0,
            "name" : "synapse_small",
            "format" : "hdf5",
            "axes" : "txyzc",
            "shape" : [1,10,20,5,1],
            "dtype" : "object",
            "block_shape" : [1, 5, 4, 1, 100],
            "block_file_name_format" : "cube{roiString}.h5/volume/data"
        }
        """
        cls.tempDir = tempfile.mkdtemp()
        cls.description_path = os.path.join(cls.tempDir, "config.json")
        with open(cls.description_path, 'w') as f:
            f.write(testConfig)
    
        logger.debug( "Loading config file..." )
        cls.bfs = BlockwiseFileset( cls.description_path, 'a' )
        cls.dataShape = tuple(cls.bfs.description.shape)

        def make_dummy_dict(x):
            return {str(x) : numpy.array([x,x])}
        vec_make_dummy_dict = numpy.vectorize(make_dummy_dict)

        int_data = numpy.random.randint(255, size=cls.dataShape ).astype(numpy.uint8)
        dict_data = vec_make_dummy_dict(int_data)
        cls.data = dict_data
        
    @classmethod
    def teardownClass(cls):
        if not cls.bfs._closed:
            cls.bfs.close()
        assert not cls.bfs.purgeAllLocks(), "Some lockfiles were left lingering."
        shutil.rmtree(cls.tempDir)

    def test_1_BasicWrite(self):
        """
        This 'test' writes  all blocks of the dataset.
        SIDE EFFECT: This test is run first because the other tests use the dataset that it produces.
        """
        logger.debug( "Writing test data..." )
        totalRoi = ([0,0,0,0,0], self.dataShape)
        self.bfs.writeData( totalRoi, self.data )

        # All blocks are now available.
        allBlockStarts = getIntersectingBlocks( self.bfs.description.block_shape, totalRoi )
        for blockStart in allBlockStarts:
            self.bfs.setBlockStatus(blockStart, BlockwiseFileset.BLOCK_AVAILABLE)

    def test_2_ReadAll(self):
        logger.debug( "Reading data..." )
        read_data = numpy.zeros( tuple(self.dataShape), dtype=object )
        self.bfs.readData( ([0,0,0,0,0], self.dataShape), read_data )
        
        logger.debug( "Checking data..." )
        for a,b in zip(self.data.flat, read_data.flat):
            for (k1,v1),(k2,v2) in zip(a.items(), b.items()):
                assert k1 == k2
                assert (v1 == v2).all()

    def test_3_ReadSome(self):
        logger.debug( "Reading data..." )
        slicing = numpy.s_[:, 2:7, 8:11, 0:1, :]
        roi = sliceToRoi( slicing, self.dataShape )
        roiShape = roi[1] - roi[0]
        read_data = numpy.zeros( tuple(roiShape), dtype=object )
        
        self.bfs.readData( roi, read_data )
        
        logger.debug( "Checking data..." )
        assert self.data[slicing].shape == read_data.shape
        for a,b in zip(self.data[slicing].flat, read_data.flat):
            for (k1,v1),(k2,v2) in zip(a.items(), b.items()):
                assert k1 == k2
                assert (v1 == v2).all()

if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)






















