import os
import shutil
import tempfile
import multiprocessing

import numpy
import vigra
import h5py

from lazyflow.graph import Graph
from lazyflow.operators.ioOperators import OpDvidVolume

# Must be imported AFTER lazyflow, which adds dvidclient to sys.path
from mockserver.h5mockserver import H5MockServer, H5CutoutRequestHandler

class TestOpDvidVolume(object):
    """
    Mostly copied from the dvid_volume test...
    """
    
    @classmethod
    def setupClass(cls):
        """
        Override.  Called by nosetests.
        """
        cls._tmp_dir = tempfile.mkdtemp()
        cls.test_filepath = os.path.join( cls._tmp_dir, "test_data.h5" )
        cls._generate_testdata_h5(cls.test_filepath)
        cls.server_proc = cls._start_mockserver( cls.test_filepath )

    @classmethod
    def teardownClass(cls):
        """
        Override.  Called by nosetests.
        """
        shutil.rmtree(cls._tmp_dir)
        cls.server_proc.terminate()

    @classmethod
    def _generate_testdata_h5(cls, test_filepath):
        """
        Generate a temporary hdf5 file for the mock server to use (and us to compare against)
        """
        # Generate some test data
        data = numpy.indices( (10, 100, 200, 3) )
        assert data.shape == (4, 10, 100, 200, 3)
        data = data.astype( numpy.uint32 )

        # Choose names
        cls.data_uuid = "abcde"
        cls.data_name = "indices_data"
        dataset_name = cls.data_uuid + '/' + cls.data_name

        # Write to h5 file
        with h5py.File( test_filepath, "w" ) as test_h5file:        
            dset = test_h5file.create_dataset(dataset_name, data=data)
            dset.attrs["axistags"] = vigra.defaultAxistags("tzyxc").toJSON()

    @classmethod
    def _start_mockserver(cls, h5filepath):
        """
        Start the mock DVID server in a separate process.
        """
        def server_main():
            server_address = ('', 8000)
            server = H5MockServer( h5filepath, server_address, H5CutoutRequestHandler )
            server.serve_forever()
    
        server_proc = multiprocessing.Process( target=server_main )
        server_proc.start()    
        return server_proc
    
    def test_cutout(self):
        """
        Get some data from the server and check it.
        """
        self._test_volume( "localhost:8000", self.test_filepath, self.data_uuid, self.data_name, (0,9,5,50,0), (4,10,20,150,3) )
    
    def _test_volume(self, hostname, h5filename, h5group, h5dataset, start, stop):
        """
        hostname: The dvid server host
        h5filename: The h5 file to compare against
        h5group: The hdf5 group, also used as the uuid of the dvid dataset
        h5dataset: The dataset name, also used as the name of the dvid dataset
        start, stop: The bounds of the cutout volume to retrieve from the server. C ORDER FOR THIS TEST BECAUSE we use transpose_axes=True.
        """
        # Retrieve from server
        graph = Graph()
        opDvidVolume = OpDvidVolume( hostname, uuid=h5group, dataset_name=h5dataset, transpose_axes=True, graph=graph )
        subvol = opDvidVolume.Output( start, stop ).wait()

        # Retrieve from file
        slicing = tuple( slice(x,y) for x,y in zip(start, stop) )
        with h5py.File(h5filename, 'r') as f:
            expected_data = f[h5group][h5dataset][slicing]

        # Compare.
        assert ( subvol.view(numpy.ndarray) == expected_data ).all(),\
            "Data from server didn't match data from file!"

if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
