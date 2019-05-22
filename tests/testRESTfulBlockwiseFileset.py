from builtins import object

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
import sys
import shutil
import tempfile
import numpy
import h5py
import nose
import platform

from lazyflow.roi import sliceToRoi

import logging

logger = logging.getLogger(__name__)

from lazyflow.utility.io_util.blockwiseFileset import BlockwiseFileset
from lazyflow.utility.io_util.RESTfulBlockwiseFileset import RESTfulBlockwiseFileset


class TestRESTFullBlockwiseFilset(object):
    @classmethod
    def setup_class(cls):
        # The openconnectome site appears to be down at the moment.
        # This test fails when that happens...
        raise nose.SkipTest

        if platform.system() == "Windows":
            # On windows, there are errors, and we make no attempt to solve them (at the moment).
            raise nose.SkipTest

        try:
            BlockwiseFileset._prepare_system()
        except ValueError:
            # If the system isn't configured to allow lots of open files, we can't run this test.
            raise nose.SkipTest

        cls.tempDir = tempfile.mkdtemp()
        logger.debug("Working in {}".format(cls.tempDir))

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
            "bounds" : [4156, 135424, 119808],
            "dtype" : "numpy.uint8",
            "url_format" : "http://openconnecto.me/ocp/ca/bock11/hdf5/0/{x_start},{x_stop}/{y_start},{y_stop}/{z_start},{z_stop}/",
            "hdf5_dataset" : "CUTOUT"
        }
        """

        blockwiseFilesetDescription = """
        {
            "_schema_name" : "blockwise-fileset-description",
            "_schema_version" : 1.0,

            "name" : "bock11-blocks",
            "format" : "hdf5",
            "axes" : "zyx",
            "shape" : [40,40,40],
            "dtype" : "numpy.uint8",
            "block_shape" : [20, 20, 20],
            "block_file_name_format" : "block-{roiString}.h5/CUTOUT",
            "dataset_root_dir" : "blocks"
        }
        """

        # Combine them into the composite description (see RESTfulBlockwiseFileset.DescriptionFields)
        compositeDescription = """
        {{
            "_schema_name" : "RESTful-blockwise-fileset-description",
            "_schema_version" : 1.0,

            "remote_description" : {remote_description},
            "local_description" : {local_description}
        }}
        """.format(
            remote_description=Bock11VolumeDescription, local_description=blockwiseFilesetDescription
        )

        # Create the description file
        cls.descriptionFilePath = os.path.join(cls.tempDir, "description.json")
        with open(cls.descriptionFilePath, "w") as f:
            f.write(compositeDescription)

        # Create a new fileset that views the same data and stores it the
        #  same way locally, but this time we'll use an offset 'view'
        # Start with a copy of the non-offset description
        offsetDescription = RESTfulBlockwiseFileset.readDescription(cls.descriptionFilePath)
        offsetDescription.local_description.view_origin = numpy.array([0, 20, 0])
        offsetDescription.local_description.dataset_root_dir = "offset_blocks"
        cls.descriptionFilePath_offset = os.path.join(cls.tempDir, "description_offset.json")
        RESTfulBlockwiseFileset.writeDescription(cls.descriptionFilePath_offset, offsetDescription)

    @classmethod
    def teardown_class(cls):
        # If the user is debugging, don't clear the files we're testing with.
        if logger.level > logging.DEBUG:
            shutil.rmtree(cls.tempDir)

    def test_1_SingleDownload(self):
        volume = RESTfulBlockwiseFileset(self.descriptionFilePath)

        slicing = numpy.s_[0:20, 0:20, 0:20]
        roi = sliceToRoi(slicing, volume.description.shape)
        data = volume.readData(roi)
        assert data.shape == (20, 20, 20)

        assert volume.getBlockStatus(([0, 0, 0])) == BlockwiseFileset.BLOCK_AVAILABLE

    def test_2_MultiDownload(self):
        volume = RESTfulBlockwiseFileset(self.descriptionFilePath)

        slicing = numpy.s_[0:25, 10:30, 0:20]
        roi = sliceToRoi(slicing, volume.description.shape)
        data = volume.readData(roi)
        assert data.shape == (25, 20, 20)

        assert volume.getBlockStatus(([0, 0, 0])) == BlockwiseFileset.BLOCK_AVAILABLE
        assert volume.getBlockStatus(([20, 0, 0])) == BlockwiseFileset.BLOCK_AVAILABLE
        assert volume.getBlockStatus(([20, 20, 0])) == BlockwiseFileset.BLOCK_AVAILABLE
        assert volume.getBlockStatus(([0, 20, 0])) == BlockwiseFileset.BLOCK_AVAILABLE

    def test_4_OffsetDownload(self):
        volume = RESTfulBlockwiseFileset(self.descriptionFilePath)

        slicing = numpy.s_[20:40, 20:40, 20:40]
        roi = sliceToRoi(slicing, volume.description.shape)
        data = volume.readData(roi)
        assert data.shape == (20, 20, 20)
        assert volume.getBlockStatus(([20, 20, 20])) == BlockwiseFileset.BLOCK_AVAILABLE

        offsetVolume = RESTfulBlockwiseFileset(self.descriptionFilePath_offset)
        offsetSlicing = numpy.s_[20:40, 0:20, 20:40]  # Note middle slice is offset (see view_origin in setup_class)
        offsetRoi = sliceToRoi(offsetSlicing, offsetVolume.description.shape)
        offsetData = offsetVolume.readData(offsetRoi)
        assert offsetData.shape == (20, 20, 20)
        assert offsetVolume.getBlockStatus(([20, 0, 20])) == BlockwiseFileset.BLOCK_AVAILABLE

        # Data should be the same
        assert (offsetData == data).all()


if __name__ == "__main__":
    import sys
    import nose

    sys.argv.append("--nocapture")  # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture")  # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)

    if not ret:
        sys.exit(1)
