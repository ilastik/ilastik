###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the Lesser GNU General Public License
# as published by the Free Software Foundation; either version 2.1
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# See the files LICENSE.lgpl2 and LICENSE.lgpl3 for full text of the
# GNU Lesser General Public License version 2.1 and 3 respectively.
# This information is also available on the ilastik web site at:
#		   http://ilastik.org/license/
###############################################################################
import os
import httplib
import json
import shutil
import tempfile
import unittest
import platform

import numpy
import vigra
import h5py

from lazyflow.graph import Graph

try:
    from lazyflow.operators.ioOperators import OpDvidVolume
    from libdvid import DVIDConnection, ConnectionMethod, DVIDNodeService
    from libdvid.voxels import VoxelsMetadata
    TEST_DVID_SERVER = os.getenv("TEST_DVID_SERVER", "127.0.0.1:8000")
    
    def get_testrepo_root_uuid():
        connection = DVIDConnection(TEST_DVID_SERVER)
        status, body, error_message = connection.make_request( "/repos/info", ConnectionMethod.GET)
        assert status == httplib.OK, "Request for /repos/info returned status {}".format( status )
        assert error_message == ""
        repos_info = json.loads(body)
        test_repos = filter( lambda (uuid, repo_info): repo_info and repo_info['Alias'] == 'testrepo', 
                             repos_info.items() )
        if test_repos:
            uuid = test_repos[0][0]
            return str(uuid)
        else:
            from libdvid import DVIDServerService
            server = DVIDServerService(TEST_DVID_SERVER)
            uuid = server.create_new_repo("testrepo", "This repo is for unit tests to use and abuse.");
            return str(uuid)

    def delete_all_data_instances(uuid):
        connection = DVIDConnection(TEST_DVID_SERVER)
        repo_info_uri = "/repo/{uuid}/info".format( uuid=uuid )
        status, body, error_message = connection.make_request( repo_info_uri, ConnectionMethod.GET)
        assert status == httplib.OK, "Request for {} returned status {}".format(repo_info_uri, status)
        assert error_message == ""
        repo_info = json.loads(body)
        for instance_name in repo_info["DataInstances"].keys():
            status, body, error_message = connection.make_request( "/api/repo/{uuid}/{dataname}?imsure=true"
                                                                   .format( uuid=uuid, dataname=str(instance_name) ),
                                                                   ConnectionMethod.DELETE )            
except ImportError:
    have_dvid = False
else:
    have_dvid = True

class TestOpDvidVolume(unittest.TestCase):
    """
    Mostly copied from the dvid_volume test...
    """
    
    @classmethod
    @unittest.skipIf(not have_dvid, "optional module libdvid not available.")
    @unittest.skipIf(platform.system() == "Windows", "DVID not tested on Windows. Skipping.")
    def setUpClass(cls):
        """
        Override.  Called by nosetests.
        """
        # Choose names
        cls.dvid_repo = "datasetA"
        cls.data_name = "random_data"
        cls.volume_location = "/repos/{dvid_repo}/volumes/{data_name}".format( **cls.__dict__ )

        cls.data_uuid = get_testrepo_root_uuid()
        cls.node_location = "/repos/{dvid_repo}/nodes/{data_uuid}".format( **cls.__dict__ )

        # Generate some test data
        data = numpy.random.randint(0, 255, (1, 128, 256, 512))
        data = numpy.asfortranarray(data, numpy.uint8)
        cls.original_data = data
        cls.voxels_metadata = VoxelsMetadata.create_default_metadata(data.shape, data.dtype, "cxyz", 1.0, "")

        # Write it to a new data instance
        node_service = DVIDNodeService(TEST_DVID_SERVER, cls.data_uuid)
        node_service.create_grayscale8(cls.data_name)
        node_service.put_gray3D( cls.data_name, data[0,...], (0,0,0) )

    @classmethod
    def tearDownClass(cls):
        """
        Override.  Called by nosetests.
        """
        delete_all_data_instances(cls.data_uuid)    

    def test_cutout(self):
        """
        Get some data from the server and check it.
        """
        self._test_volume( TEST_DVID_SERVER, self.data_uuid, self.data_name, (50,5,9,0), (150,20,10,1) )
    
    def _test_volume(self, hostname, uuid, dataname, start, stop):
        """
        hostname: The dvid server host
        uuid: The node we can test with
        dataname: The data instance to test with
        start, stop: The bounds of the cutout volume to retrieve from the server. C ORDER FOR THIS TEST BECAUSE we use transpose_axes=True
        """
        # Retrieve from server
        graph = Graph()
        opDvidVolume = OpDvidVolume( hostname, uuid, dataname, {}, transpose_axes=True, graph=graph )
        subvol = opDvidVolume.Output( start, stop ).wait()

        # Retrieve from file (which uses fortran order)
        slicing = tuple( slice(x,y) for x,y in zip(start, stop) )
        slicing = tuple( reversed(slicing) )

        expected_data = self.original_data[slicing]

        # Compare.
        assert ( subvol.view(numpy.ndarray) == expected_data.transpose() ).all(),\
            "Data from server didn't match data from file!"

if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
