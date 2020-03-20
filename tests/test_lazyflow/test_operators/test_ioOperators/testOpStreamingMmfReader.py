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
import numpy as np
import vigra
from lazyflow.graph import Graph
from lazyflow.operators.ioOperators import OpStreamingMmfReader
import nose

EXPECTED_DTYPE = np.uint8
EXPECTED_SHAPE = (180, 2816, 2816, 1)
EXPECTED_AXIS_ORDER = "tyxc"
FILE_NAME = "zlatic_larvae_200frames.mmf"


class TestOpStreamingMmfReader(object):
    # In order for this tests to work, you need to include the file 'zlatic_larvae_200frames.mmf' in the same directory.
    # This file can be downloaded from the following GitHub repository: https://github.com/ilastik/ilastik_testdata

    def setup_method(self, method):
        self.fileName = FILE_NAME

    def teardown_method(self, method):
        pass

    def test_OpStreamingMmfReader(self):
        # Skip tests since the MMF video file is not found
        if not os.path.isfile(self.fileName):
            raise nose.SkipTest

        # Test the mmf streaming reading operator with a small video containing 180 frames
        self.graph = Graph()
        mmfReader = OpStreamingMmfReader(graph=self.graph)
        mmfReader.FileName.setValue(self.fileName)
        output = mmfReader.Output[:].wait()

        # Verify shape, data type, and axis tags
        assert output.shape == EXPECTED_SHAPE
        assert mmfReader.Output.meta.dtype == EXPECTED_DTYPE
        assert mmfReader.Output.meta.axistags == vigra.defaultAxistags(EXPECTED_AXIS_ORDER)

        # Clean reader
        mmfReader.cleanUp()


if __name__ == "__main__":
    import nose

    ret = nose.run(defaultTest=__file__, env={"NOSE_NOCAPTURE": 1})
    if not ret:
        sys.exit(1)
