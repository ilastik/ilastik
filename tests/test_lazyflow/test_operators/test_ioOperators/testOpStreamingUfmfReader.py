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
import numpy as np
import vigra
from lazyflow.graph import Graph
from lazyflow.operators.ioOperators import OpStreamingUfmfReader
from lazyflow.operators.ioOperators import UfmfParser

VERSION = 3
WIDTH = 640
HEIGHT = 480
FRAME_NUM = 100

EXPECTED_DTYPE = np.uint8
EXPECTED_SHAPE = (100, 480, 640, 1)
EXPECTED_AXIS_ORDER = "tyxc"


class TestOpStreamingUfmfReader(object):
    def setup_method(self, method):
        # Write a simple uFMF video with 100 frames.
        tmpDir = tempfile.gettempdir()
        self.testUfmfFileName = os.path.join(tmpDir, "ufmfTestVideo.ufmf")

        if VERSION == 1:
            kwargs = dict(image_radius=radius)
        else:
            kwargs = dict(max_width=WIDTH, max_height=HEIGHT)

        frame0 = np.full((HEIGHT, WIDTH), 255, dtype=np.uint8)
        timestamp0 = 0

        ufmfFile = UfmfParser.UfmfSaver(self.testUfmfFileName, frame0, timestamp0, version=VERSION, **kwargs)

        pts = [(0, 0, WIDTH, HEIGHT)]

        for fmi in range(FRAME_NUM):
            frame = np.full((HEIGHT, WIDTH), 255, dtype=np.uint8)
            frame[
                (HEIGHT // FRAME_NUM) * fmi : (HEIGHT // FRAME_NUM) * fmi + FRAME_NUM,
                (WIDTH // FRAME_NUM) * fmi : (WIDTH // FRAME_NUM) * fmi + FRAME_NUM,
            ] = 50
            timestamp = fmi + 1
            ufmfFile.add_frame(frame, timestamp, pts)

        ufmfFile.close()

    def teardown_method(self, method):
        # Delete the ufmf test file.
        os.remove(self.testUfmfFileName)

    def test_OpStreamingUfmfReader(self):
        # Tests the ufmf reader operator, opening a small video that is created on setUp.
        self.graph = Graph()
        ufmfReader = OpStreamingUfmfReader(graph=self.graph)
        ufmfReader.FileName.setValue(self.testUfmfFileName)
        output = ufmfReader.Output[:].wait()

        # Verify shape, data type, and axis tags
        assert output.shape == EXPECTED_SHAPE
        assert ufmfReader.Output.meta.dtype == EXPECTED_DTYPE
        assert ufmfReader.Output.meta.axistags == vigra.defaultAxistags(EXPECTED_AXIS_ORDER)

        # There was a bug that accidentally caused the same frame to be duplicated
        # across all output frames if you requested more than one frame in a single request.
        # Here, we at least verify that the first frame and the last frame are not identical.
        assert not (output[0] == output[99]).all()

        # Clean reader
        ufmfReader.cleanUp()


if __name__ == "__main__":
    import nose

    ret = nose.run(defaultTest=__file__, env={"NOSE_NOCAPTURE": 1})
    if not ret:
        sys.exit(1)
