from builtins import map
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
#           http://ilastik.org/license/
###############################################################################
import os
import tempfile
import shutil

import numpy
from lazyflow.graph import Graph
from lazyflow.operators.ioOperators import OpRawBinaryFileReader


class TestOpRawBinaryFileReader(object):
    def setup_method(self, method):
        # Start by writing some test data to disk.
        self.testData = numpy.random.random((10, 11, 12)).astype(numpy.float32)
        self.tmpDir = tempfile.mkdtemp()

        # Filename must follow conventions in used by OpRawBinaryFileReader
        shape_string = "-".join(map(str, self.testData.shape))
        self.testDataFilePath = os.path.join(self.tmpDir, "random-test-data-{}-float32.bin".format(shape_string))

        fp = numpy.memmap(self.testDataFilePath, dtype=self.testData.dtype, shape=self.testData.shape, mode="w+")
        fp[:] = self.testData
        del fp  # Close file

    def teardown_method(self, method):
        shutil.rmtree(self.tmpDir)

    def test_OpRawBinaryFileReader(self):
        # Now read back our test data using an OpRawBinaryFileReader operator
        op = OpRawBinaryFileReader(graph=Graph())
        try:
            op.FilePath.setValue(self.testDataFilePath)

            # Read the entire file and verify the contents
            a = op.Output[:].wait()
            assert (a == self.testData).all()

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
