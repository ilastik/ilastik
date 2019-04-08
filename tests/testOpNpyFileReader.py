from builtins import range
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
import tempfile
import numpy
import lazyflow.graph
from lazyflow.operators.ioOperators import OpNpyFileReader


class TestOpNpyFileReader(object):
    def setup_method(self, method):
        self.graph = lazyflow.graph.Graph()
        tmpDir = tempfile.gettempdir()
        self.testDataFilePath = os.path.join(tmpDir, "NpyTestData.npy")
        # per default the arrays are named arr_0, arr_1... (see numpy.savez documentation)
        self.testDataFilePathNPZdefault = os.path.join(tmpDir, "NpzTestDataDefault.npz")
        self.testDataFilePathNPZnamed = os.path.join(tmpDir, "NpzTestDataNamed.npz")

        # Start by writing some test data to disk.
        self.testData = numpy.zeros((10, 11))
        for x in range(0, 10):
            for y in range(0, 11):
                self.testData[x, y] = x + y
        self.testDataB = numpy.arange(256, dtype=numpy.uint8).reshape((32, 8))

        numpy.save(self.testDataFilePath, self.testData)
        numpy.savez(self.testDataFilePathNPZdefault, self.testData, self.testDataB)
        numpy.savez(self.testDataFilePathNPZnamed, data_A=self.testData, data_B=self.testDataB)

    def teardown_method(self, method):
        # Clean up: Delete the test file.
        os.remove(self.testDataFilePath)

    def test_OpNpyFileReader(self):
        # Now read back our test data using an OpNpyFileReader operator
        npyReader = OpNpyFileReader(graph=self.graph)
        try:
            npyReader.FileName.setValue(self.testDataFilePath)

            # Read the entire file and verify the contents
            a = npyReader.Output[:].wait()
            assert a.shape == (10, 11)  # OpNpyReader automatically added a channel axis
            assert npyReader.Output.meta.dtype == self.testData.dtype

            # Why doesn't this work?  Numpy bug?
            # cmp = ( a == self.testData )
            # assert cmp.all()

            # Check each of the values
            for i in range(10):
                for j in range(11):
                    assert a[i, j] == self.testData[i, j]
        finally:
            npyReader.cleanUp()

    def test_OpNpyFileReaderNPZnamed(self):
        # Now read back our test data using an OpNpyFileReader operator
        npyReader = OpNpyFileReader(graph=self.graph)
        try:
            for internalPath, referenceData in zip(["data_A", "data_B"], [self.testData, self.testDataB]):
                npyReader.InternalPath.setValue("data_B")
                npyReader.FileName.setValue(self.testDataFilePathNPZnamed)

                # Read the entire file and verify the contents
                b = npyReader.Output[:].wait()
                assert b.shape == self.testDataB.shape
                assert npyReader.Output.meta.dtype == self.testDataB.dtype

                numpy.testing.assert_almost_equal(b, self.testDataB)
        finally:
            npyReader.cleanUp()


if __name__ == "__main__":
    import sys
    import nose

    sys.argv.append("--nocapture")  # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture")  # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)
    if not ret:
        sys.exit(1)
