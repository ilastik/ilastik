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
from pathlib import Path

import numpy
import vigra
import z5py

from lazyflow.graph import Graph
from lazyflow.operator import Operator
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

    def test_ome_zarr_without_internal_path(self):
        data = numpy.random.random((90, 100)).astype(numpy.float32)
        data = vigra.taggedView(data, vigra.defaultAxistags("yx"))

        graph = Graph()
        opPiper = OpArrayPiper(graph=graph)
        opPiper.Input.setValue(data)

        opExport = OpExportSlot(graph=graph)
        opExport.Input.connect(opPiper.Output)
        opExport.OutputFormat.setValue("single-scale OME-Zarr")
        opExport.OutputFilenameFormat.setValue(self._tmpdir + "/test_export_x{x_start}-{x_stop}_y{y_start}-{y_stop}")
        opExport.OutputInternalPath.setValue("")  # Overwrite the slot's default "exported_data"
        opExport.CoordinateOffset.setValue((10, 20))

        assert opExport.ExportPath.ready()
        export_path_components = PathComponents(opExport.ExportPath.value)
        expected_export_path = Path(self._tmpdir) / "test_export_x20-120_y10-100.zarr"
        assert Path(export_path_components.externalPath) == expected_export_path
        assert export_path_components.internalPath is None
        opExport.run_export()

        opRead = OpInputDataReader(graph=graph)
        try:
            opRead.FilePath.setValue(str(expected_export_path / "s0"))
            expected_data = data.view(numpy.ndarray).reshape((1, 1, 1) + data.shape)  # OME-Zarr always tczyx
            read_data = opRead.Output[:].wait()
            numpy.testing.assert_array_equal(read_data, expected_data)
        finally:
            opRead.cleanUp()

    def test_ome_zarr_roundtrip(self):
        """Ensure that loading an OME-Zarr dataset and then re-exporting one of
        its scales produces the same data and metadata."""
        input_meta = [
            {
                "name": "input.zarr",
                "type": "sample",
                "version": "0.4",
                "axes": [
                    {"type": "space", "name": "y", "unit": "nanometer"},
                    {"type": "space", "name": "x", "unit": "nanometer"},
                ],
                "datasets": [
                    {
                        "path": "s0",
                        "coordinateTransformations": [
                            {"scale": [0.2, 0.2], "type": "scale"},
                            {"translation": [0.0, 0.0], "type": "translation"},
                        ],
                    },
                    {
                        "path": "s1",
                        "coordinateTransformations": [
                            {"scale": [1.4, 1.4], "type": "scale"},
                            {"translation": [7.62, 8.49], "type": "translation"},
                        ],
                    },
                ],
                "coordinateTransformations": [
                    {"scale": [1.0, 1.0], "type": "scale"},
                    {"translation": [0.0, 0.0], "type": "translation"},
                ],
            }
        ]
        # Expected written meta is the same as input, but tczyx, only with the respective scale,
        # and with "exported_data" as the name (internal path is mandatory due to
        # OpExportData.OutputInternalPath having default="exported_data")
        expected_meta_s0 = [
            {
                "axes": [
                    {"name": "t", "type": "time"},
                    {"name": "c", "type": "channel"},
                    {"name": "z", "type": "space"},
                    {"name": "y", "type": "space", "unit": "nanometer"},
                    {"name": "x", "type": "space", "unit": "nanometer"},
                ],
                "coordinateTransformations": [
                    {"scale": [1.0, 1.0, 1.0, 1.0, 1.0], "type": "scale"},
                    {"translation": [0.0, 0.0, 0.0, 0.0, 0.0], "type": "translation"},
                ],
                "datasets": [
                    {
                        "coordinateTransformations": [
                            {"scale": [1.0, 1.0, 1.0, 0.2, 0.2], "type": "scale"},
                            {"translation": [0.0, 0.0, 0.0, 0.0, 0.0], "type": "translation"},
                        ],
                        "path": "exported_data/s0",
                    }
                ],
                "name": "exported_data",
                "version": "0.4",
            }
        ]
        expected_meta_s1 = [
            {
                "axes": [
                    {"name": "t", "type": "time"},
                    {"name": "c", "type": "channel"},
                    {"name": "z", "type": "space"},
                    {"name": "y", "type": "space", "unit": "nanometer"},
                    {"name": "x", "type": "space", "unit": "nanometer"},
                ],
                "coordinateTransformations": [
                    {"scale": [1.0, 1.0, 1.0, 1.0, 1.0], "type": "scale"},
                    {"translation": [0.0, 0.0, 0.0, 0.0, 0.0], "type": "translation"},
                ],
                "datasets": [
                    {
                        "coordinateTransformations": [
                            {"scale": [1.0, 1.0, 1.0, 1.4, 1.4], "type": "scale"},
                            {"translation": [0.0, 0.0, 0.0, 7.62, 8.49], "type": "translation"},
                        ],
                        "path": "exported_data/s1",
                    }
                ],
                "name": "exported_data",
                "version": "0.4",
            }
        ]

        path_in = self._tmpdir + "/input.zarr"
        file = z5py.ZarrFile(path_in, "w")
        data = numpy.random.random((89, 99)).astype(numpy.float32)
        downscale = data[::7, ::7]
        file.create_dataset("s0", data=data)
        file.create_dataset("s1", data=downscale)
        file.attrs["multiscales"] = input_meta

        graph = Graph()
        # Raw scale first
        opRead = OpInputDataReader(graph=graph)
        opExport = OpExportSlot(graph=graph)
        try:
            opRead.FilePath.setValue(path_in + "/s0")

            export_path = self._tmpdir + "/test_export1.zarr"
            opExport.Input.connect(opRead.Output)
            opExport.OutputFormat.setValue("single-scale OME-Zarr")
            opExport.OutputFilenameFormat.setValue(export_path)
            opExport.run_export()

            assert os.path.exists(export_path)
            written_file = z5py.ZarrFile(export_path, "r")
            assert written_file.attrs["multiscales"] == expected_meta_s0
        finally:
            opExport.cleanUp()
            opRead.cleanUp()

        # Same thing for the second scale
        # Have to make new ops because they aren't "recyclable" after a cleanUp
        opRead = OpInputDataReader(graph=graph)
        opExport = OpExportSlot(graph=graph)
        try:
            opRead.FilePath.setValue(path_in + "/s1")

            export_path = self._tmpdir + "/test_export2.zarr"
            opExport.Input.connect(opRead.Output)
            opExport.OutputFormat.setValue("single-scale OME-Zarr")
            opExport.OutputFilenameFormat.setValue(export_path)
            opExport.run_export()

            assert os.path.exists(export_path)
            written_file = z5py.ZarrFile(export_path, "r")
            assert written_file.attrs["multiscales"] == expected_meta_s1
        finally:
            opExport.cleanUp()
            opRead.cleanUp()

        # Another time, but give path as URI to go through OMEZarrMultiscaleReader
        # opRead then needs a parent to avoid the multiscale reader going into single-scale mode
        noop = Operator(graph=graph)
        opRead = OpInputDataReader(parent=noop)
        opExport = OpExportSlot(parent=noop)
        try:
            opRead.FilePath.setValue(Path(path_in).as_uri())
            opRead.ActiveScale.setValue("s1")

            export_path = self._tmpdir + "/test_export3.zarr"
            opExport.Input.connect(opRead.Output)
            opExport.OutputFormat.setValue("single-scale OME-Zarr")
            opExport.OutputFilenameFormat.setValue(export_path)
            opExport.run_export()

            assert os.path.exists(export_path)
            written_file = z5py.ZarrFile(export_path, "r")
            assert written_file.attrs["multiscales"] == expected_meta_s1
        finally:
            opExport.cleanUp()
            opRead.cleanUp()
            noop.cleanUp()

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
