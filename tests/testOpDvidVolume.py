# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Copyright 2011-2014, the ilastik developers

import os
import shutil
import tempfile
import unittest

import numpy
import vigra
import h5py

from lazyflow.graph import Graph

try:
    from lazyflow.operators.ioOperators import OpDvidVolume
    # Must be imported AFTER lazyflow, which adds dvidclient to sys.path
    from mockserver.h5mockserver import H5MockServer, H5MockServerDataFile 
except ImportError:
    have_dvid = False
else:
    have_dvid = True


@unittest.skipIf(not have_dvid, "optional module dvidclient not available.")
class TestOpDvidVolume(unittest.TestCase):
    """
    Mostly copied from the dvid_volume test...
    """
    
    @classmethod
    def setupClass(cls):
        """
        Override.  Called by nosetests.
        """
        if not have_dvid:
            return
        cls._tmp_dir = tempfile.mkdtemp()
        cls.test_filepath = os.path.join( cls._tmp_dir, "test_data.h5" )
        cls._generate_testdata_h5(cls.test_filepath)
        cls.server_proc, cls.shutdown_event = H5MockServer.create_and_start( cls.test_filepath, "localhost", 8000 )

    @classmethod
    def teardownClass(cls):
        """
        Override.  Called by nosetests.
        """
        if not have_dvid:
            return
        shutil.rmtree(cls._tmp_dir)
        cls.shutdown_event.set()
        cls.server_proc.join()

    @classmethod
    def _generate_testdata_h5(cls, test_filepath):
        """
        Generate a temporary hdf5 file for the mock server to use (and us to compare against)
        """
        # Generate some test data
        data = numpy.indices( (10, 100, 200, 3) )
        assert data.shape == (4, 10, 100, 200, 3)
        data = data.astype( numpy.uint32 )
        data = vigra.taggedView( data, 'tzyxc' )

        # Choose names
        cls.dvid_dataset = "datasetA"
        cls.data_uuid = "abcde"
        cls.data_name = "indices_data"

        # Write to h5 file
        with H5MockServerDataFile( test_filepath ) as test_h5file:
            test_h5file.add_node( cls.dvid_dataset, cls.data_uuid )
            test_h5file.add_volume( cls.dvid_dataset, cls.data_name, data )
    
    def test_cutout(self):
        """
        Get some data from the server and check it.
        """
        self._test_volume( "localhost:8000", self.test_filepath, self.data_uuid, self.data_name, (0,9,5,50,0), (4,10,20,150,3) )
    
    def _test_volume(self, hostname, h5filename, uuid, dataname, start, stop):
        """
        hostname: The dvid server host
        h5filename: The h5 file to compare against
        h5group: The hdf5 group, also used as the uuid of the dvid dataset
        h5dataset: The dataset name, also used as the name of the dvid dataset
        start, stop: The bounds of the cutout volume to retrieve from the server. C ORDER FOR THIS TEST BECAUSE we use transpose_axes=True.
        """
        # Retrieve from server
        graph = Graph()
        opDvidVolume = OpDvidVolume( hostname, uuid, dataname, transpose_axes=True, graph=graph )
        subvol = opDvidVolume.Output( start, stop ).wait()

        # Retrieve from file
        slicing = tuple( slice(x,y) for x,y in zip(start, stop) )
        with h5py.File(h5filename, 'r') as f:
            expected_data = f['all_nodes'][uuid][dataname][slicing]

        # Compare.
        assert ( subvol.view(numpy.ndarray) == expected_data ).all(),\
            "Data from server didn't match data from file!"

if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
