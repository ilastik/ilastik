import shutil
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
import tempfile
from builtins import object

import numpy
import pytest
import vigra

from lazyflow.graph import Graph
from lazyflow.operators.ioOperators import OpFormattedDataExport, OpInputDataReader
from lazyflow.operators.ioOperators.opFormattedDataExport import normalize
from lazyflow.roi import roiToSlice


@pytest.mark.parametrize(
    "target_dtype", [numpy.uint8, numpy.uint16, numpy.uint32, numpy.uint64, numpy.float32, numpy.float64]
)
def test_normalize_rounds_float_imprecision(target_dtype):
    """
    Special case when normalizing float probabilities from 0.0 ... 1.0 to int range 0 ... 100
    Probabilities are integer percentages (0.00, 0.01, 0.02 etc.), so there are 101 unique values
    from 0.0 to 1.0. They should map to 101 unique values from 0 to 100 regardless of output dtype.

    Doing maths may introduce float imprecision:
    list((np.arange(0, 101, dtype=np.float64) / 100 * 100.0)[[29, 57, 58]])
    [28.999999999999996, 56.99999999999999, 57.99999999999999]
    Simply casting to integer dtypes converts these to 28, 56 and 57 respectively, instead of 29, 57 and 58.
    """
    probabilities = numpy.arange(0, 101, dtype=numpy.float64) / 100
    normalized = normalize(probabilities, drange_in=(0.0, 1.0), drange_out=(0, 100), dtype_out=target_dtype)
    assert len(numpy.unique(probabilities)) == len(
        numpy.unique(normalized)
    ), "Expected 101 values before and after normalization"
    numpy.testing.assert_array_equal(numpy.round(probabilities * 100), numpy.round(normalized))


class TestOpFormattedDataExport(object):
    @classmethod
    def setup_class(cls):
        cls._tmpdir = tempfile.mkdtemp()

    @classmethod
    def teardown_class(cls):
        shutil.rmtree(cls._tmpdir)

    def testConvertOnly(self):
        """
        Choosing only conversion, not normalization, bypasses the `normalize` function.
        In this case we expect a simple dtype casting - without rounding values.
        """
        graph = Graph()
        opExport = OpFormattedDataExport(graph=graph)

        data = numpy.random.random((100, 100)).astype(numpy.float32) * 100
        data = vigra.taggedView(data, vigra.defaultAxistags("xy"))
        data[0, 0] = numpy.float32(0.5)  # make sure there are some edge cases
        data[0, 1] = numpy.float32(0.0000000001)
        data[0, 2] = numpy.float32(0.9999999999)
        opExport.Input.setValue(data)
        opExport.ExportDtype.setValue(numpy.uint8)

        opExport.OutputFormat.setValue("hdf5")
        opExport.OutputFilenameFormat.setValue(self._tmpdir + "/export")
        opExport.OutputInternalPath.setValue("volume/data")

        opExport.TransactionSlot.setValue(True)

        assert opExport.ImageToExport.ready()
        assert opExport.ExportPath.ready()
        assert opExport.ImageToExport.meta.dtype == numpy.uint8

        assert opExport.ExportPath.value == self._tmpdir + "/" + "export.h5/volume/data"
        opExport.run_export()

        opRead = OpInputDataReader(graph=graph)
        try:
            opRead.FilePath.setValue(opExport.ExportPath.value)

            expected_data = data.view(numpy.ndarray)[:].astype(numpy.uint8)

            assert opRead.Output.meta.shape == expected_data.shape
            assert opRead.Output.meta.dtype == expected_data.dtype
            read_data = opRead.Output[:].wait()

            numpy.testing.assert_array_equal(read_data, expected_data)
        finally:
            opRead.cleanUp()

    def testNormalize(self):
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
            read_data_signed = read_data.astype(numpy.int16)
            difference_from_expected = expected_data_signed - read_data_signed
            assert (numpy.abs(difference_from_expected) <= 1).all(), "Read data didn't match exported data!"
        finally:
            opRead.cleanUp()
