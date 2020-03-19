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
from lazyflow.roi import sliceToRoi
from lazyflow.utility.io_util.RESTfulVolume import RESTfulVolume

import logging

logger = logging.getLogger(__name__)


class TestRESTfulVolume(object):
    def testBasic(self):
        """
        Requires access to the Internet...
        """
        # The openconnectome site appears to be down at the moment.
        # This test fails when that happens...
        import nose

        raise nose.SkipTest

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
            "url_format" : "http://openconnecto.me/ocp/ca/bock11/hdf5/0/{x_start},{x_stop}/{y_start},{y_stop}/{z_start},{z_stop}/",
            "hdf5_dataset" : "CUTOUT"
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
            "url_format" : "http://openconnecto.me/ocp/ca/bock11/hdf5/4/{x_start},{x_stop}/{y_start},{y_stop}/{z_start},{z_stop}/",
            "hdf5_dataset" : "CUTOUT"
        }
        """

        # Create the description file.
        tempDir = tempfile.mkdtemp()
        descriptionFilePath = os.path.join(tempDir, "desc.json")
        with open(descriptionFilePath, "w") as descFile:
            descFile.write(testConfig0)

        # Create the volume object
        volume = RESTfulVolume(descriptionFilePath)

        # slicing = numpy.s_[0:100, 4000:4200, 4000:4200]
        slicing = numpy.s_[0:25, 50000:50050, 50000:50075]
        roi = sliceToRoi(slicing, volume.description.shape)
        outputFile = os.path.join(tempDir, "volume.h5")
        datasetPath = outputFile + "/cube"
        logger.debug("Downloading subvolume to: {}".format(datasetPath))
        volume.downloadSubVolume(roi, datasetPath)

        with h5py.File(outputFile, "r") as hdf5File:
            data = hdf5File["cube"]
            assert data.shape == (25, 50, 75)

        shutil.rmtree(tempDir)


if __name__ == "__main__":
    import sys
    import nose

    sys.argv.append("--nocapture")  # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture")  # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)
    if not ret:
        sys.exit(1)
