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
#		   http://ilastik.org/license/
###############################################################################
from lazyflow.graph import Graph
from lazyflow.operators.ioOperators import OpStreamingN5Reader
import z5py
import numpy
import os
import vigra

class TestOpStreamingN5Reader(object):

    def setUp(self):
        self.graph = Graph()
        self.testDataFileName = 'test.n5'
        self.op = OpStreamingN5Reader(graph=self.graph)

        self.n5File = z5py.N5File(self.testDataFileName, 'w')
        self.n5File.create_group('volume')

        # Create a test dataset
        datashape = (1,2,3,4,5)
        self.data = numpy.indices(datashape).sum(0).astype(numpy.float32)

    def tearDown(self):
        self.n5File.close()
        try:
            os.remove(self.testDataFileName)
        except:
            pass

    def test_plain(self):
        """Write the dataset to an n5 file"""
        self.n5File['volume'].create_dataset('data', data=self.data)

        # Read the data with an operator
        self.op.N5File.setValue(self.n5File)
        self.op.InternalPath.setValue('volume/data')

        assert self.op.OutputImage.meta.shape == self.data.shape
        assert self.op.OutputImage[0,1,2,1,0].wait() == 4

    def test_withAxisTags(self):
        """Write it again, this time with weird axistags"""
        axistags = vigra.AxisTags(
            vigra.AxisInfo('x',vigra.AxisType.Space),
            vigra.AxisInfo('y',vigra.AxisType.Space),
            vigra.AxisInfo('z',vigra.AxisType.Space),
            vigra.AxisInfo('c',vigra.AxisType.Channels),
            vigra.AxisInfo('t',vigra.AxisType.Time))

        # Write the dataset to an n5 file
        # (Note: Don't use vigra to do this, which may reorder the axes)
        self.n5File['volume'].create_dataset('tagged_data', data=self.data)
        # Write the axistags attribute
        self.n5File['volume/tagged_data'].attrs['axistags'] = axistags.toJSON()

        # Read the data with an operator
        self.op.N5File.setValue(self.n5File)
        self.op.InternalPath.setValue('volume/tagged_data')

        assert self.op.OutputImage.meta.shape == self.data.shape
        assert self.op.OutputImage[0,1,2,1,0].wait() == 4

if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")  # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture")  # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)
    if not ret: sys.exit(1)
