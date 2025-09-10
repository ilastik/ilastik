###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2024, the ilastik developers
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
#          http://ilastik.org/license.html
###############################################################################
import json
import os
import shutil
from collections import defaultdict, OrderedDict
from typing import Tuple, Dict
from unittest import mock
from unittest.mock import Mock

import numpy
import requests
import vigra
import h5py
from pathlib import Path
import zarr
from PIL import Image

from lazyflow.utility.io_util.write_ome_zarr import OME_ZARR_V_0_4_KWARGS
from lazyflow.utility.io_util.OMEZarrStore import ScaleNotFoundError
from lazyflow.utility.io_util.multiscaleStore import DEFAULT_SCALE_KEY
from lazyflow.utility.pathHelpers import PathComponents
from lazyflow.graph import Operator, OperatorWrapper, InputSlot, OutputSlot
from lazyflow.operators.generic import OpMultiArrayMerger
from ilastik.applets.dataSelection.opDataSelection import (
    OpMultiLaneDataSelectionGroup,
    OpDataSelectionGroup,
    OpDataSelection,
    MultiscaleUrlDatasetInfo,
    RelativeFilesystemDatasetInfo,
    FilesystemDatasetInfo,
    ProjectInternalDatasetInfo,
    UrlDatasetInfo,
    eq_shapes,
    TransactionRequiredError,
)
from ilastik.applets.dataSelection.dataSelectionSerializer import DataSelectionSerializer
from ilastik.applets.base.applet import DatasetConstraintError

import tempfile
import pytest

TOP_GROUP_NAME = "some_group"


@pytest.fixture
def serializer(empty_project_file, graph):
    opDataSelectionGroup = OpMultiLaneDataSelectionGroup(graph=graph)
    opDataSelectionGroup.ProjectFile.setValue(empty_project_file)
    opDataSelectionGroup.WorkingDirectory.setValue(Path(empty_project_file.filename).parent)
    opDataSelectionGroup.DatasetRoles.setValue(["Raw Data"])
    opDataSelectionGroup.DatasetGroup.resize(1)

    serializer = DataSelectionSerializer(opDataSelectionGroup, TOP_GROUP_NAME)
    return serializer


def save_to_hdf5(dataset_name, data, filename):
    with h5py.File(filename, "a") as f:
        f.create_dataset(name=dataset_name, data=data)


class TestOpDataSelection_Basic2D(object):
    @classmethod
    def setup_class(cls):
        cls.tmpdir = tempfile.mkdtemp()
        cls.imgFileNames2D = []
        cls.imgFileNames2Dc = []
        cls.generatedImages2Dc = []
        # Comparison of compressed data not possible - those types will be
        # skipped in raw comparison:
        cls.compressedExtensions = [".jpg", ".jpeg"]
        cls.projectFileName = os.path.join(cls.tmpdir, "testProject.ilp")

        # Create a couple test images of different types
        # in order to simplify and unify testing among the different file types
        # the extra dimension is added, as vigra would add one anyway.
        cls.imgData2D = numpy.random.randint(0, 255, (10, 11, 1)).astype(numpy.uint8)
        # v- image data variables in order to reflect the correct axis-order
        # otherwise the axes get scrambled when writing/reloading
        vimgData2D = vigra.VigraArray(cls.imgData2D, axistags=vigra.defaultAxistags("yxc"), dtype=numpy.uint8)

        testNpyFileName = os.path.join(cls.tmpdir, "testimage2D.npy")
        numpy.save(testNpyFileName, cls.imgData2D)
        cls.imgFileNames2D.append(testNpyFileName)

        testNpzFileName = os.path.join(cls.tmpdir, "testimage2D.npz")
        numpy.savez(testNpzFileName, data=cls.imgData2D)
        testNpzFileName = "{}/data".format(testNpzFileName)
        cls.imgFileNames2D.append(testNpzFileName)

        testH5FileName = os.path.join(cls.tmpdir, "testimage2D.h5")

        save_to_hdf5(dataset_name="test/data", data=cls.imgData2D, filename=testH5FileName)
        testH5FileName = "{}/test/data".format(testH5FileName)
        cls.imgFileNames2D.append(testH5FileName)

        for extension in vigra.impex.listExtensions().split(" "):
            tmpFileName = os.path.join(cls.tmpdir, "testImage2D.{}".format(extension))
            # not all extensions support this kind of pixeltype
            try:
                vigra.impex.writeImage(vimgData2D, tmpFileName)
                cls.imgFileNames2D.append(tmpFileName)
            except RuntimeError as e:
                msg = str(e).replace("\n", "")
                print("Couldn't write temp 2D image file using vigra with `{}` extension : {}".format(extension, msg))

        cls.imgData2Dc = numpy.random.randint(0, 255, (100, 200, 3)).astype(numpy.uint8)
        vimgData2Dc = vigra.VigraArray(cls.imgData2Dc, axistags=vigra.defaultAxistags("yxc"), dtype=numpy.uint8)

        testNpyFileName = os.path.join(cls.tmpdir, "testimage2Dc.npy")
        numpy.save(testNpyFileName, cls.imgData2Dc)
        cls.imgFileNames2Dc.append(testNpyFileName)

        testNpzFileName = os.path.join(cls.tmpdir, "testimage2Dc.npz")
        numpy.savez(testNpzFileName, data=cls.imgData2Dc)
        testNpzFileName = "{}/data".format(testNpzFileName)
        cls.imgFileNames2Dc.append(testNpzFileName)

        testH5FileName = os.path.join(cls.tmpdir, "testimage2Dc.h5")
        save_to_hdf5(dataset_name="test/data", data=cls.imgData2Dc, filename=testH5FileName)
        testH5FileName = "{}/test/data".format(testH5FileName)
        cls.imgFileNames2Dc.append(testH5FileName)

        for extension in vigra.impex.listExtensions().split(" "):
            tmpFileName = os.path.join(cls.tmpdir, "testImage2Dc.{}".format(extension))
            # not all extensions support this kind of pixeltype
            try:
                vigra.impex.writeImage(vimgData2Dc, tmpFileName)
                cls.imgFileNames2Dc.append(tmpFileName)
                cls.generatedImages2Dc.append(tmpFileName)
            except RuntimeError as e:
                msg = str(e).replace("\n", "")
                print("Couldn't write temp 2D+c image file using vigra with `{}` extension : {}".format(extension, msg))

        # Create a 'project' file and give it some data
        cls.projectFile = h5py.File(cls.projectFileName, "w")
        cls.projectFile.create_group("DataSelection")
        cls.projectFile["DataSelection"].create_group("local_data")
        # Use the same data as the 2d+c data (above)
        cls.projectFile["DataSelection/local_data"].create_dataset("dataset1", data=cls.imgData2Dc)
        cls.projectFile.flush()

    @classmethod
    def teardown_class(cls):
        cls.projectFile.close()
        try:
            shutil.rmtree(cls.tmpdir)
        except OSError as e:
            print("Exception caught while deleting temporary files: {}".format(e))

    def create_nickname(self, fileName: str):
        comps = PathComponents(fileName)
        expected_nickname = Path(comps.externalPath).stem
        if comps.internalPath:
            expected_nickname += comps.internalPath.replace("/", "-")
        return expected_nickname

    def testBasic2D(self, graph):
        """Test if plane 2d files are loaded correctly"""
        for fileName in self.imgFileNames2D:
            reader = OperatorWrapper(OpDataSelection, graph=graph, operator_kwargs={"forceAxisOrder": False})
            reader.ProjectFile.setValue(self.projectFile)
            reader.WorkingDirectory.setValue(os.getcwd())

            info = FilesystemDatasetInfo(filePath=fileName)

            reader.Dataset.setValues([info])

            # Read the test files using the data selection operator and verify the contents
            imgData2D = reader.Image[0][...].wait()

            assert reader.ImageName[0].value == self.create_nickname(fileName)
            # Check raw images
            assert imgData2D.shape == self.imgData2D.shape
            # skip this if image was saved compressed:
            if any(x in fileName.lower() for x in self.compressedExtensions):
                print("Skipping raw comparison for compressed data: {}".format(fileName))
                continue
            numpy.testing.assert_array_equal(imgData2D, self.imgData2D)

    def testBasic2Dc(self, graph):
        """Test if 2d 3-channel files are loaded correctly"""
        # For some reason vigra saves 2D+c data compressed in gifs, so skip!
        self.compressedExtensions.append(".gif")
        for fileName in self.imgFileNames2Dc:
            reader = OperatorWrapper(OpDataSelection, graph=graph, operator_kwargs={"forceAxisOrder": False})
            reader.ProjectFile.setValue(self.projectFile)
            reader.WorkingDirectory.setValue(os.getcwd())

            info = FilesystemDatasetInfo(filePath=fileName)

            reader.Dataset.setValues([info])

            # Read the test files using the data selection operator and verify the contents
            imgData2Dc = reader.Image[0][...].wait()

            # Check the file name output
            assert reader.ImageName[0].value == self.create_nickname(fileName)
            # Check raw images
            assert imgData2Dc.shape == self.imgData2Dc.shape, (imgData2Dc.shape, self.imgData2Dc.shape)
            # skip this if image was saved compressed:
            if any(x in fileName.lower() for x in self.compressedExtensions):
                print("Skipping raw comparison for compressed data: {}".format(fileName))
                continue
            numpy.testing.assert_array_equal(imgData2Dc, self.imgData2Dc)

    def testProjectLocalData(self, serializer, empty_project_file, graph):
        for fileName in self.generatedImages2Dc:
            # For some reason vigra saves 2D+c data compressed in gifs, so skip!
            if Path(fileName).suffix in self.compressedExtensions + [".gif"]:
                continue
            filesystem_info = FilesystemDatasetInfo(filePath=fileName)

            # From project
            inner_path = filesystem_info.importAsLocalDataset(project_file=empty_project_file)
            info = ProjectInternalDatasetInfo(project_file=empty_project_file, inner_path=inner_path)

            projectInternalData = info.get_provider_slot(graph=graph)[...].wait()

            assert projectInternalData.shape == self.imgData2Dc.shape, (
                projectInternalData.shape,
                self.imgData2Dc.shape,
            )
            assert (projectInternalData == self.imgData2Dc).all()


class TestOpDataSelection_Basic_native_3D(object):
    """Test related to loading file types that support 3D"""

    @classmethod
    def setup_class(cls):
        cls.tmpdir = tempfile.mkdtemp()
        cls.imgFileNames3D = []
        cls.imgFileNames3DNicknames = []

        cls.imgFileNames3Dc = []
        cls.imgFileNames3DcNicknames = []

        cls.generatedImages3Dc = []
        # Comparison of compressed data not possible - those types will be
        # skipped in raw comparison:
        cls.projectFileName = os.path.join(cls.tmpdir, "testProject.ilp")

        # Create a couple test images of different types
        # in order to simplify and unify testing among the different file types
        # the extra dimension is added, as vigra would add one anyway.
        cls.imgData3D = numpy.random.randint(0, 255, (10, 11, 12, 1)).astype(numpy.uint8)
        # v- image data variables in order to reflect the correct axis-order
        # otherwise the axes get scrambled when writing/reloading
        vimgData3D = vigra.VigraArray(cls.imgData3D, axistags=vigra.defaultAxistags("zyxc"), dtype=numpy.uint8)

        testNpyFileName = os.path.join(cls.tmpdir, "testimage3D.npy")
        numpy.save(testNpyFileName, cls.imgData3D)
        cls.imgFileNames3D.append(testNpyFileName)
        cls.imgFileNames3DNicknames.append("testimage3D")

        testNpzFileName = os.path.join(cls.tmpdir, "testimage3D.npz")
        numpy.savez(testNpzFileName, data=cls.imgData3D)
        testNpzFileName = "{}/data".format(testNpzFileName)
        cls.imgFileNames3D.append(testNpzFileName)
        cls.imgFileNames3DNicknames.append("testimage3D-data")

        testH5FileName = os.path.join(cls.tmpdir, "testimage3D.h5")
        save_to_hdf5(dataset_name="test/data", data=cls.imgData3D, filename=testH5FileName)
        testH5FileName = "{}/test/data".format(testH5FileName)
        cls.imgFileNames3D.append(testH5FileName)
        cls.imgFileNames3DNicknames.append("testimage3D-test-data")

        cls.imgData3Dc = numpy.random.randint(0, 255, (10, 11, 12, 3)).astype(numpy.uint8)
        vimgData3Dc = vigra.VigraArray(cls.imgData3Dc, axistags=vigra.defaultAxistags("zyxc"), dtype=numpy.uint8)

        testNpyFileName = os.path.join(cls.tmpdir, "testimage3Dc.npy")
        numpy.save(testNpyFileName, cls.imgData3Dc)
        cls.imgFileNames3Dc.append(testNpyFileName)
        cls.imgFileNames3DcNicknames.append("testimage3Dc")
        cls.generatedImages3Dc.append(testNpyFileName)

        testNpzFileName = os.path.join(cls.tmpdir, "testimage3Dc.npz")
        numpy.savez(testNpzFileName, data=cls.imgData3Dc)
        testNpzFileName = "{}/data".format(testNpzFileName)
        cls.imgFileNames3Dc.append(testNpzFileName)
        cls.imgFileNames3DcNicknames.append("testimage3Dc-data")
        cls.generatedImages3Dc.append(testNpzFileName)

        testH5FileName = os.path.join(cls.tmpdir, "testimage3Dc.h5")
        save_to_hdf5(dataset_name="test/data", data=cls.imgData3Dc, filename=testH5FileName)
        testH5FileName = "{}/test/data".format(testH5FileName)
        cls.imgFileNames3Dc.append(testH5FileName)
        cls.imgFileNames3DcNicknames.append("testimage3Dc-test-data")
        cls.generatedImages3Dc.append(testH5FileName)

        # Create a 'project' file and give it some data
        cls.projectFile = h5py.File(cls.projectFileName, "w")
        cls.projectFile.create_group("DataSelection")
        cls.projectFile["DataSelection"].create_group("local_data")
        # Use the same data as the 3d+c data (above)
        cls.projectFile["DataSelection/local_data"].create_dataset("dataset1", data=cls.imgData3Dc)
        cls.projectFile.flush()

    @classmethod
    def teardown_class(cls):
        cls.projectFile.close()
        try:
            shutil.rmtree(cls.tmpdir)
        except OSError as e:
            print("Exception caught while deleting temporary files: {}".format(e))

    def testBasic3D(self, graph):
        """Test if plane 2d files are loaded correctly"""
        for fileName, nickname in zip(self.imgFileNames3D, self.imgFileNames3DNicknames):
            reader = OperatorWrapper(OpDataSelection, graph=graph, operator_kwargs={"forceAxisOrder": False})
            reader.ProjectFile.setValue(self.projectFile)
            reader.WorkingDirectory.setValue(os.getcwd())
            reader.Dataset.setValues([FilesystemDatasetInfo(filePath=fileName)])

            # Read the test files using the data selection operator and verify the contents
            imgData3D = reader.Image[0][...].wait()

            # Check the file name output
            assert reader.ImageName[0].value == nickname
            # Check raw images
            assert imgData3D.shape == self.imgData3D.shape, (imgData3D.shape, self.imgData3D.shape)
            # skip this if image was saved compressed:
            numpy.testing.assert_array_equal(imgData3D, self.imgData3D)

    def testBasic3DWrongAxes(self, graph):
        """Test if 3D file with intentionally wrong axes is rejected"""
        for fileName in self.imgFileNames3D:
            reader = OperatorWrapper(OpDataSelection, graph=graph, operator_kwargs={"forceAxisOrder": False})
            reader.ProjectFile.setValue(self.projectFile)
            reader.WorkingDirectory.setValue(os.getcwd())
            reader.ProjectDataGroup.setValue("DataSelection/local_data")

            info = FilesystemDatasetInfo(filePath=fileName, axistags=vigra.defaultAxistags("tzyc"))

            try:
                reader.Dataset.setValues([info])
                assert False, "Should have thrown an exception!"
            except DatasetConstraintError:
                pass
            except:
                assert False, "Should have thrown a DatasetConstraintError!"

    def testBasic3Dc(self, graph):
        """Test if 2d 3-channel files are loaded correctly"""
        # For some reason vigra saves 2D+c data compressed in gifs, so skip!
        for fileName, nickname in zip(self.imgFileNames3Dc, self.imgFileNames3DcNicknames):
            reader = OperatorWrapper(OpDataSelection, graph=graph, operator_kwargs={"forceAxisOrder": False})
            reader.ProjectFile.setValue(self.projectFile)
            reader.WorkingDirectory.setValue(os.getcwd())
            reader.ProjectDataGroup.setValue("DataSelection/local_data")

            reader.Dataset.setValues([FilesystemDatasetInfo(filePath=fileName)])

            # Read the test files using the data selection operator and verify the contents
            imgData3Dc = reader.Image[0][...].wait()

            # Check the file name output
            assert reader.ImageName[0].value == nickname
            # Check raw images
            assert imgData3Dc.shape == self.imgData3Dc.shape, (imgData3Dc.shape, self.imgData3Dc.shape)
            # skip this if image was saved compressed:
            numpy.testing.assert_array_equal(imgData3Dc, self.imgData3Dc)

    def test3DProjectLocalData(self, serializer, empty_project_file, graph):
        empty_project_file.create_group("DataSelection")
        empty_project_file["DataSelection"].create_group("local_data")
        empty_project_file["DataSelection/local_data"].create_dataset("dataset1", data=self.imgData3Dc)
        info = ProjectInternalDatasetInfo(
            inner_path="DataSelection/local_data/dataset1", project_file=empty_project_file
        )

        projectInternalData = info.get_provider_slot(graph=graph)[...].wait()
        assert projectInternalData.shape == self.imgData3Dc.shape, (projectInternalData.shape, self.imgData3Dc.shape)
        assert (projectInternalData == self.imgData3Dc).all()

        for fileName in self.generatedImages3Dc:
            filesystem_info = FilesystemDatasetInfo(filePath=fileName)
            inner_path = filesystem_info.importAsLocalDataset(project_file=empty_project_file)
            info = ProjectInternalDatasetInfo(project_file=empty_project_file, inner_path=inner_path)

            projectInternalData = info.get_provider_slot(graph=graph)[...].wait()

            assert projectInternalData.shape == self.imgData3Dc.shape, (
                projectInternalData.shape,
                self.imgData3Dc.shape,
            )
            assert (projectInternalData == self.imgData3Dc).all()


class TestOpDataSelection_3DStacks(object):
    @classmethod
    def setup_class(cls):
        cls.tmpdir = tempfile.mkdtemp()
        cls.imgFileNameGlobs2D = []
        cls.imgFileNameGlobs2DNicknames = []

        cls.imgFileNameGlobs2Dc = []
        cls.imgFileNameGlobs2DcNicknames = []

        cls.imgFileLists2D = defaultdict(list)

        cls.vigraExtensions = vigra.impex.listExtensions().split(" ")
        # Comparison of compressed data not possible - those types will be
        # skipped in raw comparison:
        cls.compressedExtensions = [".jpg", ".jpeg"]
        cls.projectFileName = os.path.join(cls.tmpdir, "testProject.ilp")

        # Create a couple test images of different types
        # in order to simplify and unify testing among the different file types
        # the extra dimension is added, as vigra would add one anyway.
        # 2D Stacks ##
        cls.imgData3D = numpy.random.randint(0, 255, (9, 10, 11, 1)).astype(numpy.uint8)
        # v- image data variables in order to reflect the correct axis-order
        # otherwise the axes get scrambled when writing/reloading
        cls.removedExtensions = []
        for slice_index, slice2D in enumerate(cls.imgData3D):
            vimgData2D = vigra.VigraArray(slice2D, axistags=vigra.defaultAxistags("yxc"), dtype=numpy.uint8)

            testNpyFileName = os.path.join(cls.tmpdir, "testimage2D_{:02d}.npy".format(slice_index))
            numpy.save(testNpyFileName, slice2D)

            testNpzFileName = os.path.join(cls.tmpdir, "testimage2D_{:02d}.npz".format(slice_index))
            numpy.savez(testNpzFileName, data=slice2D)
            testNpzFileName = "{}/data".format(testNpzFileName)

            testH5FileName = os.path.join(cls.tmpdir, "testimage2D_{:02d}.h5".format(slice_index))
            save_to_hdf5(dataset_name="test/data", data=slice2D, filename=testH5FileName)

            cls.imgFileLists2D["h5"].append("{}/test/data".format(testH5FileName))

            for extension in cls.vigraExtensions:
                if extension in cls.removedExtensions:
                    continue
                tmpFileName = os.path.join(cls.tmpdir, "testImage2D_{:02d}.{}".format(slice_index, extension))
                # not all extensions support this kind of pixeltype
                try:
                    vigra.impex.writeImage(vimgData2D, tmpFileName)
                    cls.imgFileLists2D[extension].append(tmpFileName)
                except RuntimeError as e:
                    cls.removedExtensions.append(extension)
                    msg = str(e).replace("\n", "")
                    print(
                        "Couldn't write temp 2D image file using vigra with `{}` "
                        "extension : {}".format(extension, msg)
                    )
        for extension in cls.removedExtensions:
            cls.vigraExtensions.pop(cls.vigraExtensions.index(extension))

        for extension in cls.vigraExtensions:
            cls.imgFileNameGlobs2D.append(os.path.join(cls.tmpdir, "testImage2D_*.{}".format(extension)))
            cls.imgFileNameGlobs2DNicknames.append("testImage2D_0")
        cls.imgFileNameGlobs2D.append(os.path.join(cls.tmpdir, "testimage2D_*.h5/test/data"))
        cls.imgFileNameGlobs2DNicknames.append("testimage2D_0-test-data")
        # uncomment once support is implemented
        # os.path.join(cls.tmpdir, "testimage2D_*.npz/data"),
        # os.path.join(cls.tmpdir, "testimage2D_*.npy"),

        # 2Dc Stacks ##
        cls.imgData3Dc = numpy.random.randint(0, 255, (9, 10, 11, 3)).astype(numpy.uint8)

        cls.removedExtensions = []
        for slice_index, slice2Dc in enumerate(cls.imgData3Dc):
            # v- image data variables in order to reflect the correct axis-order
            # otherwise the axes get scrambled when writing/reloading
            vimgData2Dc = vigra.VigraArray(slice2Dc, axistags=vigra.defaultAxistags("yxc"), dtype=numpy.uint8)

            testNpyFileName = os.path.join(cls.tmpdir, "testimage2Dc_{:02d}.npy".format(slice_index))
            numpy.save(testNpyFileName, slice2Dc)

            testNpzFileName = os.path.join(cls.tmpdir, "testimage2Dc_{:02d}.npz".format(slice_index))
            numpy.savez(testNpzFileName, data=slice2Dc)
            testNpzFileName = "{}/data".format(testNpzFileName)

            testH5FileName = os.path.join(cls.tmpdir, "testimage2Dc_{:02d}.h5".format(slice_index))
            save_to_hdf5(dataset_name="test/data", data=slice2Dc, filename=testH5FileName)

            for extension in cls.vigraExtensions:
                if extension in cls.removedExtensions:
                    continue
                tmpFileName = os.path.join(cls.tmpdir, "testImage2Dc_{:02d}.{}".format(slice_index, extension))
                # not all extensions support this kind of pixeltype
                try:
                    vigra.impex.writeImage(vimgData2Dc, tmpFileName)
                except RuntimeError as e:
                    cls.removedExtensions.append(extension)
                    msg = str(e).replace("\n", "")
                    print(
                        "Couldn't write temp 2D image file using vigra with `{}` "
                        "extension : {}".format(extension, msg)
                    )
        for extension in cls.removedExtensions:
            cls.vigraExtensions.pop(cls.vigraExtensions.index(extension))

        for extension in cls.vigraExtensions:
            cls.imgFileNameGlobs2Dc.append(os.path.join(cls.tmpdir, "testImage2Dc_*.{}".format(extension)))
            cls.imgFileNameGlobs2DcNicknames.append("testImage2Dc_0")

        cls.imgFileNameGlobs2Dc.append(os.path.join(cls.tmpdir, "testimage2Dc_*.h5/test/data"))
        cls.imgFileNameGlobs2DcNicknames.append("testimage2Dc_0-test-data")
        # uncomment once support is implemented
        # os.path.join(cls.tmpdir, "testimage2Dc_*.npz/data"),
        # os.path.join(cls.tmpdir, "testimage2Dc_*.npy"),

        # Create a 'project' file and give it some data
        cls.projectFile = h5py.File(cls.projectFileName, "w")
        cls.projectFile.create_group("DataSelection")
        cls.projectFile["DataSelection"].create_group("local_data")
        # Use the same data as the 3d+c data (above)
        cls.projectFile["DataSelection/local_data"].create_dataset("dataset1", data=cls.imgData3D)
        cls.projectFile.flush()

    @classmethod
    def teardown_class(cls):
        cls.projectFile.close()
        try:
            shutil.rmtree(cls.tmpdir)
        except OSError as e:
            print("Exception caught while deleting temporary files: {}".format(e))

    def testBasic3DstackFromGlobString(self, empty_project_file, graph):
        """Test if stacked 2d files are loaded correctly"""

        reader = OperatorWrapper(OpDataSelection, graph=graph, operator_kwargs={"forceAxisOrder": False})
        reader.WorkingDirectory.setValue(str(Path(empty_project_file.filename).parent))
        for fileName, nickname in zip(self.imgFileNameGlobs2D, self.imgFileNameGlobs2DNicknames):
            reader.Dataset.setValues([FilesystemDatasetInfo(filePath=fileName, sequence_axis="z")])

            # Read the test files using the data selection operator and verify the contents
            imgData3D = reader.Image[0][...].wait()

            # Check the file name output
            assert reader.ImageName[0].value == nickname
            # Check raw images
            assert imgData3D.shape == self.imgData3D.shape, (imgData3D.shape, self.imgData3D.shape)
            # skip this if image was saved compressed:
            if any(x in fileName.lower() for x in self.compressedExtensions):
                print("Skipping raw comparison for compressed data: {}".format(fileName))
                continue
            numpy.testing.assert_array_equal(imgData3D, self.imgData3D)

    def testBasic3DstacksFromFileList(self, empty_project_file, graph):
        for ext, fileNames in list(self.imgFileLists2D.items()):
            fileNameString = os.path.pathsep.join(fileNames)
            reader = OperatorWrapper(OpDataSelection, graph=graph, operator_kwargs={"forceAxisOrder": False})
            reader.WorkingDirectory.setValue(str(Path(empty_project_file.filename).parent))

            reader.Dataset.setValues([FilesystemDatasetInfo(filePath=fileNameString, sequence_axis="z")])

            # Read the test files using the data selection operator and verify the contents
            imgData3D = reader.Image[0][...].wait()

            # Check raw images
            assert imgData3D.shape == self.imgData3D.shape, (imgData3D.shape, self.imgData3D.shape)
            # skip this if image was saved compressed:
            if any(x.strip(".") in ext.lower() for x in self.compressedExtensions):
                print("Skipping raw comparison for compressed data: {}".format(ext))
                continue
            numpy.testing.assert_array_equal(imgData3D, self.imgData3D)

    def testBasic3DcStackFromGlobString(self, empty_project_file, graph):
        """Test if stacked 2d 3-channel files are loaded correctly"""
        # For some reason vigra saves 2D+c data compressed in gifs, so skip!
        for fileName, nickname in zip(self.imgFileNameGlobs2Dc, self.imgFileNameGlobs2DcNicknames):
            reader = OperatorWrapper(OpDataSelection, graph=graph, operator_kwargs={"forceAxisOrder": False})
            reader.WorkingDirectory.setValue(str(Path(empty_project_file.filename).parent))

            reader.Dataset.setValues([FilesystemDatasetInfo(filePath=fileName, sequence_axis="z")])

            # Read the test files using the data selection operator and verify the contents
            imgData3Dc = reader.Image[0][...].wait()

            # Check the file name output
            assert reader.ImageName[0].value == nickname
            # Check raw images
            assert imgData3Dc.shape == self.imgData3Dc.shape, (imgData3Dc.shape, self.imgData3Dc.shape)
            # skip this if image was saved compressed:
            if any(x in fileName.lower() for x in self.compressedExtensions + [".gif"]):
                print("Skipping raw comparison for compressed data: {}".format(fileName))
                continue
            numpy.testing.assert_array_equal(imgData3Dc, self.imgData3Dc)


class TestOpDataSelection_SingleFileH5Stacks:
    @classmethod
    def setup_class(cls):
        cls.tmpdir = tempfile.mkdtemp()
        cls.projectFileName = os.path.join(cls.tmpdir, "testProject.ilp")
        # generate some test data 'tczyx'
        cls.imgData3Dct = numpy.random.randint(0, 256, (10, 3, 8, 7, 6)).astype(numpy.uint8)

        # write a h5-file to directory
        cls.image_file_name = os.path.join(cls.tmpdir, "multi-h5.h5")

        h5file = h5py.File(cls.image_file_name, "w")
        cls.file_names = []
        try:
            g1 = h5file.create_group("g1")
            for t_index, t_slice in enumerate(cls.imgData3Dct):
                file_name = "timeslice_{:03d}".format(t_index)
                g1.create_dataset(file_name, data=t_slice)
                cls.file_names.append("{}/g1/{}".format(cls.image_file_name, file_name))
        finally:
            h5file.close()

        cls.glob_string = "{}/g1/timeslice_*".format(cls.image_file_name)
        # Create a 'project' file and give it some data
        cls.projectFile = h5py.File(cls.projectFileName, "w")
        cls.projectFile.create_group("DataSelection")
        cls.projectFile["DataSelection"].create_group("local_data")
        # Use the same data as the 3d+c data (above)
        cls.projectFile["DataSelection/local_data"].create_dataset("dataset1", data=cls.imgData3Dct)
        cls.projectFile.flush()

    @classmethod
    def teardown_class(cls):
        cls.projectFile.close()
        try:
            shutil.rmtree(cls.tmpdir)
        except OSError as e:
            print("Exception caught while deleting temporary files: {}".format(e))

    def test_load_single_file_with_glob(self, graph):
        reader = OperatorWrapper(OpDataSelection, graph=graph, operator_kwargs={"forceAxisOrder": False})
        reader.WorkingDirectory.setValue(os.getcwd())

        reader.Dataset.setValues([FilesystemDatasetInfo(filePath=self.glob_string, sequence_axis="t")])

        # Read the test files using the data selection operator and verify the contents
        imgData = reader.Image[0][...].wait()

        # Check raw images
        assert imgData.shape == self.imgData3Dct.shape, (imgData.shape, self.imgData3Dct.shape)

        numpy.testing.assert_array_equal(imgData, self.imgData3Dct)

    def test_load_single_file_with_list(self, graph):
        reader = OperatorWrapper(OpDataSelection, graph=graph, operator_kwargs={"forceAxisOrder": False})
        reader.WorkingDirectory.setValue(os.getcwd())

        fileNameString = os.path.pathsep.join(self.file_names)
        info = FilesystemDatasetInfo(filePath=fileNameString, sequence_axis="t")

        reader.Dataset.setValues([info])

        # Read the test files using the data selection operator and verify the contents
        imgData = reader.Image[0][...].wait()
        print("imgData", reader.Image.meta.axistags, reader.Image.meta.original_axistags)

        # Check raw images
        assert imgData.shape == self.imgData3Dct.shape, (imgData.shape, self.imgData3Dct.shape)

        numpy.testing.assert_array_equal(imgData, self.imgData3Dct)


class TestOpDataSelection_FileSeriesStacks:
    @pytest.fixture(scope="class")
    def tempdir(self, tmp_path_factory):
        temp_dir = tmp_path_factory.mktemp("test_stack_along_data")
        yield temp_dir
        shutil.rmtree(str(temp_dir))

    @pytest.fixture(scope="class")
    def series_data(self):
        R = [
            [1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        ]
        G = [
            [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0],
        ]
        B = [
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0],
        ]
        data = {
            "rgb00c": numpy.array(R, dtype=numpy.float32),  # b&w letters
            "rgb10c": numpy.array(G, dtype=numpy.float32),
            "rgb20c": numpy.array(B, dtype=numpy.float32),
        }
        data["rgb01c"] = data["rgb00c"][..., None]  # b&w letters with empty channel axis
        data["rgb11c"] = data["rgb10c"][..., None]
        data["rgb21c"] = data["rgb20c"][..., None]
        data["rgb03c"] = numpy.zeros((data["rgb00c"].shape[0], data["rgb00c"].shape[1], 3), dtype=numpy.float32)
        data["rgb13c"] = numpy.zeros((data["rgb10c"].shape[0], data["rgb10c"].shape[1], 3), dtype=numpy.float32)
        data["rgb23c"] = numpy.zeros((data["rgb20c"].shape[0], data["rgb20c"].shape[1], 3), dtype=numpy.float32)
        data["rgb03c"][..., 0] = data["rgb00c"]  # red R
        data["rgb13c"][..., 1] = data["rgb10c"]  # green G
        data["rgb23c"][..., 2] = data["rgb20c"]  # blue B
        return data

    @pytest.fixture(scope="class")
    def save_test_data(self, series_data, tempdir):
        base = tempdir
        for name, data in series_data.items():
            # save as h5
            save_to_hdf5(dataset_name="data", data=data, filename=base / f"{name}.h5")

            # save as png and tiff, if possible
            if name.endswith("0c"):
                im = Image.fromarray(data)
                im.save(base / f"{name}.tiff")
                vigra.impex.writeImage(image=(data.T * 255).astype(numpy.uint8), filename=str(base / f"{name}.png"))
            elif name.endswith("1c"):
                vigra.impex.writeImage(
                    image=(data.transpose(1, 0, 2) * 255).astype(numpy.uint8), filename=str(base / f"{name}.png")
                )
            elif name.endswith("3c"):
                data = (data * 255).astype(numpy.uint8)
                im = Image.fromarray(data, mode="RGB")
                im.save(base / f"{name}.tiff")
                vigra.impex.writeImage(image=data.transpose(1, 0, 2), filename=str(base / f"{name}.png"))

    @pytest.fixture(scope="class")
    def expected_data(self, series_data):
        series_0c = [series_data["rgb00c"], series_data["rgb10c"], series_data["rgb20c"]]
        series_3c = [series_data["rgb03c"], series_data["rgb13c"], series_data["rgb23c"]]
        return {
            "rgb0c_stack": numpy.stack(series_0c, axis=0),
            "rgb0c_stack_t": numpy.stack(series_0c, axis=2).transpose(1, 0, 2) * 255,
            "rgb0c_stack_2": numpy.stack(series_0c, axis=2),
            "rgb3c_concat": numpy.concatenate(series_3c, axis=2),
            "rgb3c_concat_t": numpy.concatenate(series_3c, axis=2).transpose(1, 0, 2) * 255,
            "rgb3c_concat_255": numpy.concatenate(series_3c, axis=2) * 255,
            "rgb0c_stack_None": numpy.stack(series_0c, axis=0)[..., None],
            "rgb0c_stack_None255": numpy.stack(series_0c, axis=0)[..., None] * 255,
            "rgb3c_stack": numpy.stack(series_3c, axis=0),
            "rgb3c_stack255": numpy.stack(series_3c, axis=0) * 255,
        }

    @pytest.mark.parametrize(
        "name, extension, sequence_axis, expected_key",
        [
            ["rgb*0c", ".h5/data", "c", "rgb0c_stack"],
            ["rgb*0c", ".png", "c", "rgb0c_stack_t"],
            ["rgb*0c", ".tiff", "c", "rgb0c_stack"],
            ["rgb*1c", ".h5/data", "c", "rgb0c_stack_2"],
            ["rgb*1c", ".png", "c", "rgb0c_stack_t"],
            ["rgb*3c", ".h5/data", "c", "rgb3c_concat"],
            ["rgb*3c", ".png", "c", "rgb3c_concat_t"],
            ["rgb*3c", ".tiff", "c", "rgb3c_concat_255"],
            ["rgb*0c", ".h5/data", "z", "rgb0c_stack_None"],
            ["rgb*0c", ".png", "z", "rgb0c_stack_None255"],
            ["rgb*0c", ".tiff", "z", "rgb0c_stack_None"],
            ["rgb*1c", ".h5/data", "z", "rgb0c_stack_None"],
            ["rgb*1c", ".png", "z", "rgb0c_stack_None255"],
            ["rgb*3c", ".h5/data", "z", "rgb3c_stack"],
            ["rgb*3c", ".png", "z", "rgb3c_stack255"],
            ["rgb*3c", ".tiff", "z", "rgb3c_stack255"],
            ["rgb*0c", ".h5/data", "t", "rgb0c_stack_None"],
            ["rgb*0c", ".png", "t", "rgb0c_stack_None255"],
            ["rgb*0c", ".tiff", "t", "rgb0c_stack_None"],
            ["rgb*1c", ".h5/data", "t", "rgb0c_stack_None"],
            ["rgb*1c", ".png", "t", "rgb0c_stack_None255"],
            ["rgb*3c", ".h5/data", "t", "rgb3c_stack"],
            ["rgb*3c", ".png", "t", "rgb3c_stack255"],
            ["rgb*3c", ".tiff", "t", "rgb3c_stack255"],
        ],
    )
    def test_stack_along(
        self, tempdir, save_test_data, expected_data, graph, name, extension, sequence_axis, expected_key
    ):
        fileName = tempdir / f"{name}{extension}"
        reader = OpDataSelection(graph=graph, forceAxisOrder=False)
        reader.WorkingDirectory.setValue(os.getcwd())
        reader.Dataset.setValue(FilesystemDatasetInfo(filePath=str(fileName), sequence_axis=sequence_axis))
        read = reader.Image[...].wait()
        expected = expected_data[expected_key]
        try:
            numpy.testing.assert_allclose(read, expected), f"{name}: {read.shape}, {expected.shape}"
        finally:
            reader.cleanUp()  # Ensure tempdir can be deleted


def mock_precomputed_requests(monkeypatch, url: str, info: dict, chunks: dict[str, numpy.array]):
    """
    Monkeypatches requests.get to mock a server hosting a precomputed dataset.
    Needs to be passed the monkeypatch fixture and dataset parameters.
    """

    def mock_response_for_url(_url):
        response = Mock()
        response.status_code = 200
        ext = _url.lstrip(url)
        if ext == "info":
            response.content = json.dumps(info)
        elif ext in chunks:
            response.content = chunks[ext].tobytes()
        else:
            raise KeyError(f"Unknown mock url: {_url}")
        return response

    monkeypatch.setattr(requests, "get", lambda _url: mock_response_for_url(_url))


class TestOpDataSelection_PrecomputedChunks:
    SHAPE_SCALED_XYZ = (12, 10, 1)
    SHAPE_ORIGINAL_XYZ = (24, 20, 1)
    CHUNK_SIZE_XYZ = (16, 16, 1)
    CHUNKS = {  # numpy default axis order is zyx; we use it as it also works fine with the operator's tczyx
        "1600_1600_70/0-12_0-10_0-1": numpy.random.randint(0, 256, (1, 10, 12), dtype=numpy.uint16),
        "800_800_70/0-16_0-16_0-1": numpy.random.randint(0, 256, (1, 16, 16), dtype=numpy.uint16),
        "800_800_70/16-24_0-16_0-1": numpy.random.randint(0, 256, (1, 16, 8), dtype=numpy.uint16),
        "800_800_70/0-16_16-20_0-1": numpy.random.randint(0, 256, (1, 4, 16), dtype=numpy.uint16),
        "800_800_70/16-24_16-20_0-1": numpy.random.randint(0, 256, (1, 4, 8), dtype=numpy.uint16),
    }
    IMAGE_SCALED = CHUNKS["1600_1600_70/0-12_0-10_0-1"]
    IMAGE_ORIGINAL = numpy.concatenate(
        [
            numpy.concatenate([CHUNKS["800_800_70/0-16_0-16_0-1"], CHUNKS["800_800_70/16-24_0-16_0-1"]], axis=2),
            numpy.concatenate([CHUNKS["800_800_70/0-16_16-20_0-1"], CHUNKS["800_800_70/16-24_16-20_0-1"]], axis=2),
        ],
        axis=1,
    )
    MOCK_DATASET_URL = "precomputed://https://mocked.com/precomputed_dataset"
    INFO_JSON = {
        "@type": "neuroglancer_multiscale_volume",
        "type": "image",
        "data_type": "uint16",
        "num_channels": 1,
        "scales": [
            {
                "key": "800_800_70",
                "size": list(SHAPE_ORIGINAL_XYZ),
                "resolution": [800, 800, 70],
                "voxel_offset": [0, 0, 0],
                "chunk_sizes": [list(CHUNK_SIZE_XYZ)],
                "encoding": "raw",
            },
            {
                "key": "1600_1600_70",
                "size": list(SHAPE_SCALED_XYZ),
                "resolution": [1600, 1600, 70],
                "voxel_offset": [0, 0, 0],
                "chunk_sizes": [list(CHUNK_SIZE_XYZ)],
                "encoding": "raw",
            },
        ],
    }

    @pytest.fixture
    def datasetInfo(self, monkeypatch):
        mock_precomputed_requests(monkeypatch, self.MOCK_DATASET_URL, self.INFO_JSON, self.CHUNKS)
        return MultiscaleUrlDatasetInfo(url=self.MOCK_DATASET_URL)

    @pytest.fixture
    def op(self, graph, monkeypatch, datasetInfo) -> OpDataSelection:
        op = OpDataSelection(graph=graph)
        op.WorkingDirectory.setValue(os.getcwd())
        op.ActiveScale.setValue(DEFAULT_SCALE_KEY)
        op.Dataset.setValue(datasetInfo)
        return op

    def test_load_precomputed_chunks_over_http(self, op):
        # Default scale should be lowest resolution
        loaded_scale0 = op.Image[:].wait()
        numpy.testing.assert_allclose(loaded_scale0, self.IMAGE_SCALED.reshape((1, 1, 1, 10, 12)))

        assert op.Image.meta.scales == OrderedDict(
            [
                ("800_800_70", OrderedDict([("c", 1), ("z", 1), ("y", 20), ("x", 24)])),
                ("1600_1600_70", OrderedDict([("c", 1), ("z", 1), ("y", 10), ("x", 12)])),
            ]
        )

        # Switch to original unscaled resolution (first in the list, see multiscaleStore.multiscales)
        scale_keys = list(op.Image.meta.scales.keys())
        op.ActiveScale.setValue(scale_keys[0])
        loaded_scale1 = op.Image[:].wait()
        numpy.testing.assert_allclose(loaded_scale1, self.IMAGE_ORIGINAL.reshape((1, 1, 1, 20, 24)))

    def test_scale_updates_dataset_info(self, op, datasetInfo):
        scale_keys = list(op.Image.meta.scales.keys())
        op.ActiveScale.setValue(scale_keys[1])
        assert datasetInfo.working_scale == scale_keys[1]


class OpShapeChecker(Operator):
    """A mock op that emulates the checking of shape constraints across roles,
    like OpObjectExtraction._checkConstraints or the tagged-shape check in OpSimpleStacker (multicut)."""

    Role1 = InputSlot()
    Role2 = InputSlot()
    Role3 = InputSlot()
    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.input_ready_checks = 0

        self.Role1.notifyReady(self._checkConstraints)  # Shape check as in OpObjectExtraction
        self.Role2.notifyReady(self._checkConstraints)

    def _checkConstraints(self, *_):
        if self.Role1.ready() and self.Role2.ready():
            self.input_ready_checks += 1
            rawTaggedShape = self.Role1.meta.getTaggedShape()
            segTaggedShape = self.Role2.meta.getTaggedShape()
            rawTaggedShape["c"] = None
            segTaggedShape["c"] = None
            if dict(rawTaggedShape) != dict(segTaggedShape):
                raise DatasetConstraintError(
                    "test", f"Mismatching shapes would fail in OpObjectExtraction: {rawTaggedShape} != {segTaggedShape}"
                )

    def setupOutputs(self):
        # Shape check as in OpSimpleStacker
        shape1 = dict(self.Role1.meta.getTaggedShape())
        shape2 = dict(self.Role2.meta.getTaggedShape())
        shape3 = dict(self.Role3.meta.getTaggedShape())
        if shape1 != shape2 or shape2 != shape3:
            raise DatasetConstraintError(
                "test", f"Must not try to set up this op with mismatching input images: {shape1}, {shape2}, {shape3}"
            )


class TestOpDataSelection_OMEZarr:
    SHAPE_SCALED_ZYX = (1, 10, 12)
    SHAPE_ORIGINAL_ZYX = (1, 20, 24)
    CHUNK_SIZE_ZYX = (1, 16, 16)
    IMAGE_SCALED = numpy.random.randint(0, 256, SHAPE_SCALED_ZYX, dtype=numpy.uint16)
    IMAGE_ORIGINAL = numpy.random.randint(0, 256, SHAPE_ORIGINAL_ZYX, dtype=numpy.uint16)
    S1ZARRAY = {
        "zarr_format": 2,
        "shape": list(SHAPE_SCALED_ZYX),
        "chunks": list(CHUNK_SIZE_ZYX),
        "dtype": "|u1",
        "compressor": {"id": "gzip", "level": -1},
        "fill_value": 0,
        "filters": [],
        "order": "C",
        "dimension_separator": "/",
    }
    S0ZARRAY = {
        "zarr_format": 2,
        "shape": list(SHAPE_ORIGINAL_ZYX),
        "chunks": list(CHUNK_SIZE_ZYX),
        "dtype": "|u1",
        "compressor": {"id": "gzip", "level": -1},
        "fill_value": 0,
        "filters": [],
        "order": "C",
        "dimension_separator": "/",
    }
    ZATTRS = {
        "multiscales": [
            {
                "name": "dataset.zarr",
                "type": "Sample",
                "version": "0.4",
                "axes": [
                    {"type": "space", "name": "z", "unit": "pixel"},
                    {"type": "space", "name": "y", "unit": "pixel"},
                    {"type": "space", "name": "x", "unit": "pixel"},
                ],
                "datasets": [
                    {
                        "path": "s0",
                        "coordinateTransformations": [
                            {"scale": [1.0, 1.0, 1.0], "type": "scale"},
                            {"translation": [0.0, 0.0, 0.0], "type": "translation"},
                        ],
                    },
                    {
                        "path": "s1",
                        "coordinateTransformations": [
                            {"scale": [2.0, 2.0, 2.0], "type": "scale"},
                            {"translation": [0.0, 0.0, 0.0], "type": "translation"},
                        ],
                    },
                ],
                "coordinateTransformations": [],
            }
        ]
    }

    @pytest.fixture
    def mock_ome_zarr_metadata(self, monkeypatch):
        """Monkeypatches FSStore.__getitem__ to mock metadata responses of an OME-Zarr dataset."""
        responses = {".zattrs": self.ZATTRS, "s1/.zarray": self.S1ZARRAY, "s0/.zarray": self.S0ZARRAY}
        monkeypatch.setattr(zarr.storage.FSStore, "__getitem__", lambda _self, key: json.dumps(responses[key]).encode())

    @pytest.fixture
    def mock_ome_zarr_data(self, monkeypatch):
        """Monkeypatches zarr.Array.__getitem__ to mock contents of an OME-Zarr dataset."""
        images = {"s0": self.IMAGE_ORIGINAL, "s1": self.IMAGE_SCALED}
        monkeypatch.setattr(zarr.Array, "__getitem__", lambda _self, slicing: images[_self.path][slicing])

    @pytest.fixture(
        params=[
            "https://localhost:8000/dataset.zarr",
            "s3://some-bucket/dataset.zarr",
            "https://s3.selfhoster.com/bucket/dataset.zarr",
        ]
    )
    def datasetInfo(self, request, monkeypatch, mock_ome_zarr_metadata):
        return MultiscaleUrlDatasetInfo(url=request.param)

    @pytest.fixture
    def op(self, graph, monkeypatch, datasetInfo):
        op = OpDataSelection(graph=graph)
        op.WorkingDirectory.setValue(os.getcwd())
        op.ActiveScale.setValue(DEFAULT_SCALE_KEY)
        op.Dataset.setValue(datasetInfo)
        return op

    def test_ome_zarr_loads_via_FSStore_and_ZarrArray(self, op, mock_ome_zarr_data):
        # Default scale should be lowest resolution
        loaded_scale0 = op.Image[:].wait()
        numpy.testing.assert_allclose(loaded_scale0, self.IMAGE_SCALED.reshape((1, 1, 1, 10, 12)))

        assert op.Image.meta.scales == OrderedDict(
            [
                ("s0", OrderedDict([("z", 1), ("y", 20), ("x", 24)])),
                ("s1", OrderedDict([("z", 1), ("y", 10), ("x", 12)])),
            ]
        )

        # Switch to original unscaled resolution (first in the list, see multiscaleStore.multiscales)
        scale_keys = list(op.Image.meta.scales.keys())
        op.ActiveScale.setValue(scale_keys[0])
        loaded_scale1 = op.Image[:].wait()
        numpy.testing.assert_allclose(loaded_scale1, self.IMAGE_ORIGINAL.reshape((1, 1, 1, 20, 24)))

    def test_scale_updates_dataset_info(self, op, datasetInfo):
        scale_keys = list(op.Image.meta.scales.keys())
        op.ActiveScale.setValue(scale_keys[1])
        assert datasetInfo.working_scale == scale_keys[1]

    @pytest.fixture
    def op_data_lane(self, graph) -> OpDataSelectionGroup:
        op_data_lane = OpDataSelectionGroup(graph=graph)
        op_data_lane.WorkingDirectory.setValue(os.getcwd())
        op_data_lane.DatasetRoles.setValue(["Raw Data", "Segmentation", "Another Role"])
        assert len(op_data_lane.DatasetGroup) == 3 and len(op_data_lane.ImageGroup) == 3
        return op_data_lane

    def test_scale_change_without_transaction_forbidden(self, op_data_lane, mock_ome_zarr_metadata):
        dataset_info_raw = MultiscaleUrlDatasetInfo(url="https://s3.localhost/rawdata.zarr")
        dataset_info_segmentation = MultiscaleUrlDatasetInfo(url="https://s3.localhost/segmentation.zarr")
        dataset_info_other = MultiscaleUrlDatasetInfo(url="https://s3.localhost/sthelse.zarr")
        op_data_lane.DatasetGroup[0].setValue(dataset_info_raw)
        op_data_lane.DatasetGroup[1].setValue(dataset_info_segmentation)
        op_data_lane.DatasetGroup[2].setValue(dataset_info_other)

        with pytest.raises(TransactionRequiredError, match="must disconnect"):
            op_data_lane.ActiveScaleGroup.setValue("s0")

    @pytest.fixture
    def cross_role_ops(self, op_data_lane, graph) -> Tuple[OpDataSelectionGroup, OpShapeChecker]:
        """A data selection lane op chained with a shape-checking op that cannot work with inputs of different shapes.
        This emulates e.g. object classification or multicut."""
        opSumInputs = OpMultiArrayMerger(graph=graph)  # Problematic op from object classification
        opSumInputs.MergingFunction.setValue(sum)
        opSumInputs.Inputs.resize(1)  # Rare kind of op with a level-1 input; unreadiness signalling was buggy here
        # In OpThresholdTwoLevels, the second data role first goes through a bunch of other ops,
        # but opSumInputs.Inputs[0] is connected to the output of that chain.
        opSumInputs.Inputs[0].connect(op_data_lane.ImageGroup[1])
        op_shape_check = OpShapeChecker(graph=graph)
        op_shape_check.Role1.connect(op_data_lane.ImageGroup[0])
        op_shape_check.Role2.connect(opSumInputs.Output)
        op_shape_check.Role3.connect(op_data_lane.ImageGroup[2])
        return op_data_lane, op_shape_check

    def test_multiscales_can_be_used_in_multiple_roles(self, cross_role_ops, mock_ome_zarr_metadata):
        op_data_lane, op_shape_check = cross_role_ops
        dataset_info_raw = MultiscaleUrlDatasetInfo(url="https://s3.localhost/rawdata.zarr")
        dataset_info_segmentation = MultiscaleUrlDatasetInfo(url="https://s3.localhost/segmentation.zarr")
        dataset_info_other = MultiscaleUrlDatasetInfo(url="https://s3.localhost/sthelse.zarr")
        op_data_lane.DatasetGroup[0].setValue(dataset_info_raw)
        op_data_lane.DatasetGroup[1].setValue(dataset_info_segmentation)
        assert op_shape_check.input_ready_checks == 1
        op_data_lane.DatasetGroup[2].setValue(dataset_info_other)
        assert op_shape_check._setup_count == 1, "setting all datasets should set up shape-checking op"

        op_data_lane.ScaleChangeFinished.disconnect()
        op_data_lane.ActiveScaleGroup.setValue("s0")
        assert op_shape_check.input_ready_checks == 1  # should not have propagated to shape checker
        op_data_lane.ScaleChangeFinished.setValue(True)
        assert op_shape_check.input_ready_checks == 2
        assert op_shape_check._setup_count == 2, "changing scale should trigger shape-checking op setup"

    @pytest.fixture
    def two_ome_zarrs(self, tmp_path) -> Tuple[Path, Path]:
        """
        Sets up a two random OME-Zarr datasets, one with 2 and one with 3 scales.
        Returns absolute path to the two datasets.
        The two-scales dataset represents a multiscale segmentation exported
        from the first downscale of the three-scales dataset.
        """
        subdir3 = "scales3.zarr"
        subdir2 = "scales2.zarr"
        zarr_dir3 = tmp_path / subdir3
        zarr_dir2 = tmp_path / subdir2
        zarr_dir3.mkdir(parents=True, exist_ok=True)
        zarr_dir2.mkdir(parents=True, exist_ok=True)

        dataset_shape = [2, 3, 4, 100, 100]  # tczyx for good measure
        chunk_size = [2, 3, 3, 64, 64]
        axes_json = [
            {"type": "space", "name": "t"},
            {"type": "space", "name": "c"},
            {"type": "space", "name": "z"},
            {"type": "space", "name": "y"},
            {"type": "space", "name": "x"},
        ]
        zattrs3 = {
            "multiscales": [
                {
                    "name": "some.zarr",
                    "version": "0.4",
                    "axes": axes_json,
                    "datasets": [
                        {
                            "path": "s0",
                            "coordinateTransformations": [
                                {"scale": [1.0 for _ in dataset_shape], "type": "scale"},
                            ],
                        },
                        {
                            "path": "s1",
                            "coordinateTransformations": [
                                {"scale": [2.0 for _ in dataset_shape], "type": "scale"},
                            ],
                        },
                        {
                            "path": "s2",
                            "coordinateTransformations": [
                                {"scale": [4.0 for _ in dataset_shape], "type": "scale"},
                            ],
                        },
                    ],
                    "coordinateTransformations": [],
                },
            ]
        }
        zattrs2 = {
            "multiscales": [
                {
                    "name": "some.zarr",
                    "version": "0.4",
                    "axes": axes_json,
                    "datasets": [  # omit what was the raw scale on the three-scales dataset
                        {
                            "path": "s1",
                            "coordinateTransformations": [
                                {"scale": [2.0 for _ in dataset_shape], "type": "scale"},
                            ],
                        },
                        {
                            "path": "s2",
                            "coordinateTransformations": [
                                {"scale": [4.0 for _ in dataset_shape], "type": "scale"},
                            ],
                        },
                    ],
                    "coordinateTransformations": [],
                },
            ]
        }
        (zarr_dir3 / ".zattrs").write_text(json.dumps(zattrs3))
        (zarr_dir2 / ".zattrs").write_text(json.dumps(zattrs2))

        image_original = numpy.random.randint(0, 256, dataset_shape, dtype=numpy.uint16)
        image_scaled = image_original[:, :, :, ::2, ::2]
        image_scaled2 = image_scaled[:, :, :, ::2, ::2]
        chunks = tuple(chunk_size)
        zarr.array(
            image_original, chunks=chunks, store=zarr.DirectoryStore(str(zarr_dir3 / "s0")), **OME_ZARR_V_0_4_KWARGS
        )
        zarr.array(
            image_scaled, chunks=chunks, store=zarr.DirectoryStore(str(zarr_dir3 / "s1")), **OME_ZARR_V_0_4_KWARGS
        )
        zarr.array(
            image_scaled2, chunks=chunks, store=zarr.DirectoryStore(str(zarr_dir3 / "s2")), **OME_ZARR_V_0_4_KWARGS
        )
        zarr.array(
            image_scaled, chunks=chunks, store=zarr.DirectoryStore(str(zarr_dir2 / "s1")), **OME_ZARR_V_0_4_KWARGS
        )
        zarr.array(
            image_scaled2, chunks=chunks, store=zarr.DirectoryStore(str(zarr_dir2 / "s2")), **OME_ZARR_V_0_4_KWARGS
        )

        return zarr_dir2, zarr_dir3

    def test_missing_scale_in_other_role_raises(self, cross_role_ops, two_ome_zarrs):
        """
        2scales is the "segmentation", 3scales is the "raw data".
        This mimics the scenario with multiscale export v1:
        The user runs e.g. pixel classification on the first downscale (s1) of the 3scales raw data and then
        exports "multi-scale OME-Zarr".
        The export, 2scales, has no s0 because it was exported from the s1 downscale of 3scales,
        and the multiscale export doesn't do upscaling to match scales larger than the working scale.
        """
        op_data_lane, op_shape_check = cross_role_ops
        path_zarr_2scales, path_zarr_3scales = two_ome_zarrs
        dataset_info_raw = MultiscaleUrlDatasetInfo(url=path_zarr_3scales.as_uri())
        dataset_info_segmentation = MultiscaleUrlDatasetInfo(url=path_zarr_2scales.as_uri())
        dataset_info_other = MultiscaleUrlDatasetInfo(url=path_zarr_2scales.as_uri())
        op_data_lane.DatasetGroup[0].setValue(dataset_info_raw)
        op_data_lane.DatasetGroup[1].setValue(dataset_info_segmentation)
        op_data_lane.DatasetGroup[2].setValue(dataset_info_other)
        assert op_shape_check._setup_count == 1, "setting all datasets should set up shape-checking op"

        with pytest.raises(ScaleNotFoundError):
            op_data_lane.ScaleChangeFinished.disconnect()
            op_data_lane.ActiveScaleGroup.setValue("s0")
            op_data_lane.ScaleChangeFinished.setValue(True)


class TestOpDataSelection_DatasetInfo:
    # Having a bad char (:) in the url makes sure that nickname conversion to a file-name-safe string is covered
    MOCK_PRECOMPUTED_URL = "precomputed://http://localhost:8000"
    MOCK_PRECOMPUTED_INFO = {
        "type": "image",
        "data_type": "uint16",
        "num_channels": 1,
        "scales": [{"key": "foo", "chunk_sizes": [[1, 1, 1]], "resolution": [0, 0, 0], "size": [1, 1, 1]}],
    }
    MOCK_PROJECT_SUBPATH = "mock_dir"

    @pytest.fixture
    def mock_project(self, data_path):
        mock_project_location = data_path / self.MOCK_PROJECT_SUBPATH
        data = mock.Mock()
        data.shape = (10, 10)
        data.attrs = {}
        project = mock.MagicMock()
        project.filename = mock_project_location / "mock.file"
        project.__getitem__.return_value = data
        return project

    @pytest.fixture
    def mock_ome_zarr_metadata(self, monkeypatch):
        """Monkeypatches FSStore.__getitem__ to mock metadata responses of an OME-Zarr dataset."""
        responses = {
            ".zattrs": {
                "multiscales": [
                    {"axes": [{"name": "x"}, {"name": "y"}], "datasets": [{"path": "s0"}], "version": "0.4"}
                ]
            },
            "s0/.zarray": {
                "zarr_format": 2,
                "dtype": "|u1",
                "fill_value": 0,
                "shape": [1, 1],
                "chunks": [1, 1],
                "compressor": {"id": "gzip", "level": -1},
                "order": "C",
                "filters": [],
            },
        }
        monkeypatch.setattr(zarr.storage.FSStore, "__getitem__", lambda _self, key: json.dumps(responses[key]).encode())

    def test_default_export_paths_filesystem(self, data_path):
        # Need to provide actually existing files because file-based DatasetInfos
        # read the file for metadata during instantiation.
        dataset_info = FilesystemDatasetInfo(filePath=str(data_path / "inputdata" / "3d1c-synthetic.h5"))
        assert dataset_info.default_output_dir == data_path / "inputdata"
        dataset_info2 = RelativeFilesystemDatasetInfo(filePath=str(data_path / "inputdata" / "3d1c-synthetic.h5"))
        assert dataset_info2.default_output_dir == data_path / "inputdata"

    def test_default_export_paths_project(self, data_path, mock_project):
        dataset_info = ProjectInternalDatasetInfo(inner_path="foo", project_file=mock_project)
        assert dataset_info.default_output_dir == data_path / self.MOCK_PROJECT_SUBPATH

    def test_default_export_paths_url(self, data_path, mock_project, monkeypatch, mock_ome_zarr_metadata):
        # Need to mock requests because web-based DatasetInfos
        # request metadata from the server during instantiation
        mock_precomputed_requests(monkeypatch, self.MOCK_PRECOMPUTED_URL, self.MOCK_PRECOMPUTED_INFO, {})
        dataset_info = MultiscaleUrlDatasetInfo(url=self.MOCK_PRECOMPUTED_URL, project_file=mock_project)
        assert dataset_info.default_output_dir == data_path / self.MOCK_PROJECT_SUBPATH

        dataset_info2 = MultiscaleUrlDatasetInfo(url="http://localhost:8000/some.zarr", project_file=mock_project)
        assert dataset_info2.default_output_dir == data_path / self.MOCK_PROJECT_SUBPATH

        # When using a "file:" URI, the default export path should be the dataset's parent directory
        ome_zarr_path = data_path / "dataset.zarr"
        dataset_info3 = MultiscaleUrlDatasetInfo(url=ome_zarr_path.as_uri(), project_file=mock_project)
        assert dataset_info3.default_output_dir == data_path

    @pytest.fixture
    def ilp_with_legacy_urldatasetinfo(self, empty_project_file):
        ilp = empty_project_file
        info_group = (
            ilp.require_group(TOP_GROUP_NAME).require_group("infos").require_group("0").require_group("Raw Data")
        )
        info_entries = {
            "__class__": "UrlDatasetInfo",
            "nickname": self.MOCK_PRECOMPUTED_URL.lstrip("precomputed://http://"),
            "filePath": self.MOCK_PRECOMPUTED_URL,
            "allowLabels": True,
        }
        for k, v in info_entries.items():
            info_group.create_dataset(k, data=v)
        return ilp

    def test_urldatasetinfo_serializes_equivalent_to_multiscaleurldatasetinfo(
        self, ilp_with_legacy_urldatasetinfo, monkeypatch
    ):
        mock_precomputed_requests(monkeypatch, self.MOCK_PRECOMPUTED_URL, self.MOCK_PRECOMPUTED_INFO, {})
        legacy_group = ilp_with_legacy_urldatasetinfo[TOP_GROUP_NAME]["infos"]["0"]["Raw Data"]
        legacy_dataset_info = UrlDatasetInfo.from_h5_group(legacy_group)
        modern_dataset_info = MultiscaleUrlDatasetInfo(url=self.MOCK_PRECOMPUTED_URL)
        # ID is randomly generated, but we want them to be identical for this test
        legacy_dataset_info.legacy_datasetId = modern_dataset_info.legacy_datasetId

        # We know that as of now, a legacy UrlDatasetInfo would be equivalent to a modern MultiscaleUrlDatasetInfo
        # with the scale set to the original resolution (the last in the list), and locked-in.
        modern_dataset_info.working_scale = self.MOCK_PRECOMPUTED_INFO["scales"][-1]["key"]
        modern_dataset_info.scale_locked = True
        assert legacy_dataset_info.to_json_data() == modern_dataset_info.to_json_data()


def test_cleanup(data_path, graph):
    filepath1 = data_path / "inputdata" / "2d3c.h5"  # Any file is fine
    filepath2 = data_path / "inputdata" / "3d.h5"
    reader = OpDataSelection(graph=graph)
    reader.WorkingDirectory.setValue(os.getcwd())

    # When
    reader.Dataset.setValue(FilesystemDatasetInfo(filePath=str(filepath1)))
    children_after_load = len(reader.children)
    reader.Dataset.setValue(FilesystemDatasetInfo(filePath=str(filepath2)))

    # Then
    assert len(reader.children) == children_after_load, "Did not clean up all children after input change"


def tagged_shape(keys, shape):
    return dict(zip(keys, shape))


@pytest.mark.parametrize(
    "shape1, shape2, match_expected",
    [
        (tagged_shape("xy", [5, 6]), tagged_shape("xy", [5, 6]), True),
        (tagged_shape("xy", [5, 6]), tagged_shape("yx", [6, 5]), True),
        (tagged_shape("xyc", [5, 6, 3]), tagged_shape("yx", [6, 5]), True),
        (tagged_shape("xy", [5, 6]), tagged_shape("yxc", [6, 5, 3]), True),
        (tagged_shape("xyc", [5, 6, 1]), tagged_shape("yxc", [6, 5, 3]), True),
        (tagged_shape("xyztc", [5, 6, 1, 1, 3]), tagged_shape("yx", [6, 5]), True),
        (tagged_shape("xy", [5, 6]), tagged_shape("tczyx", [1, 3, 1, 6, 5]), True),
        (tagged_shape("xyzt", [3, 4, 5, 6]), tagged_shape("tyzx", [6, 4, 5, 3]), True),
        (tagged_shape("xy", [5, 6]), tagged_shape("xy", [5, 7]), False),
        (tagged_shape("xyztc", [5, 6, 9, 8, 1]), tagged_shape("xy", [5, 6]), False),
        (tagged_shape("xyztc", [5, 6, 9, 8, 1]), tagged_shape("yx", [6, 5]), False),
        (tagged_shape("xyztc", [5, 6, 9, 8, 1]), tagged_shape("zty", [9, 8, 6]), False),
    ],
)
def test_eq_shapes(shape1: Dict[str, int], shape2: Dict[str, int], match_expected: bool):
    assert match_expected == eq_shapes(shape1, shape2)
