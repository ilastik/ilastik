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
from lazyflow.operators.ioOperators import OpInputDataReader
from lazyflow.operator import Operator
import json
import os
import numpy
import vigra
import lazyflow.graph
import tempfile
import shutil
import h5py
import pytest
import zarr

from collections import OrderedDict
from typing import Tuple
from PIL import Image

from lazyflow.utility.io_util.OMEZarrStore import (
    OME_ZARR_V_0_4_KWARGS,
    OMEZarrMultiscaleMeta,
    InvalidTransformationError,
    NotAnOMEZarrMultiscale,
)
from lazyflow.utility.io_util.multiscaleStore import Multiscales


class TestOpInputDataReader(object):
    def setup_method(self, method):
        self.graph = lazyflow.graph.Graph()
        tmpDir = tempfile.mkdtemp()
        self.testNpyDataFileName = tmpDir + "/test.npy"
        self.testNpzDataFileName = tmpDir + "/test.npz"
        self.testImageFileName = tmpDir + "/test.png"
        self.testmultiImageFileName = tmpDir + "/test-{index:02d}.png"
        self.testH5FileName = tmpDir + "/test.h5"
        self.testmultiH5FileName = tmpDir + "/test-{index:02d}.h5"
        self.testmultiTiffFileName = tmpDir + "/test-{index:02d}.tiff"
        self.tmpDir = tmpDir

    def teardown_method(self, method):
        # Clean up: Delete the test data files.
        shutil.rmtree(self.tmpDir)

    def test_npy(self):
        # Create Numpy test data
        a = numpy.zeros((10, 11))
        for x in range(0, 10):
            for y in range(0, 11):
                a[x, y] = x + y
        numpy.save(self.testNpyDataFileName, a)

        # Now read back our test data using an OpInputDataReader operator
        npyReader = OpInputDataReader(graph=self.graph)
        try:
            npyReader.FilePath.setValue(self.testNpyDataFileName)
            cwd = os.path.split(__file__)[0]
            npyReader.WorkingDirectory.setValue(cwd)

            # Read the entire NPY file and verify the contents
            npyData = npyReader.Output[:].wait()
            assert npyData.shape == (10, 11)
            for x in range(0, 10):
                for y in range(0, 11):
                    assert npyData[x, y] == x + y
        finally:
            npyReader.cleanUp()

    def test_npz(self):
        # Create two Numpy test arrays
        a = numpy.zeros((10, 11))
        for x in range(0, 10):
            for y in range(0, 11):
                a[x, y] = x + y

        b = numpy.arange((3 * 9)).reshape((3, 9))
        numpy.savez(self.testNpzDataFileName, a=a, b=b)

        # Now read back our test data using an OpInputDataReader operator
        npyReader = OpInputDataReader(graph=self.graph)

        try:
            for internalPath, referenceArray in zip(["a", "b"], [a, b]):
                npyReader.FilePath.setValue("{}/{}".format(self.testNpzDataFileName, internalPath))
                cwd = os.path.split(__file__)[0]
                npyReader.WorkingDirectory.setValue(cwd)

                npzData = npyReader.Output[:].wait()
                assert npzData.shape == referenceArray.shape
                numpy.testing.assert_array_equal(npzData, referenceArray)
        finally:
            npyReader.cleanUp()

    def test_png(self):
        # Create PNG test data
        a = numpy.zeros((100, 200))
        for x in range(a.shape[0]):
            for y in range(a.shape[1]):
                a[x, y] = (x + y) % 256
        vigra.impex.writeImage(a, self.testImageFileName)

        # Read the entire PNG file and verify the contents
        pngReader = OpInputDataReader(graph=self.graph)
        pngReader.FilePath.setValue(self.testImageFileName)
        cwd = os.path.split(__file__)[0]
        pngReader.WorkingDirectory.setValue(cwd)
        pngData = pngReader.Output[:].wait()
        for x in range(pngData.shape[0]):
            for y in range(pngData.shape[1]):
                assert pngData[x, y, 0] == (x + y) % 256

    @pytest.mark.parametrize("sequence_axis", ["t", "z", "c"])
    def test_multi_png(self, sequence_axis):

        # Create PNG test data
        data = numpy.random.randint(0, 255, size=(5, 100, 200)).astype(numpy.uint8)
        for idx, dat in enumerate(data):
            vigra.impex.writeImage(dat.T, self.testmultiImageFileName.format(index=idx))

        # Read the entire PNG file and verify the contents
        pngReader = OpInputDataReader(graph=self.graph)
        pngReader.SequenceAxis.setValue(sequence_axis)
        globString = self.testmultiImageFileName.replace("02d}", "s}").format(index="*")
        pngReader.FilePath.setValue(globString)
        cwd = os.path.split(__file__)[0]
        pngReader.WorkingDirectory.setValue(cwd)
        pngData = pngReader.Output[:].wait().squeeze()
        if sequence_axis == "c":
            data = data.T

        assert pngData.shape == data.shape, f"{pngData.shape}, {data.shape}"
        numpy.testing.assert_array_equal(pngData, data)

    def test_h5(self):
        # Create HDF5 test data
        with h5py.File(self.testH5FileName, "w") as f:
            f.create_group("volume")
            shape = (1, 2, 3, 4, 5)
            f["volume"].create_dataset(
                "data", data=numpy.indices(shape).sum(0).astype(numpy.float32), chunks=True, compression="gzip"
            )

        # Read the entire HDF5 file and verify the contents
        h5Reader = OpInputDataReader(graph=self.graph)
        try:
            h5Reader.FilePath.setValue(self.testH5FileName + "/volume/data")  # Append internal path
            cwd = os.path.split(__file__)[0]
            h5Reader.WorkingDirectory.setValue(cwd)

            # Grab a section of the h5 data
            h5Data = h5Reader.Output[0, 0, :, :, :].wait()
            assert h5Data.shape == (1, 1, 3, 4, 5)
            # (Just check part of the data)
            for k in range(0, shape[2]):
                for l in range(0, shape[3]):
                    for m in range(0, shape[4]):
                        assert h5Data[0, 0, k, l, m] == k + l + m

        finally:
            # Call cleanUp() to close the file that this operator opened
            h5Reader.cleanUp()
            assert not h5Reader._file  # Whitebox assertion...

    @pytest.mark.parametrize("sequence_axis", ["t", "z", "c"])
    def test_h5_stack_single_file(self, sequence_axis):
        """Test stack/sequence reading in hdf5-files for given 'sequence_axis'"""
        shape = (4, 8, 16, 32, 3)  # assuming axis guess order is 'tzyxc'
        data = numpy.random.randint(0, 255, size=shape).astype(numpy.uint8)
        with h5py.File(self.testH5FileName, "w") as f:
            data_group = f.create_group("volumes")
            for index, t_slice in enumerate(data):
                data_group.create_dataset("timepoint-{index:02d}".format(index=index), data=t_slice)

        if sequence_axis == "z":
            data = numpy.concatenate(data, axis=0)
        elif sequence_axis == "c":
            data = numpy.concatenate(data, axis=-1)

        h5SequenceReader = OpInputDataReader(graph=self.graph)
        h5SequenceReader.SequenceAxis.setValue(sequence_axis)
        filenamePlusGlob = "{}/volumes/timepoint-*".format(self.testH5FileName)
        try:
            h5SequenceReader.FilePath.setValue(filenamePlusGlob)

            h5data = h5SequenceReader.Output[:].wait()
            assert h5data.shape == data.shape, f"{h5data.shape}, {data.shape}"
            numpy.testing.assert_array_equal(h5data, data)
        finally:
            # Call cleanUp() to close the file that this operator opened
            h5SequenceReader.cleanUp()

    @pytest.mark.parametrize("sequence_axis", ["t", "z", "c"])
    def test_h5_stack_multi_file(self, sequence_axis):
        """Test stack/sequence reading in hdf5-files"""
        shape = (4, 8, 16, 32, 3)
        data = numpy.random.randint(0, 255, size=shape).astype(numpy.uint8)
        for index, t_slice in enumerate(data):
            fname = self.testmultiH5FileName.format(index=index)
            with h5py.File(fname, "w") as f:
                data_group = f.create_group("volume")
                data_group.create_dataset("data", data=t_slice)

        if sequence_axis == "z":
            data = numpy.concatenate(data, axis=0)
        elif sequence_axis == "c":
            data = numpy.concatenate(data, axis=-1)

        h5SequenceReader = OpInputDataReader(graph=self.graph)
        h5SequenceReader.SequenceAxis.setValue(sequence_axis)
        globString = self.testmultiH5FileName.replace("02d}", "s}").format(index="*")
        filenamePlusGlob = "{}/volume/data".format(globString)
        try:
            h5SequenceReader.FilePath.setValue(filenamePlusGlob)
            h5data = h5SequenceReader.Output[:].wait()
            assert h5data.shape == data.shape
            numpy.testing.assert_array_equal(h5data, data)
        finally:
            # Call cleanUp() to close the file that this operator opened
            h5SequenceReader.cleanUp()

    @pytest.mark.parametrize("sequence_axis", ["t", "z", "c"])
    def test_tiff_stack_multi_file(self, sequence_axis):
        """Test stack/sequence reading in hdf5-files"""
        shape = (4, 8, 16, 3)
        data = numpy.random.randint(0, 255, size=shape).astype(numpy.uint8)
        for idx, data_slice in enumerate(data):
            im = Image.fromarray(data_slice, mode="RGB")
            im.save(self.testmultiTiffFileName.format(index=idx))

        if sequence_axis == "c":
            data = numpy.concatenate(data, axis=-1)

        reader = OpInputDataReader(graph=self.graph)
        reader.SequenceAxis.setValue(sequence_axis)
        globString = self.testmultiTiffFileName.replace("02d}", "s}").format(index="*")
        try:
            reader.FilePath.setValue(globString)
            tiffdata = reader.Output[:].wait()

            assert tiffdata.shape == data.shape, f"{tiffdata.shape}, {data.shape}"
            numpy.testing.assert_array_equal(tiffdata, data)
        finally:
            # Call cleanUp() to close the file that this operator opened
            reader.cleanUp()

    def test_npy_with_roi(self):
        a = numpy.indices((100, 100, 200)).astype(numpy.uint8).sum(0)
        assert a.shape == (100, 100, 200)
        numpy.save(self.testNpyDataFileName, a)
        opReader = OpInputDataReader(graph=lazyflow.graph.Graph())
        try:
            opReader.FilePath.setValue(self.testNpyDataFileName)
            opReader.SubVolumeRoi.setValue(((10, 20, 30), (50, 70, 90)))

            all_data = opReader.Output[:].wait()
            assert all_data.shape == (40, 50, 60)
            assert (all_data == a[10:50, 20:70, 30:90]).all()
        finally:
            opReader.cleanUp()


class TestOpInputDataReaderWithOMEZarr:
    """
    Extends end-to-end test in test_HeadlessPixelClassificationWorkflow
    with additional test cases:
    - OME-Zarr store with
        - multiple multiscales entries (though no such stores exist or are expected)
        - scales of one multiscale distributed across several zgroups
            (a typical output of ngff_zarr in its current version)
    - Dataset location given as path vs. as URI
    - Scale selection via /direct/path/to.zarr/scale (headless, API, batch)
    - Scale selection via ActiveScale inputslot (GUI, currently only works with URI not path)
    """

    PathTuple = Tuple[str, str, str]  # container root, raw scale, downscale

    @pytest.fixture(
        ids=[
            "typical",
            "with_dataset_name",
            "ngff_zarr_layout",
            "typical_labels",
            "labels_with_dataset_name",
            "labels_inverted_layout",
            "typical_well_fov",
        ],
        params=[
            ("some.zarr", "s0", "s1"),
            ("some.zarr", "correct/s0", "correct/s1"),
            ("some.zarr", "s0/correct", "s1/correct"),
            ("some.zarr/labels/nuclei", "s0", "s1"),  # labels (./labels/name/scales)
            ("some.zarr/labels/nuclei", "correct/s0", "correct/s1"),
            ("some.zarr/labels/nuclei", "s0/correct", "s1/correct"),
            ("some.zarr/A/1/0", "s0", "s1"),  # well (./row/column/field-of-view/scales)
        ],
    )
    def ome_zarr_store_on_disc(
        self, tmp_path, request, monkeypatch
    ) -> Tuple[PathTuple, Multiscales, OMEZarrMultiscaleMeta]:
        """Sets up a zarr store of a random image at raw scale and a downscale.
        Returns path to the store, and the metadata expected on the
        reader's output slot."""
        subdir, path0, path1 = request.param
        zarr_dir = tmp_path / subdir
        zarr_dir.mkdir(parents=True, exist_ok=True)

        dataset_shape = [3, 100, 100]  # cyx - to match the 2d3c project
        scaled_shape = [3, 50, 50]
        chunk_size = [3, 64, 64]
        correct_multiscale_zattrs = {
            "name": "some.zarr",
            "type": "Sample",
            "version": "0.4",
            "axes": [
                {"type": "space", "name": "c"},
                {"type": "space", "name": "y", "unit": "pixel"},
                {"type": "space", "name": "x", "unit": "pixel"},
            ],
            "datasets": [
                {
                    "path": path0,
                    "coordinateTransformations": [
                        {"scale": [1.0 for _ in dataset_shape], "type": "scale"},
                        {"translation": [0.0 for _ in dataset_shape], "type": "translation"},
                    ],
                },
                {
                    "path": path1,
                    "coordinateTransformations": [
                        {"scale": [2.0 for _ in scaled_shape], "type": "scale"},
                        {"translation": [0.0 for _ in scaled_shape], "type": "translation"},
                    ],
                },
            ],
            "coordinateTransformations": [],
        }
        full_zattrs = {
            "multiscales": [
                {  # Additional multiscales entry to test that the correct one (the other one) is used
                    "version": "0.4",
                    "axes": [
                        {"type": "space", "name": "y"},
                        {"type": "space", "name": "x"},
                    ],
                    "datasets": [{"path": "wrong/s0"}],
                },
                correct_multiscale_zattrs,
            ]
        }
        (zarr_dir / ".zattrs").write_text(json.dumps(full_zattrs))

        image_original = numpy.random.randint(0, 256, dataset_shape, dtype=numpy.uint16)
        image_scaled = image_original[:, ::2, ::2]
        chunks = tuple(chunk_size)

        zarr.array(
            image_original,
            chunks=chunks,
            store=zarr.DirectoryStore(str(zarr_dir / path0)),
            **OME_ZARR_V_0_4_KWARGS,
        )
        zarr.array(
            image_scaled,
            chunks=chunks,
            store=zarr.DirectoryStore(str(zarr_dir / path1)),
            **OME_ZARR_V_0_4_KWARGS,
        )

        # Scales metadata for GUI
        expected_multiscales = OrderedDict(
            [
                (path0, OrderedDict(zip("cyx", dataset_shape))),
                (path1, OrderedDict(zip("cyx", scaled_shape))),
            ]
        )
        # Singleton the error so that OMEZarrMultiscaleMeta objects can be eq compared
        err_placeholder = InvalidTransformationError()
        monkeypatch.setattr(InvalidTransformationError, "__new__", lambda _: err_placeholder)
        # OME-Zarr metadata for export
        expected_additional_meta = OMEZarrMultiscaleMeta.from_multiscale_spec(correct_multiscale_zattrs)

        return request.param, expected_multiscales, expected_additional_meta

    @pytest.fixture
    def parent(self, graph):
        # provide a noop parent so that OpInputDataReader doesn't drop into single-scale mode
        return Operator(graph=graph)

    def test_load_from_file_path(self, tmp_path, parent, ome_zarr_store_on_disc):
        paths, expected_multiscales, expected_additional_meta = ome_zarr_store_on_disc
        zarr_dir, path0, _ = paths
        # Request raw scale to test that the full path is used.
        # The loader implementation defaults to loading the lowest resolution (last scale).
        raw_data_path = tmp_path / zarr_dir / path0
        reader = OpInputDataReader(parent=parent)
        reader.FilePath.setValue(str(raw_data_path))
        reader.WorkingDirectory.setValue(str(zarr_dir))

        assert reader.Output.meta.scales == expected_multiscales
        assert reader.Output.meta.ome_zarr_meta == expected_additional_meta

        loaded_data = reader.Output[:].wait()

        assert loaded_data.shape == (3, 100, 100)
        assert numpy.count_nonzero(loaded_data) > 10000

    def test_load_from_file_uri(self, tmp_path, parent, ome_zarr_store_on_disc):
        paths, expected_multiscales, expected_additional_meta = ome_zarr_store_on_disc
        zarr_dir, path0, _ = paths
        # Request raw scale to test that the full path is used.
        # The loader implementation defaults to loading the lowest resolution (last scale).
        raw_data_path = tmp_path / zarr_dir / path0
        reader = OpInputDataReader(parent=parent)
        reader.FilePath.setValue(raw_data_path.as_uri())
        reader.WorkingDirectory.setValue(str(zarr_dir))

        assert reader.Output.meta.scales == expected_multiscales
        assert reader.Output.meta.ome_zarr_meta == expected_additional_meta

        loaded_data = reader.Output[:].wait()

        assert loaded_data.shape == (3, 100, 100)
        assert numpy.count_nonzero(loaded_data) > 10000

    def test_load_from_file_uri_without_parent(self, tmp_path, graph, ome_zarr_store_on_disc):
        paths, expected_multiscales, expected_additional_meta = ome_zarr_store_on_disc
        zarr_dir, path0, path1 = paths
        # Request downscale because with no parent, the reader defaults to loading only the first scale
        raw_data_path = tmp_path / zarr_dir / path1
        reader = OpInputDataReader(graph=graph)
        reader.FilePath.setValue(raw_data_path.as_uri())

        assert path1 in reader.Output.meta.scales
        assert path0 not in reader.Output.meta.scales
        assert reader.Output.meta.scales[path1] == expected_multiscales[path1]
        assert reader.Output.meta.ome_zarr_meta == expected_additional_meta

        loaded_data = reader.Output[:].wait()

        assert loaded_data.shape == (3, 50, 50)
        assert numpy.count_nonzero(loaded_data) > 5000

    def test_load_from_file_uri_via_slot(self, tmp_path, parent, ome_zarr_store_on_disc):
        paths, expected_multiscales, expected_additional_meta = ome_zarr_store_on_disc
        zarr_subdir, path0, _ = paths
        zarr_dir = tmp_path / zarr_subdir
        reader = OpInputDataReader(parent=parent, ActiveScale=path0)
        reader.FilePath.setValue(zarr_dir.as_uri())
        reader.WorkingDirectory.setValue(zarr_dir)

        assert reader.Output.meta.scales == expected_multiscales
        assert reader.Output.meta.ome_zarr_meta == expected_additional_meta

        loaded_data = reader.Output[:].wait()

        assert loaded_data.shape == (3, 100, 100)
        assert numpy.count_nonzero(loaded_data) > 10000

    def test_load_labels_options(self, tmp_path, parent):
        labels_zattrs = {"labels": ["nuclei", "Cells"]}  # case-sensitive
        labels_dir = tmp_path / "some.zarr/labels"
        labels_dir.mkdir(parents=True, exist_ok=True)
        (labels_dir / ".zattrs").write_text(json.dumps(labels_zattrs))

        reader = OpInputDataReader(parent=parent)
        expected_uris = [(labels_dir / "nuclei").as_uri(), (labels_dir / "Cells").as_uri()]
        with pytest.raises(NotAnOMEZarrMultiscale) as e:
            reader.FilePath.setValue(str(labels_dir))
        assert "labels directory" in str(e.value), str(e.value)
        assert all(expected in str(e.value) for expected in expected_uris), str(e.value)

    def test_load_well_options(self, tmp_path, parent):
        # sub-path within well not expected in real data, but should be able to handle it
        well_zattrs = {"well": {"images": [{"path": "suB/0"}, {"path": "suB/1"}]}}
        well_dir = tmp_path / "some.zarr/A/1"
        well_dir.mkdir(parents=True, exist_ok=True)
        (well_dir / ".zattrs").write_text(json.dumps(well_zattrs))

        reader = OpInputDataReader(parent=parent)
        expected_uris = [(well_dir / "suB/0").as_uri(), (well_dir / "suB/1").as_uri()]
        requested_uri = (well_dir / "suB").as_uri()
        with pytest.raises(NotAnOMEZarrMultiscale) as e:
            reader.FilePath.setValue(str(requested_uri))
        assert "well directory" in str(e.value), str(e.value)
        assert all(expected in str(e.value) for expected in expected_uris), str(e.value)

    def test_load_plate_options(self, tmp_path, parent):
        plate_zattrs = {"plate": {"wells": [{"path": "A/1"}, {"path": "B/2"}]}}
        plate_dir = tmp_path / "some.zarr"
        plate_dir.mkdir(parents=True, exist_ok=True)
        (plate_dir / ".zattrs").write_text(json.dumps(plate_zattrs))

        reader = OpInputDataReader(parent=parent)
        expected_uris = [(plate_dir / "A/1").as_uri(), (plate_dir / "B/2").as_uri()]
        requested_uri = (plate_dir / "A").as_uri()
        with pytest.raises(NotAnOMEZarrMultiscale) as e:
            reader.FilePath.setValue(str(requested_uri))
        assert "plate directory" in str(e.value), str(e.value)
        assert all(expected in str(e.value) for expected in expected_uris), str(e.value)
