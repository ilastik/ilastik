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
# 		   http://ilastik.org/license/
###############################################################################
import os
import shutil
import tempfile
import unittest
import platform
import http.client
import json
import time

import numpy
import vigra
import h5py
import pytest

from lazyflow.graph import Graph
from lazyflow.roi import roiFromShape
from lazyflow.operators import OpArrayPiper
from lazyflow.operators.ioOperators import OpExportSlot, OpInputDataReader

TEST_DVID_SERVER = os.getenv("TEST_DVID_SERVER", None)
if TEST_DVID_SERVER is None:
    pytest.skip("skipping DVID tests, Environment variable TEST_DVID_SERVER is not specified", allow_module_level=True)

try:
    from lazyflow.operators.ioOperators import OpExportDvidVolume
    from libdvid import DVIDConnection, ConnectionMethod, DVIDNodeService
    from libdvid.voxels import VoxelsMetadata, VoxelsAccessor

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

    def delete_all_data_instances(uuid):
        connection = DVIDConnection(TEST_DVID_SERVER)
        repo_info_uri = "/repo/{uuid}/info".format(uuid=uuid)
        status, body, error_message = connection.make_request(repo_info_uri, ConnectionMethod.GET)
        assert status == http.client.OK, "Request for {} returned status {}".format(repo_info_uri, status)
        assert error_message == ""
        repo_info = json.loads(body)
        for instance_name in list(repo_info["DataInstances"].keys()):
            status, body, error_message = connection.make_request(
                "/api/repo/{uuid}/{dataname}?imsure=true".format(uuid=uuid, dataname=str(instance_name)),
                ConnectionMethod.DELETE,
            )


except ImportError:
    have_dvid = False
else:
    have_dvid = True


class TestOpDvidVolume(unittest.TestCase):
    @unittest.skipIf(True, "FIXME: OpExportDvidVolume doesn't work any more....")
    @unittest.skipIf(not have_dvid, "optional module libdvid not available.")
    @unittest.skipIf(platform.system() == "Windows", "DVID not tested on Windows. Skipping.")
    def setup_method(self, method):
        """
        Override.  Called by nosetests.
        """
        # Choose names
        self.hostname = TEST_DVID_SERVER
        self.dvid_repo = "datasetA"
        self.data_name = "exported_data_{}".format(time.time())
        self.data_uuid = get_testrepo_root_uuid()

    def teardown_method(self, method):
        """
        Override.  Called by nosetests.
        """
        delete_all_data_instances(self.data_uuid)

    def test_export(self):
        # For now, we require block-aligned POST
        data = numpy.random.randint(0, 255, (32, 128, 256, 1)).astype(numpy.uint8)
        data = numpy.asfortranarray(data, numpy.uint8)
        assert data.shape == (32, 128, 256, 1)
        data = data.astype(numpy.uint8)
        data = vigra.taggedView(data, vigra.defaultAxistags("zyxc"))

        # Retrieve from server
        graph = Graph()

        opPiper = OpArrayPiper(graph=graph)
        opPiper.Input.setValue(data)

        opExport = OpExportDvidVolume(transpose_axes=True, graph=graph)

        # Reverse data order for dvid export
        opExport.Input.connect(opPiper.Output)
        opExport.NodeDataUrl.setValue(
            "http://localhost:8000/api/node/{uuid}/{dataname}".format(uuid=self.data_uuid, dataname=self.data_name)
        )

        # Export!
        opExport.run_export()

        # Read back. (transposed, because of transposed_axes, above)
        accessor = VoxelsAccessor(TEST_DVID_SERVER, self.data_uuid, self.data_name)
        read_data = accessor[:]

        # Compare.
        assert (data.view(numpy.ndarray) == read_data.transpose()).all(), "Exported data is not correct"

    def test_export_with_offset(self):
        """
        For now, the offset and data must both be block-aligned for DVID.
        """
        data = numpy.random.randint(0, 255, (32, 128, 256, 1)).astype(numpy.uint8)
        data = numpy.asfortranarray(data, numpy.uint8)
        assert data.shape == (32, 128, 256, 1)
        data = vigra.taggedView(data, vigra.defaultAxistags("zyxc"))

        # Retrieve from server
        graph = Graph()

        opPiper = OpArrayPiper(graph=graph)
        opPiper.Input.setValue(data)

        opExport = OpExportDvidVolume(transpose_axes=True, graph=graph)

        # Reverse data order for dvid export
        opExport.Input.connect(opPiper.Output)
        opExport.NodeDataUrl.setValue(
            "http://localhost:8000/api/node/{uuid}/{dataname}".format(uuid=self.data_uuid, dataname=self.data_name)
        )
        offset = (32, 64, 128, 0)
        opExport.OffsetCoord.setValue(offset)

        # Export!
        opExport.run_export()

        # Read back. (transposed, because of transposed_axes, above)
        accessor = VoxelsAccessor(TEST_DVID_SERVER, self.data_uuid, self.data_name)
        read_data = accessor[:]

        # The offset should have caused larger extents in the saved data.
        assert (read_data.transpose().shape == numpy.add(data.shape, offset)).all(), "Wrong shape: {}".format(
            exported_data.transpose().shape
        )

        # Compare.
        offset_slicing = tuple(slice(s, None) for s in offset)
        assert (data.view(numpy.ndarray) == read_data.transpose()[offset_slicing]).all(), "Exported data is not correct"

    def test_via_OpExportSlot(self):
        data = 255 * numpy.random.random((64, 128, 128, 1))
        data = data.astype(numpy.uint8)
        data = vigra.taggedView(data, vigra.defaultAxistags("zyxc"))

        graph = Graph()

        opPiper = OpArrayPiper(graph=graph)
        opPiper.Input.setValue(data)

        opExport = OpExportSlot(graph=graph)
        opExport.Input.connect(opPiper.Output)
        opExport.OutputFormat.setValue("dvid")
        url = "http://{hostname}/api/node/{data_uuid}/{data_name}".format(**self.__dict__)
        opExport.OutputFilenameFormat.setValue(url)

        assert opExport.ExportPath.ready()
        assert opExport.ExportPath.value == url

        opExport.run_export()

        opRead = OpInputDataReader(graph=graph)
        try:
            opRead.FilePath.setValue(opExport.ExportPath.value)
            expected_data = data.view(numpy.ndarray)
            read_data = opRead.Output(*roiFromShape(data.shape)).wait()
            assert (read_data == expected_data).all(), "Read data didn't match exported data!"
        finally:
            opRead.cleanUp()


if __name__ == "__main__":
    import sys
    import nose

    sys.argv.append("--nocapture")  # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture")  # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
