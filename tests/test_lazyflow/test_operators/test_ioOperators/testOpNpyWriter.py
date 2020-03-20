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
import shutil

import numpy
import vigra

from lazyflow.graph import Graph
from lazyflow.operators import OpArrayPiper
from lazyflow.operators.ioOperators import OpInputDataReader, OpNpyWriter


class TestOpNpyWriter(object):
    @classmethod
    def setup_class(cls):
        cls._tmpdir = tempfile.mkdtemp()

    @classmethod
    def teardown_class(cls):
        shutil.rmtree(cls._tmpdir)

    def testBasic(self):
        data = numpy.random.random((100, 100)).astype(numpy.float32)
        data = vigra.taggedView(data, vigra.defaultAxistags("xy"))

        graph = Graph()

        opPiper = OpArrayPiper(graph=graph)
        opPiper.Input.setValue(data)

        opWriter = OpNpyWriter(graph=graph)
        opWriter.Input.connect(opPiper.Output)
        opWriter.Filepath.setValue(self._tmpdir + "/npy_writer_test_output.npy")

        # Write it...
        opWriter.write()

        opRead = OpInputDataReader(graph=graph)
        try:
            opRead.FilePath.setValue(opWriter.Filepath.value)
            expected_data = data.view(numpy.ndarray)
            read_data = opRead.Output[:].wait()
            assert (read_data == expected_data).all(), "Read data didn't match exported data!"
        finally:
            opRead.cleanUp()


if __name__ == "__main__":
    import sys
    import nose

    sys.argv.append("--nocapture")  # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture")  # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
