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
from lazyflow.roi import roiToSlice
from lazyflow.operators.ioOperators import OpInputDataReader, OpFormattedDataExport


class TestOpFormattedDataExport(object):
    @classmethod
    def setup_class(cls):
        cls._tmpdir = tempfile.mkdtemp()

    @classmethod
    def teardown_class(cls):
        shutil.rmtree(cls._tmpdir)

    def testBasic(self):
        graph = Graph()
        opExport = OpFormattedDataExport(graph=graph)

        data = numpy.random.random((100, 100)).astype(numpy.float32) * 100
        data = vigra.taggedView(data, vigra.defaultAxistags("xy"))
        opExport.Input.setValue(data)

        sub_roi = [(10, 0), (None, 80)]
        opExport.RegionStart.setValue(sub_roi[0])
        opExport.RegionStop.setValue(sub_roi[1])

        opExport.ExportDtype.setValue(numpy.uint8)

        opExport.InputMin.setValue(0.0)
        opExport.InputMax.setValue(100.0)
        opExport.ExportMin.setValue(100)
        opExport.ExportMax.setValue(200)

        opExport.OutputFormat.setValue("hdf5")
        opExport.OutputFilenameFormat.setValue(self._tmpdir + "/export_x{x_start}-{x_stop}_y{y_start}-{y_stop}")
        opExport.OutputInternalPath.setValue("volume/data")

        opExport.TransactionSlot.setValue(True)

        assert opExport.ImageToExport.ready()
        assert opExport.ExportPath.ready()
        assert opExport.ImageToExport.meta.drange == (100, 200)

        # print "exporting data to: {}".format( opExport.ExportPath.value )
        assert opExport.ExportPath.value == self._tmpdir + "/" + "export_x10-100_y0-80.h5/volume/data"
        opExport.run_export()

        opRead = OpInputDataReader(graph=graph)
        try:
            opRead.FilePath.setValue(opExport.ExportPath.value)

            # Compare with the correct subregion and convert dtype.
            sub_roi[1] = (100, 80)  # Replace 'None' with full extent
            expected_data = data.view(numpy.ndarray)[roiToSlice(*sub_roi)]
            expected_data = expected_data.astype(numpy.uint8)
            expected_data += 100  # see renormalization settings

            assert opRead.Output.meta.shape == expected_data.shape
            assert opRead.Output.meta.dtype == expected_data.dtype
            read_data = opRead.Output[:].wait()

            # Due to rounding errors, the actual result and the expected result may differ by 1
            #  e.g. if the original pixel value was 32.99999999
            # Also, must promote to signed values to avoid unsigned rollover
            # See issue ( https://github.com/ilastik/lazyflow/issues/165 ).
            expected_data_signed = expected_data.astype(numpy.int16)
            read_data_signed = expected_data.astype(numpy.int16)
            difference_from_expected = expected_data_signed - read_data_signed
            assert (numpy.abs(difference_from_expected) <= 1).all(), "Read data didn't match exported data!"
        finally:
            opRead.cleanUp()


if __name__ == "__main__":
    import sys
    import nose

    sys.argv.append("--nocapture")  # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture")  # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
