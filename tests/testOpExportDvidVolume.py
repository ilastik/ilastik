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
    from lazyflow.operators.ioOperators import OpExportDvidVolume
    # Must be imported AFTER lazyflow, which adds dvidclient to sys.path
    from mockserver.h5mockserver import H5MockServer, H5MockServerDataFile 
except ImportError:
    have_dvid = False
else:
    have_dvid = True


@unittest.skipIf(not have_dvid, "optional module dvidclient not available.")
class TestOpDvidVolume(unittest.TestCase):
    
    @classmethod
    def setupClass(cls):
        """
        Override.  Called by nosetests.
        """
        if not have_dvid:
            return
        cls._tmp_dir = tempfile.mkdtemp()
        cls.test_filepath = os.path.join( cls._tmp_dir, "test_data.h5" )
        cls._generate_empty_h5(cls.test_filepath)
        cls.server_proc, cls.shutdown_event = H5MockServer.create_and_start( cls.test_filepath, "localhost", 8000, 
                                                                             same_process=False, disable_server_logging=True )

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
    def _generate_empty_h5(cls, test_filepath):
        """
        Generate a temporary hdf5 file for the mock server to use (and us to compare against)
        """
        # Choose names
        cls.dvid_dataset = "datasetA"
        cls.data_uuid = "abcde"
        cls.data_name = "indices_data"

        # Write to h5 file
        with H5MockServerDataFile( test_filepath ) as test_h5file:
            test_h5file.add_node( cls.dvid_dataset, cls.data_uuid )
    
    def test_export(self):
        """
        hostname: The dvid server host
        h5filename: The h5 file to compare against
        h5group: The hdf5 group, also used as the uuid of the dvid dataset
        h5dataset: The dataset name, also used as the name of the dvid dataset
        start, stop: The bounds of the cutout volume to retrieve from the server. C ORDER FOR THIS TEST BECAUSE we use transpose_axes=True.
        """
        # Retrieve from server
        graph = Graph()
        opExport = OpExportDvidVolume( transpose_axes=True, graph=graph )
        
        data = numpy.indices( (10, 100, 200, 4) )
        assert data.shape == (4, 10, 100, 200, 4)
        data = data.astype( numpy.uint8 )
        data = vigra.taggedView( data, vigra.defaultAxistags('tzyxc') )

        # Reverse data order for dvid export
        opExport.Input.setValue( data )
        opExport.NodeDataUrl.setValue( 'http://localhost:8000/api/node/{uuid}/{dataname}'.format( uuid=self.data_uuid, dataname=self.data_name ) )

        # Export!
        opExport.run_export()

        # Retrieve from file
        with h5py.File(self.test_filepath, 'r') as f:
            exported_data = f['all_nodes'][self.data_uuid][self.data_name][:]

        # Compare.
        assert ( data.view(numpy.ndarray) == exported_data ).all(),\
            "Exported data is not correct"

if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
