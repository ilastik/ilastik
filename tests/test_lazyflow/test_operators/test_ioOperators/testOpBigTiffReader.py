###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2017, the ilastik developers
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
#          http://ilastik.org/license/
###############################################################################
import logging
import os
import shutil
import tempfile
import unittest

import numpy
import pytiff
import vigra

from lazyflow.graph import Graph
from lazyflow.operators.ioOperators import OpBigTiffReader


logger = logging.getLogger(__name__)


class TestOpBigTiffReader(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Generate some example data, write data as bigtiff using pytiff"""
        cls.tmp_data_folder = tempfile.mkdtemp()
        cls.test_file_name = f"{cls.tmp_data_folder}/bigtiff_testfile.tif"

        cls.data = numpy.random.randint(0, 255, (800, 1200)).astype("uint8")
        try:
            t = pytiff.Tiff(cls.test_file_name, file_mode="w", bigtiff=True)
            t.write(cls.data)
        finally:
            t.close()

    @classmethod
    def teardown_class(cls):
        shutil.rmtree(cls.tmp_data_folder)

    def test_is_obsolete(self):
        """Check if vigra can read it

        if vigra can read those tiffs, obBigTiffReader is obsolete
        """
        self.assertRaises(RuntimeError, vigra.impex.readImage, self.test_file_name)

    def test_read_bigtiff(self):
        g = Graph()
        op = OpBigTiffReader(graph=g)
        op.Filepath.setValue(self.test_file_name)

        self.assertTrue(op.Output.ready())

        self.assertEqual(op.Output.meta.shape, self.data.shape)
        output_data = op.Output[:].wait()

        # clean up closes tiff file, which prevents PermissionError on Windows
        op.cleanUp()

        numpy.testing.assert_array_equal(output_data, self.data)


if __name__ == "__main__":
    # Run this file independently to see debug output.
    import sys
    import nose

    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler(sys.stdout))

    ioOpLogger = logging.getLogger("lazyflow.operators.ioOperators")
    ioOpLogger.addHandler(logging.StreamHandler(sys.stdout))
    ioOpLogger.setLevel(logging.DEBUG)

    sys.argv.append("--nocapture")  # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture")  # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
