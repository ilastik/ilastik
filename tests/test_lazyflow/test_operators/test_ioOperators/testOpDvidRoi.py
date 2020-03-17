from future import standard_library

standard_library.install_aliases()

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
#           http://ilastik.org/license/
###############################################################################
import os
import http.client
import json
import shutil
import tempfile
import unittest
import platform

import numpy
import vigra
import h5py
import pytest

from lazyflow.graph import Graph
from lazyflow.roi import roiToSlice

TEST_DVID_SERVER = os.getenv("TEST_DVID_SERVER", None)
if TEST_DVID_SERVER is None:
    pytest.skip("skipping DVID tests, Environment variable TEST_DVID_SERVER is not specified", allow_module_level=True)

try:
    from lazyflow.operators.ioOperators import OpDvidRoi
    from libdvid import DVIDConnection, ConnectionMethod, DVIDNodeService
    from libdvid.voxels import VoxelsMetadata

    def get_testrepo_root_uuid():
        connection = DVIDConnection(TEST_DVID_SERVER)
        status, body, error_message = connection.make_request("/repos/info", ConnectionMethod.GET)
        assert status == http.client.OK, "Request for /repos/info returned status {}".format(status)
        assert error_message == ""
        repos_info = json.loads(body)
        test_repos = [
            uuid_repo_info
            for uuid_repo_info in list(repos_info.items())
            if uuid_repo_info[1] and uuid_repo_info[1]["Alias"] == "testrepo"
        ]
        if test_repos:
            uuid = test_repos[0][0]
            return str(uuid)
        else:
            from libdvid import DVIDServerService

            server = DVIDServerService(TEST_DVID_SERVER)
            uuid = server.create_new_repo("testrepo", "This repo is for unit tests to use and abuse.")
            return str(uuid)


except ImportError:
    have_dvid = False
else:
    have_dvid = True


class TestOpDvidRoi(unittest.TestCase):
    @classmethod
    @unittest.skipIf(not have_dvid, "optional module libdvid not available.")
    @unittest.skipIf(platform.system() == "Windows", "DVID not tested on Windows. Skipping.")
    def setUpClass(cls):
        """
        Override.  Called by nosetests.
        """
        cls.uuid = get_testrepo_root_uuid()
        cls.roi_name = "OpDvidRoi_test_roi"
        node_service = DVIDNodeService(TEST_DVID_SERVER, cls.uuid)
        node_service.create_roi(cls.roi_name)

        # Create an upside-down L-shaped roi, something like this:
        #
        # 1 1 1 1
        # 1 1 1 1
        # 1 1 0 0
        # 1 1 0 0
        cls.expected_data = numpy.ones((64, 128, 128), dtype=numpy.uint8, order="C")
        cls.expected_data[:, 64:, 64:] = 0
        block_values = cls.expected_data[::32, ::32, ::32]
        coords = numpy.transpose(numpy.nonzero(block_values))
        node_service.post_roi(cls.roi_name, coords)

    def test(self):
        # Retrieve from server
        graph = Graph()
        opRoi = OpDvidRoi(TEST_DVID_SERVER, self.uuid, self.roi_name, graph=graph)
        roi_vol = opRoi.Output((0, 0, 0), self.expected_data.shape).wait()
        assert (roi_vol == self.expected_data).all()

        # Test a non-aligned roi
        subvol = ((30, 60, 50), (40, 70, 70))
        roi_vol = opRoi.Output(*subvol).wait()
        assert (roi_vol == self.expected_data[roiToSlice(*subvol)]).all()


if __name__ == "__main__":
    import sys
    import nose

    sys.argv.append("--nocapture")  # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture")  # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
