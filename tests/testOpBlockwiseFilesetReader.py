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
from lazyflow.utility.io_util.blockwiseFileset import BlockwiseFileset
from lazyflow.operators.ioOperators import OpBlockwiseFilesetReader

import logging

logger = logging.getLogger(__name__)


class TestOpBlockwiseFilesetReader(object):
    def setup_method(self, method):
        """
        Create a blockwise fileset to test with.
        """
        if platform.system() == "Windows":
            # On windows, there are errors, and we make no attempt to solve them (at the moment).
            raise nose.SkipTest

        try:
            BlockwiseFileset._prepare_system()
        except ValueError:
            # If the system isn't configured to allow lots of open files, we can't run this test.
            raise nose.SkipTest

        testConfig = """
        {
            "_schema_name" : "blockwise-fileset-description",
            "_schema_version" : 1.0,

            "name" : "synapse_small",
            "format" : "hdf5",
            "axes" : "txyzc",
            "shape" : [1,400,400,100,1],
            "dtype" : "numpy.uint8",
            "block_shape" : [1, 50, 50, 50, 100],
            "block_file_name_format" : "cube{roiString}.h5/volume/data"
        }
        """
        self.tempDir = tempfile.mkdtemp()
        self.configpath = os.path.join(self.tempDir, "config.json")

        logger.debug("Loading config file...")
        with open(self.configpath, "w") as f:
            f.write(testConfig)

        logger.debug("Creating random test data...")
        bfs = BlockwiseFileset(self.configpath, "a")
        dataShape = tuple(bfs.description.shape)
        self.data = numpy.random.randint(255, size=dataShape).astype(numpy.uint8)

        logger.debug("Writing test data...")
        datasetRoi = ([0, 0, 0, 0, 0], dataShape)
        bfs.writeData(datasetRoi, self.data)
        block_starts = getIntersectingBlocks(bfs.description.block_shape, datasetRoi)
        for block_start in block_starts:
            bfs.setBlockStatus(block_start, BlockwiseFileset.BLOCK_AVAILABLE)
        bfs.close()

    def teardown_method(self, method):
        shutil.rmtree(self.tempDir)

    def testRead(self):
        graph = Graph()
        op = OpBlockwiseFilesetReader(graph=graph)
        op.DescriptionFilePath.setValue(self.configpath)

        slice1 = numpy.s_[:, 20:150, 20:150, 20:100, :]
        readData = op.Output[slice1].wait()
        assert (readData == self.data[slice1]).all()
        op.cleanUp()


if __name__ == "__main__":
    import sys
    import nose

    sys.argv.append("--nocapture")  # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture")  # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)

    if not ret:
        sys.exit(1)
