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
import platform

import nose
import numpy
import vigra

from lazyflow.graph import Graph
from lazyflow.utility import PathComponents
from lazyflow.roi import roiFromShape
from lazyflow.operators.operators import OpArrayPiper
from lazyflow.operators import OpBlockedArrayCache
from lazyflow.operators.opReorderAxes import OpReorderAxes
from lazyflow.operators.ioOperators import OpInputDataReader, OpExportSlot, OpStackLoader
from lazyflow.operators.ioOperators.opTiffSequenceReader import OpTiffSequenceReader


class TestOpExportSlot(object):
    @classmethod
    def setup_class(cls):
        cls._tmpdir = tempfile.mkdtemp()

    @classmethod
    def teardown_class(cls):
        shutil.rmtree(cls._tmpdir)

    def testBasic_Hdf5(self):
        data = numpy.random.random((100, 100)).astype(numpy.float32)
        data = vigra.taggedView(data, vigra.defaultAxistags("xy"))

        graph = Graph()
        opPiper = OpArrayPiper(graph=graph)
        opPiper.Input.setValue(data)

        opExport = OpExportSlot(graph=graph)
        opExport.Input.connect(opPiper.Output)
        opExport.OutputFormat.setValue("hdf5")
        opExport.OutputFilenameFormat.setValue(self._tmpdir + "/test_export_x{x_start}-{x_stop}_y{y_start}-{y_stop}")
        opExport.OutputInternalPath.setValue("volume/data")
        opExport.CoordinateOffset.setValue((10, 20))

        assert opExport.ExportPath.ready()
        export_file = PathComponents(opExport.ExportPath.value).externalPath
        assert os.path.split(export_file)[1] == "test_export_x10-110_y20-120.h5"
        # print "exporting data to: {}".format( opExport.ExportPath.value )
        opExport.run_export()

        opRead = OpInputDataReader(graph=graph)
        try:
            opRead.FilePath.setValue(opExport.ExportPath.value)
            expected_data = data.view(numpy.ndarray)
            read_data = opRead.Output[:].wait()
            assert (read_data == expected_data).all(), "Read data didn't match exported data!"
        finally:
            opRead.cleanUp()

    def testBasic_Npy(self):
        data = numpy.random.random((100, 100)).astype(numpy.float32)
        data = vigra.taggedView(data, vigra.defaultAxistags("xy"))

        graph = Graph()
        opPiper = OpArrayPiper(graph=graph)
        opPiper.Input.setValue(data)

        opExport = OpExportSlot(graph=graph)
        opExport.Input.connect(opPiper.Output)
        opExport.OutputFormat.setValue("numpy")
        opExport.OutputFilenameFormat.setValue(self._tmpdir + "/test_export_x{x_start}-{x_stop}_y{y_start}-{y_stop}")
        opExport.CoordinateOffset.setValue((10, 20))

        assert opExport.ExportPath.ready()
        assert os.path.split(opExport.ExportPath.value)[1] == "test_export_x10-110_y20-120.npy"
        # print "exporting data to: {}".format( opExport.ExportPath.value )
        opExport.run_export()

        opRead = OpInputDataReader(graph=graph)
        try:
            opRead.FilePath.setValue(opExport.ExportPath.value)
            expected_data = data.view(numpy.ndarray)
            read_data = opRead.Output[:].wait()
            assert (read_data == expected_data).all(), "Read data didn't match exported data!"
        finally:
            opRead.cleanUp()

    # Support for DVID export is tested in testOpDvidExport.py
    # def testBasic_Dvid(self):
    #    pass

    def testBasic_2d(self):
        data = 255 * numpy.random.random((50, 100))
        data = data.astype(numpy.uint8)
        data = vigra.taggedView(data, vigra.defaultAxistags("yx"))

        graph = Graph()

        opPiper = OpArrayPiper(graph=graph)
        opPiper.Input.setValue(data)

        opExport = OpExportSlot(graph=graph)
        opExport.Input.connect(opPiper.Output)
        opExport.OutputFormat.setValue("png")
        opExport.OutputFilenameFormat.setValue(self._tmpdir + "/test_export_x{x_start}-{x_stop}_y{y_start}-{y_stop}")
        opExport.CoordinateOffset.setValue((10, 20))

        assert opExport.ExportPath.ready()
        assert os.path.split(opExport.ExportPath.value)[1] == "test_export_x20-120_y10-60.png"
        opExport.run_export()

        opRead = OpInputDataReader(graph=graph)
        try:
            opRead.FilePath.setValue(opExport.ExportPath.value)
            expected_data = data.view(numpy.ndarray)
            read_data = opRead.Output[:].wait()

            # Note: vigra inserts a channel axis, so read_data is xyc
            assert (read_data[..., 0] == expected_data).all(), "Read data didn't match exported data!"
        finally:
            opRead.cleanUp()

    def testBasic_2d_Sequence(self):
        data = 255 * numpy.random.random((10, 50, 100, 3))
        data = data.astype(numpy.uint8)
        data = vigra.taggedView(data, vigra.defaultAxistags("zyxc"))

        # Must run this through an operator
        # Can't use opExport.setValue() because because OpStackWriter can't work with ValueRequests
        graph = Graph()
        opData = OpBlockedArrayCache(graph=graph)
        opData.BlockShape.setValue(data.shape)
        opData.Input.setValue(data)

        filepattern = self._tmpdir + "/test_export_x{x_start}-{x_stop}_y{y_start}-{y_stop}_z{slice_index}"
        opExport = OpExportSlot(graph=graph)
        opExport.Input.connect(opData.Output)
        opExport.OutputFormat.setValue("png sequence")
        opExport.OutputFilenameFormat.setValue(filepattern)
        opExport.CoordinateOffset.setValue((10, 20, 30, 0))

        opExport.run_export()

        export_pattern = opExport.ExportPath.value
        globstring = export_pattern.format(slice_index=999)
        globstring = globstring.replace("999", "*")

        opReader = OpStackLoader(graph=graph)
        try:
            opReader.globstring.setValue(globstring)

            assert opReader.stack.meta.shape == data.shape, "Exported files were of the wrong shape or number."
            assert (opReader.stack[:].wait() == data.view(numpy.ndarray)).all(), "Exported data was not correct"
        finally:
            opReader.cleanUp()

    def testBasic_MultipageTiffSequence(self):
        data = 255 * numpy.random.random((5, 10, 50, 100, 3))
        data = data.astype(numpy.uint8)
        data = vigra.taggedView(data, vigra.defaultAxistags("tzyxc"))

        # Must run this through an operator
        # Can't use opExport.setValue() because because OpStackWriter can't work with ValueRequests
        graph = Graph()
        opData = OpBlockedArrayCache(graph=graph)
        opData.BlockShape.setValue(data.shape)
        opData.Input.setValue(data)

        filepattern = self._tmpdir + "/test_export_x{x_start}-{x_stop}_y{y_start}-{y_stop}_t{slice_index}"
        opExport = OpExportSlot(graph=graph)
        opExport.Input.connect(opData.Output)
        opExport.OutputFormat.setValue("multipage tiff sequence")
        opExport.OutputFilenameFormat.setValue(filepattern)
        opExport.CoordinateOffset.setValue((7, 10, 20, 30, 0))

        opExport.run_export()

        export_pattern = opExport.ExportPath.value
        globstring = export_pattern.format(slice_index=999)
        globstring = globstring.replace("999", "*")

        opReader = OpTiffSequenceReader(graph=graph)
        opReorderAxes = OpReorderAxes(graph=graph)

        try:
            opReader.GlobString.setValue(globstring)

            # (The OpStackLoader produces txyzc order.)
            opReorderAxes.AxisOrder.setValue("tzyxc")
            opReorderAxes.Input.connect(opReader.Output)

            assert opReorderAxes.Output.meta.shape == data.shape, "Exported files were of the wrong shape or number."
            assert (opReorderAxes.Output[:].wait() == data.view(numpy.ndarray)).all(), "Exported data was not correct"

        finally:
            opReorderAxes.cleanUp()
            opReader.cleanUp()

    def testInvalidDim2d(self):
        data = 255 * numpy.random.random((50, 100, 2))
        data = data.astype(numpy.uint8)
        data = vigra.taggedView(data, vigra.defaultAxistags("xyz"))

        graph = Graph()
        opExport = OpExportSlot(graph=graph)
        opExport.Input.setValue(data)
        opExport.OutputFilenameFormat.setValue(self._tmpdir + "/test_export")

        for fmt in ("jpg", "png", "pnm", "bmp"):
            opExport.OutputFormat.setValue(fmt)
            msg = opExport.FormatSelectionErrorMsg.value
            assert msg, "{} supported although it is actually not".format(fmt)

        for fmt in ("hdf5", "multipage tiff"):
            opExport.OutputFormat.setValue(fmt)
            msg = opExport.FormatSelectionErrorMsg.value
            assert not msg, "{} not supported although it should be ({})".format(fmt, msg)

    def testInvalidDtype(self):
        data = 255 * numpy.random.random((50, 100))
        data = data.astype(numpy.uint32)
        data = vigra.taggedView(data, vigra.defaultAxistags("xy"))

        graph = Graph()
        opExport = OpExportSlot(graph=graph)
        opExport.Input.setValue(data)
        opExport.OutputFilenameFormat.setValue(self._tmpdir + "/test_export")

        for fmt in ("jpg", "png", "pnm", "bmp"):
            opExport.OutputFormat.setValue(fmt)
            msg = opExport.FormatSelectionErrorMsg.value
            assert msg, "{} supported although it is actually not".format(fmt)


if __name__ == "__main__":
    import sys
    import nose
    import logging

    handler = logging.StreamHandler(sys.stdout)
    logging.getLogger().addHandler(handler)

    sys.argv.append("--nocapture")  # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture")  # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
