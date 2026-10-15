###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
# 		   http://ilastik.org/license.html
###############################################################################
import os
import tempfile
import shutil
from pathlib import Path

import h5py
import numpy
import pytest
import vigra

from lazyflow.graph import Graph
from lazyflow.roi import roiToSlice
from lazyflow.operators.ioOperators import OpInputDataReader
from ilastik.applets.dataSelection.opDataSelection import FilesystemDatasetInfo

from ilastik.applets.dataExport.opDataExport import OpDataExport, DataExportPathFormatter


class TestOpDataExport(object):
    @classmethod
    def setup_class(cls):
        cls._tmpdir = tempfile.mkdtemp()

    @classmethod
    def teardown_class(cls):
        shutil.rmtree(cls._tmpdir)

    @pytest.mark.parametrize("nickname", ["test_nickname", "sample.1", "sample.h5"])
    @pytest.mark.parametrize("suffix", ["", ".h5", ".tiff"])
    def testBasic(self, tmp_h5_single_dataset: Path, nickname, suffix):
        graph = Graph()
        opExport = OpDataExport(graph=graph)
        try:
            opExport.TransactionSlot.setValue(True)
            opExport.WorkingDirectory.setValue(self._tmpdir)

            rawInfo = FilesystemDatasetInfo(
                filePath=str(tmp_h5_single_dataset / "test_group/test_data"), nickname=nickname
            )

            opExport.RawDatasetInfo.setValue(rawInfo)

            opExport.SelectionNames.setValue(["Mock Export Data"])

            data = numpy.random.random((100, 100)).astype(numpy.float32) * 100
            data = vigra.taggedView(data, vigra.defaultAxistags("xy"))

            opExport.Inputs.resize(1)
            opExport.Inputs[0].setValue(data)

            sub_roi = [(10, 20), (90, 80)]
            opExport.RegionStart.setValue(sub_roi[0])
            opExport.RegionStop.setValue(sub_roi[1])

            opExport.ExportDtype.setValue(numpy.uint8)

            opExport.OutputFormat.setValue("hdf5")
            opExport.OutputFilenameFormat.setValue(
                "{dataset_dir}/{nickname}_export_x{x_start}-{x_stop}_y{y_start}-{y_stop}" + suffix
            )
            opExport.OutputInternalPath.setValue("volume/data")

            assert opExport.ImageToExport.ready()
            assert opExport.ExportPath.ready()

            expected_path = tmp_h5_single_dataset.parent.joinpath(
                rawInfo.nickname + "_export_x10-90_y20-80.h5/volume/data"
            ).as_posix()
            computed_path = opExport.ExportPath.value
            assert os.path.normpath(computed_path) == os.path.normpath(expected_path)
            opExport.run_export()
        finally:
            opExport.cleanUp()

        opRead = OpInputDataReader(graph=graph)
        try:
            opRead.FilePath.setValue(computed_path)

            # Compare with the correct subregion and convert dtype.
            expected_data = data.view(numpy.ndarray)[roiToSlice(*sub_roi)]
            expected_data = expected_data.astype(numpy.uint8)
            read_data = opRead.Output[:].wait()
            assert (read_data == expected_data).all(), "Read data didn't match exported data!"
        finally:
            opRead.cleanUp()

    @pytest.mark.parametrize(
        "template,basename",
        [
            ("{nickname:.10s}", "sample.123"),
            ("{nickname}.{result_type}", "sample.1234567.Probabilities"),
        ],
    )
    def test_filename_templates_after_format_change(self, tmp_h5_single_dataset, tmp_path, template, basename):
        opExport = OpDataExport(graph=Graph())
        try:
            opExport.TransactionSlot.setValue(True)
            opExport.WorkingDirectory.setValue(str(tmp_path))
            opExport.RawDatasetInfo.setValue(
                FilesystemDatasetInfo(
                    filePath=str(tmp_h5_single_dataset / "test_group/test_data"), nickname="sample.1234567"
                )
            )
            opExport.SelectionNames.setValue(["Probabilities"])
            opExport.Inputs.resize(1)
            opExport.Inputs[0].setValue(vigra.taggedView(numpy.zeros((2, 3), dtype=numpy.uint8), "xy"))
            opExport.OutputFilenameFormat.setValue(template)

            for output_format, ending in [
                ("hdf5", ".h5/exported_data"),
                ("numpy", ".npy"),
                ("hdf5", ".h5/exported_data"),
            ]:
                opExport.OutputFormat.setValue(output_format)
                assert Path(opExport.ExportPath.value) == tmp_path / (basename + ending)
        finally:
            opExport.cleanUp()

    @pytest.mark.parametrize("nicknames", [("sample.1", "sample.2"), ("sample.1.h5", "sample.2.h5")])
    def test_distinct_dotted_nicknames(self, tmp_h5_single_dataset, tmp_path, nicknames):
        output_dir = tmp_path / "export.results"
        output_dir.mkdir()
        expected = {}
        opExport = OpDataExport(graph=Graph())
        try:
            opExport.TransactionSlot.setValue(True)
            opExport.WorkingDirectory.setValue(str(output_dir))
            opExport.SelectionNames.setValue(["Probabilities"])
            opExport.OutputFormat.setValue("hdf5")
            opExport.OutputFilenameFormat.setValue("{nickname}")
            opExport.Inputs.resize(1)

            for value, nickname in enumerate(nicknames):
                data = numpy.full((2, 3), value, dtype=numpy.uint8)
                opExport.Inputs[0].setValue(vigra.taggedView(data, "xy"))
                opExport.RawDatasetInfo.setValue(
                    FilesystemDatasetInfo(
                        filePath=str(tmp_h5_single_dataset / "test_group/test_data"), nickname=nickname
                    )
                )
                opExport.run_export()
                expected[output_dir / (nickname + ".h5")] = data
        finally:
            opExport.cleanUp()

        assert sorted(output_dir.iterdir()) == sorted(expected)
        for path, data in expected.items():
            with h5py.File(path, "r") as exported:
                numpy.testing.assert_array_equal(exported["exported_data"][:], data)


class TestDataExportPathFormatter:
    class DummyDSInfo:
        def __init__(self, filePath, nickname, default_output_dir):
            self.filePath = filePath
            self.nickname = nickname
            self.default_output_dir = default_output_dir

    @pytest.fixture
    def path_formatter(self):
        ds_info = self.DummyDSInfo(
            filePath="/tmp/a/b/test_ds.h5", nickname="test_nickname", default_output_dir="/tmp/a"
        )
        return DataExportPathFormatter(dataset_info=ds_info, working_dir="/tmp/a", result_type="mytype")

    @pytest.mark.parametrize(
        "template_str,expected_path",
        [
            ("{nickname}", "test_nickname"),
            ("{dataset_dir}/{nickname}", "/tmp/a/test_nickname"),
            ("{dataset_dir}/{nickname}+{result_type}", "/tmp/a/test_nickname+mytype"),
            ("{var}", "{var}"),
            ("", ""),
            ("mypath", "mypath"),
        ],
    )
    def test_format_path(self, path_formatter, template_str, expected_path):
        formatted_path = path_formatter.format_path(template_str)
        assert expected_path == formatted_path

    @pytest.mark.parametrize(
        "template_str",
        [
            "{nickname",
            "nickname}",
        ],
    )
    def test_invalid_format_path(self, path_formatter, template_str):
        with pytest.raises(ValueError):
            path_formatter.format_path(template_str)
