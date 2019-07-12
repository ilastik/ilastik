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
import platform

import numpy
import nose

from lazyflow.graph import Graph
from lazyflow.roi import getIntersectingBlocks
from lazyflow.utility.io_util import RESTfulBlockwiseFileset
from lazyflow.operators.ioOperators import OpRESTfulBlockwiseFilesetReader

import logging

logger = logging.getLogger(__name__)


class TestOpBlockwiseFilesetReader(object):
    @classmethod
    def setup_class(cls):
        # The openconnectome site appears to be down at the moment.
        # This test fails when that happens...
        raise nose.SkipTest

        if platform.system() == "Windows":
            # On windows, there are errors, and we make no attempt to solve them (at the moment).
            raise nose.SkipTest

        try:
            from lazyflow.utility.io_util.blockwiseFileset import BlockwiseFileset

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
            "## NOTE 1": "The first z-slice of the bock dataset is 2917, so the origin_offset must be at least 2917",
            "## NOTE 2": "The website says that the data goes up to plane 4156, but it actually errors out past 4150",
            "origin_offset" : [2917, 0, 0],
            "bounds" : [4150, 135424, 119808],
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
            "block_file_name_format" : "block-{roiString}.h5/CUTOUT"
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

    @classmethod
    def teardown_class(cls):
        # If the user is debugging, don't clear the files we're testing with.
        if logger.level > logging.DEBUG:
            shutil.rmtree(cls.tempDir)

    def test_1_Read(self):
        graph = Graph()
        op = OpRESTfulBlockwiseFilesetReader(graph=graph)
        try:
            op.DescriptionFilePath.setValue(self.descriptionFilePath)

            logger.debug("test_1_Read(): Reading data")
            slice1 = numpy.s_[0:21, 5:27, 10:33]
            readData = op.Output[slice1].wait()
            assert readData.shape == (21, 22, 23)
        finally:
            op.cleanUp()

    def test_2_ReadTranslated(self):
        # Start by reading some data
        graph = Graph()
        op = OpRESTfulBlockwiseFilesetReader(graph=graph)
        try:
            op.DescriptionFilePath.setValue(self.descriptionFilePath)

            logger.debug("test_2_Read(): Reading data")
            slice1 = numpy.s_[20:30, 30:40, 20:30]
            readData = op.Output[slice1].wait()
            assert readData.shape == (10, 10, 10)

            logger.debug("test_2_Read(): Creating translated description")
            # Create a copy of the original description, but specify a translated (and smaller) view
            desc = RESTfulBlockwiseFileset.readDescription(self.descriptionFilePath)
            desc.view_origin = [20, 30, 20]
            offsetConfigPath = self.descriptionFilePath + "_offset"
            RESTfulBlockwiseFileset.writeDescription(offsetConfigPath, desc)

            # Read the same data as before using the translated view (offset our roi)
            opTranslated = OpRESTfulBlockwiseFilesetReader(graph=graph)
            try:
                opTranslated.DescriptionFilePath.setValue(offsetConfigPath)

                logger.debug("test_2_Read(): Reading translated data")
                sliceTranslated = numpy.s_[0:10, 0:10, 0:10]
                translatedReadData = op.Output[sliceTranslated].wait()
                assert translatedReadData.shape == (10, 10, 10)
                assert (translatedReadData == readData).all(), "Data doesn't match!"
            finally:
                opTranslated.cleanUp()
        finally:
            op.cleanUp()


if __name__ == "__main__":
    import sys
    import nose

    sys.argv.append("--nocapture")  # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture")  # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)

    if not ret:
        sys.exit(1)
