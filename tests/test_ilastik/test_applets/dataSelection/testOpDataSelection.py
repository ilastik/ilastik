from __future__ import print_function
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
#          http://ilastik.org/license.html
###############################################################################
import os
import shutil
import itertools
from collections import defaultdict
import numpy
import vigra
import lazyflow
import h5py
from PIL import Image
from lazyflow.graph import OperatorWrapper
from ilastik.applets.dataSelection.opDataSelection import OpDataSelection, DatasetInfo
from ilastik.applets.base.applet import DatasetConstraintError

import tempfile


class TestOpDataSelection_Basic2D(object):

    @classmethod
    def setup_class(cls):
        cls.tmpdir = tempfile.mkdtemp()
        cls.imgFileNames2D = []
        cls.imgFileNames2Dc = []
        # Comparison of compressed data not possible - those types will be
        # skipped in raw comparison:
        cls.compressedExtensions = ['.jpg', '.jpeg']
        cls.projectFileName = os.path.join(cls.tmpdir, 'testProject.ilp')

        # Create a couple test images of different types
        # in order to simplify and unify testing among the different file types
        # the extra dimension is added, as vigra would add one anyway.
        cls.imgData2D = numpy.random.randint(0, 255, (10, 11, 1)).astype(numpy.uint8)
        # v- image data variables in order to reflect the correct axis-order
        # otherwise the axes get scrambled when writing/reloading
        vimgData2D = vigra.VigraArray(
            cls.imgData2D,
            axistags=vigra.defaultAxistags('yxc'),
            dtype=numpy.uint8
        )

        testNpyFileName = os.path.join(cls.tmpdir, "testimage2D.npy")
        numpy.save(testNpyFileName, cls.imgData2D)
        cls.imgFileNames2D.append(testNpyFileName)

        testNpzFileName = os.path.join(cls.tmpdir, "testimage2D.npz")
        numpy.savez(testNpzFileName, data=cls.imgData2D)
        testNpzFileName = "{}/data".format(testNpzFileName)
        cls.imgFileNames2D.append(testNpzFileName)

        testH5FileName = os.path.join(cls.tmpdir, "testimage2D.h5")
        vigra.impex.writeHDF5(
            data=cls.imgData2D,
            filenameOrGroup=testH5FileName,
            pathInFile='test/data'
        )
        testH5FileName = "{}/test/data".format(testH5FileName)
        cls.imgFileNames2D.append(testH5FileName)

        for extension in vigra.impex.listExtensions().split(' '):
            tmpFileName = os.path.join(cls.tmpdir, "testImage2D.{}".format(extension))
            # not all extensions support this kind of pixeltype
            try:
                vigra.impex.writeImage(
                    vimgData2D,
                    tmpFileName,
                )
                cls.imgFileNames2D.append(tmpFileName)
            except RuntimeError as e:
                msg = str(e).replace('\n', '')
                print(
                    "Couldn't write temp 2D image file using vigra with `{}` "
                    "extension : {}".format(extension, msg)
                )

        cls.imgData2Dc = numpy.random.randint(0, 255, (100, 200, 3)).astype(numpy.uint8)
        vimgData2Dc = vigra.VigraArray(
            cls.imgData2Dc,
            axistags=vigra.defaultAxistags('yxc'),
            dtype=numpy.uint8
        )

        testNpyFileName = os.path.join(cls.tmpdir, "testimage2Dc.npy")
        numpy.save(testNpyFileName, cls.imgData2Dc)
        cls.imgFileNames2Dc.append(testNpyFileName)

        testNpzFileName = os.path.join(cls.tmpdir, "testimage2Dc.npz")
        numpy.savez(testNpzFileName, data=cls.imgData2Dc)
        testNpzFileName = "{}/data".format(testNpzFileName)
        cls.imgFileNames2Dc.append(testNpzFileName)

        testH5FileName = os.path.join(cls.tmpdir, "testimage2Dc.h5")
        vigra.impex.writeHDF5(
            data=cls.imgData2Dc,
            filenameOrGroup=testH5FileName,
            pathInFile='test/data'
        )
        testH5FileName = "{}/test/data".format(testH5FileName)
        cls.imgFileNames2Dc.append(testH5FileName)

        for extension in vigra.impex.listExtensions().split(' '):
            tmpFileName = os.path.join(cls.tmpdir, "testImage2Dc.{}".format(extension))
            # not all extensions support this kind of pixeltype
            try:
                vigra.impex.writeImage(
                    vimgData2Dc,
                    tmpFileName,
                )
                cls.imgFileNames2Dc.append(tmpFileName)
            except RuntimeError as e:
                msg = str(e).replace('\n', '')
                print(
                    "Couldn't write temp 2D+c image file using vigra with `{}` "
                    "extension : {}".format(extension, msg)
                )

        # Create a 'project' file and give it some data
        cls.projectFile = h5py.File(cls.projectFileName)
        cls.projectFile.create_group('DataSelection')
        cls.projectFile['DataSelection'].create_group('local_data')
        # Use the same data as the 2d+c data (above)
        cls.projectFile['DataSelection/local_data'].create_dataset('dataset1', data=cls.imgData2Dc)
        cls.projectFile.flush()

    @classmethod
    def teardown_class(cls):
        cls.projectFile.close()
        try:
            shutil.rmtree(cls.tmpdir)
        except OSError as e:
            print('Exception caught while deleting temporary files: {}'.format(e))

    def testBasic2D(self):
        """Test if plane 2d files are loaded correctly"""
        for fileName in self.imgFileNames2D:
            graph = lazyflow.graph.Graph()
            reader = OperatorWrapper(OpDataSelection, graph=graph, operator_kwargs={'forceAxisOrder': False})
            reader.ProjectFile.setValue(self.projectFile)
            reader.WorkingDirectory.setValue(os.getcwd())
            reader.ProjectDataGroup.setValue('DataSelection/local_data')

            info = DatasetInfo()
            # Will be read from the filesystem since the data won't be found in the project file.
            info.location = DatasetInfo.Location.ProjectInternal
            info.filePath = fileName
            info.internalPath = ""
            info.invertColors = False
            info.convertToGrayscale = False

            reader.Dataset.setValues([info])

            # Read the test files using the data selection operator and verify the contents
            imgData2D = reader.Image[0][...].wait()

            # Check the file name output
            assert reader.ImageName[0].value == fileName
            # Check raw images
            assert imgData2D.shape == self.imgData2D.shape
            # skip this if image was saved compressed:
            if any(x in fileName.lower() for x in self.compressedExtensions):
                print("Skipping raw comparison for compressed data: {}".format(fileName))
                continue
            numpy.testing.assert_array_equal(imgData2D, self.imgData2D)

    def testBasic2Dc(self):
        """Test if 2d 3-channel files are loaded correctly"""
        # For some reason vigra saves 2D+c data compressed in gifs, so skip!
        self.compressedExtensions.append('.gif')
        for fileName in self.imgFileNames2Dc:
            graph = lazyflow.graph.Graph()
            reader = OperatorWrapper(OpDataSelection, graph=graph, operator_kwargs={'forceAxisOrder': False})
            reader.ProjectFile.setValue(self.projectFile)
            reader.WorkingDirectory.setValue(os.getcwd())
            reader.ProjectDataGroup.setValue('DataSelection/local_data')

            info = DatasetInfo()
            # Will be read from the filesystem since the data won't be found in the project file.
            info.location = DatasetInfo.Location.ProjectInternal
            info.filePath = fileName
            info.internalPath = ""
            info.invertColors = False
            info.convertToGrayscale = False

            reader.Dataset.setValues([info])

            # Read the test files using the data selection operator and verify the contents
            imgData2Dc = reader.Image[0][...].wait()

            # Check the file name output
            assert reader.ImageName[0].value == fileName
            # Check raw images
            assert imgData2Dc.shape == self.imgData2Dc.shape, (imgData2Dc.shape, self.imgData2Dc.shape)
            # skip this if image was saved compressed:
            if any(x in fileName.lower() for x in self.compressedExtensions):
                print("Skipping raw comparison for compressed data: {}".format(fileName))
                continue
            numpy.testing.assert_array_equal(imgData2Dc, self.imgData2Dc)

#
#    def testColorInversion(self):
#        graph = lazyflow.graph.Graph()
#        reader = OpDataSelection(graph=graph)
#        reader.ProjectFile.setValue(self.projectFile)
#        reader.WorkingDirectory.setValue( os.getcwd() )
#
#        # Create a list of dataset infos . . .
#        datasetInfos = []
#
#        # npy inverted
#        info = DatasetInfo()
#        info.location = DatasetInfo.Location.FileSystem
#        info.filePath = self.testNpyFileName
#        info.internalPath = ""
#        info.invertColors = True
#        info.convertToGrayscale = False
#        datasetInfos.append(info)
#
#        # png inverted
#        info = DatasetInfo()
#        info.location = DatasetInfo.Location.FileSystem
#        info.filePath = self.testPngFileName
#        info.internalPath = ""
#        info.invertColors = True
#        info.convertToGrayscale = False
#        datasetInfos.append(info)
#
#        reader.Dataset.setValues(datasetInfos)
#
#        invertedNpyData = reader.ProcessedImages[0][...].wait()
#        invertedPngData = reader.ProcessedImages[1][...].wait()
#
#        # Check inverted images
#        assert invertedNpyData.shape == self.imgData2D.shape + (1,) # (Reader appends a channel dimension for this data)
#        for x in range(invertedNpyData.shape[0]):
#            for y in range(invertedNpyData.shape[1]):
#                assert invertedNpyData[x,y,0] == 255-self.imgData2D[x,y]
#
#        assert invertedPngData.shape == self.imgData2Dc.shape
#        for x in range(invertedPngData.shape[0]):
#            for y in range(invertedPngData.shape[1]):
#                for c in range(invertedPngData.shape[2]):
#                    assert invertedPngData[x,y,c] == 255-self.imgData2Dc[x,y,0]
#
#    def testGrayscaling(self):
#        graph = lazyflow.graph.Graph()
#        reader = OpDataSelection(graph=graph)
#        reader.ProjectFile.setValue(self.projectFile)
#        reader.WorkingDirectory.setValue( os.getcwd() )
#
#        # Create a list of dataset infos . . .
#        datasetInfos = []
#
#        # png grayscale
#        info = DatasetInfo()
#        info.location = DatasetInfo.Location.FileSystem
#        info.filePath = self.testPngFileName
#        info.internalPath = ""
#        info.invertColors = False
#        info.convertToGrayscale = True
#        datasetInfos.append(info)
#
#        reader.Dataset.setValues(datasetInfos)
#
#        grayscalePngData = reader.ProcessedImages[0][...].wait()
#
#        # Check grayscale conversion
#        assert grayscalePngData.shape == self.imgData2Dc.shape[:-1] + (1,) # Only one channel
#        for x in range(grayscalePngData.shape[0]):
#            for y in range(grayscalePngData.shape[1]):
#                # (See formula in OpRgbToGrayscale)
#                assert grayscalePngData[x,y,0] == int(numpy.round(  0.299*self.imgData2Dc[x,y,0]
#                                                                  + 0.587*self.imgData2Dc[x,y,1]
#                                                                  + 0.114*self.imgData2Dc[x,y,2] ))
#    def testInvertedGrayscaling(self):
#        graph = lazyflow.graph.Graph()
#        reader = OpDataSelection(graph=graph)
#        reader.ProjectFile.setValue(self.projectFile)
#        reader.WorkingDirectory.setValue( os.getcwd() )
#
#        # Create a list of dataset infos . . .
#        datasetInfos = []
#
#        # png grayscale & inverted
#        info = DatasetInfo()
#        info.location = DatasetInfo.Location.FileSystem
#        info.filePath = self.testPngFileName
#        info.internalPath = ""
#        info.invertColors = True
#        info.convertToGrayscale = True
#        datasetInfos.append(info)
#
#        reader.Dataset.setValues(datasetInfos)
#
#        invertedGrayscalePngData = reader.ProcessedImages[0][...].wait()
#
#
#        # Check inverted grayscale conversion
#        assert invertedGrayscalePngData.shape == (100, 200, 1)
#        for x in range(invertedGrayscalePngData.shape[0]):
#            for y in range(invertedGrayscalePngData.shape[1]):
#                # (See formula in OpRgbToGrayscale)
#                assert invertedGrayscalePngData[x,y,0] == int(numpy.round(  0.299*(255-self.imgData2Dc[x,y,0])
#                                                                          + 0.587*(255-self.imgData2Dc[x,y,1])
#                                                                          + 0.114*(255-self.imgData2Dc[x,y,2]) ))

    def testProjectLocalData(self):
        graph = lazyflow.graph.Graph()
        reader = OperatorWrapper(OpDataSelection, graph=graph, operator_kwargs={'forceAxisOrder': False})
        reader.ProjectFile.setValue(self.projectFile)
        reader.WorkingDirectory.setValue(os.getcwd())
        reader.ProjectDataGroup.setValue('DataSelection/local_data')

        # Create a list of dataset infos . . .
        datasetInfos = []

        # From project
        info = DatasetInfo()
        info.location = DatasetInfo.Location.ProjectInternal
        info.filePath = "This string should be ignored..."
        info._datasetId = 'dataset1'  # (Cheating a bit here...)
        info.invertColors = False
        info.convertToGrayscale = False
        datasetInfos.append(info)

        reader.Dataset.setValues(datasetInfos)

        projectInternalData = reader.Image[0][...].wait()

        assert projectInternalData.shape == self.imgData2Dc.shape, (projectInternalData.shape, self.imgData2Dc.shape)
        assert (projectInternalData == self.imgData2Dc).all()


class TestOpDataSelection_Basic_native_3D(object):
    """Test related to loading file types that support 3D"""
    @classmethod
    def setup_class(cls):
        cls.tmpdir = tempfile.mkdtemp()
        cls.imgFileNames3D = []
        cls.imgFileNames3Dc = []
        # Comparison of compressed data not possible - those types will be
        # skipped in raw comparison:
        cls.projectFileName = os.path.join(cls.tmpdir, 'testProject.ilp')

        # Create a couple test images of different types
        # in order to simplify and unify testing among the different file types
        # the extra dimension is added, as vigra would add one anyway.
        cls.imgData3D = numpy.random.randint(0, 255, (10, 11, 12, 1)).astype(numpy.uint8)
        # v- image data variables in order to reflect the correct axis-order
        # otherwise the axes get scrambled when writing/reloading
        vimgData3D = vigra.VigraArray(
            cls.imgData3D,
            axistags=vigra.defaultAxistags('zyxc'),
            dtype=numpy.uint8
        )

        testNpyFileName = os.path.join(cls.tmpdir, "testimage3D.npy")
        numpy.save(testNpyFileName, cls.imgData3D)
        cls.imgFileNames3D.append(testNpyFileName)

        testNpzFileName = os.path.join(cls.tmpdir, "testimage3D.npz")
        numpy.savez(testNpzFileName, data=cls.imgData3D)
        testNpzFileName = "{}/data".format(testNpzFileName)
        cls.imgFileNames3D.append(testNpzFileName)

        testH5FileName = os.path.join(cls.tmpdir, "testimage3D.h5")
        vigra.impex.writeHDF5(
            data=cls.imgData3D,
            filenameOrGroup=testH5FileName,
            pathInFile='test/data'
        )
        testH5FileName = "{}/test/data".format(testH5FileName)
        cls.imgFileNames3D.append(testH5FileName)

        cls.imgData3Dc = numpy.random.randint(0, 255, (10, 11, 12, 3)).astype(numpy.uint8)
        vimgData3Dc = vigra.VigraArray(
            cls.imgData3Dc,
            axistags=vigra.defaultAxistags('zyxc'),
            dtype=numpy.uint8
        )

        testNpyFileName = os.path.join(cls.tmpdir, "testimage3Dc.npy")
        numpy.save(testNpyFileName, cls.imgData3Dc)
        cls.imgFileNames3Dc.append(testNpyFileName)

        testNpzFileName = os.path.join(cls.tmpdir, "testimage3Dc.npz")
        numpy.savez(testNpzFileName, data=cls.imgData3Dc)
        testNpzFileName = "{}/data".format(testNpzFileName)
        cls.imgFileNames3Dc.append(testNpzFileName)

        testH5FileName = os.path.join(cls.tmpdir, "testimage3Dc.h5")
        vigra.impex.writeHDF5(
            data=cls.imgData3Dc,
            filenameOrGroup=testH5FileName,
            pathInFile='test/data'
        )
        testH5FileName = "{}/test/data".format(testH5FileName)
        cls.imgFileNames3Dc.append(testH5FileName)

        # Create a 'project' file and give it some data
        cls.projectFile = h5py.File(cls.projectFileName)
        cls.projectFile.create_group('DataSelection')
        cls.projectFile['DataSelection'].create_group('local_data')
        # Use the same data as the 3d+c data (above)
        cls.projectFile['DataSelection/local_data'].create_dataset('dataset1', data=cls.imgData3Dc)
        cls.projectFile.flush()

    @classmethod
    def teardown_class(cls):
        cls.projectFile.close()
        try:
            shutil.rmtree(cls.tmpdir)
        except OSError as e:
            print('Exception caught while deleting temporary files: {}'.format(e))

    def testBasic3D(self):
        """Test if plane 2d files are loaded correctly"""
        for fileName in self.imgFileNames3D:
            graph = lazyflow.graph.Graph()
            reader = OperatorWrapper(OpDataSelection, graph=graph, operator_kwargs={'forceAxisOrder': False})
            reader.ProjectFile.setValue(self.projectFile)
            reader.WorkingDirectory.setValue(os.getcwd())
            reader.ProjectDataGroup.setValue('DataSelection/local_data')

            info = DatasetInfo()
            # Will be read from the filesystem since the data won't be found in the project file.
            info.location = DatasetInfo.Location.ProjectInternal
            info.filePath = fileName
            info.internalPath = ""
            info.invertColors = False
            info.convertToGrayscale = False

            reader.Dataset.setValues([info])

            # Read the test files using the data selection operator and verify the contents
            imgData3D = reader.Image[0][...].wait()

            # Check the file name output
            assert reader.ImageName[0].value == fileName
            # Check raw images
            assert imgData3D.shape == self.imgData3D.shape, (imgData3D.shape, self.imgData3D.shape)
            # skip this if image was saved compressed:
            numpy.testing.assert_array_equal(imgData3D, self.imgData3D)

    def testBasic3DWrongAxes(self):
        """Test if 3D file with intentionally wrong axes is rejected """
        for fileName in self.imgFileNames3D:
            graph = lazyflow.graph.Graph()
            reader = OperatorWrapper(OpDataSelection, graph=graph, operator_kwargs={'forceAxisOrder': False})
            reader.ProjectFile.setValue(self.projectFile)
            reader.WorkingDirectory.setValue(os.getcwd())
            reader.ProjectDataGroup.setValue('DataSelection/local_data')

            info = DatasetInfo()
            # Will be read from the filesystem since the data won't be found in the project file.
            info.location = DatasetInfo.Location.ProjectInternal
            info.filePath = fileName
            info.internalPath = ""
            info.invertColors = False
            info.convertToGrayscale = False
            info.axistags = vigra.defaultAxistags('tzyc')

            try:
                reader.Dataset.setValues([info])
                assert False, "Should have thrown an exception!"
            except DatasetConstraintError:
                pass
            except:
                assert False, "Should have thrown a DatasetConstraintError!"

    def testBasic3Dc(self):
        """Test if 2d 3-channel files are loaded correctly"""
        # For some reason vigra saves 2D+c data compressed in gifs, so skip!
        for fileName in self.imgFileNames3Dc:
            graph = lazyflow.graph.Graph()
            reader = OperatorWrapper(OpDataSelection, graph=graph, operator_kwargs={'forceAxisOrder': False})
            reader.ProjectFile.setValue(self.projectFile)
            reader.WorkingDirectory.setValue(os.getcwd())
            reader.ProjectDataGroup.setValue('DataSelection/local_data')

            info = DatasetInfo()
            # Will be read from the filesystem since the data won't be found in the project file.
            info.location = DatasetInfo.Location.ProjectInternal
            info.filePath = fileName
            info.internalPath = ""
            info.invertColors = False
            info.convertToGrayscale = False

            reader.Dataset.setValues([info])

            # Read the test files using the data selection operator and verify the contents
            imgData3Dc = reader.Image[0][...].wait()

            # Check the file name output
            assert reader.ImageName[0].value == fileName
            # Check raw images
            assert imgData3Dc.shape == self.imgData3Dc.shape, (imgData3Dc.shape, self.imgData3Dc.shape)
            # skip this if image was saved compressed:
            numpy.testing.assert_array_equal(imgData3Dc, self.imgData3Dc)

    def testProjectLocalData(self):
        graph = lazyflow.graph.Graph()
        reader = OperatorWrapper(OpDataSelection, graph=graph, operator_kwargs={'forceAxisOrder': False})
        reader.ProjectFile.setValue(self.projectFile)
        reader.WorkingDirectory.setValue(os.getcwd())
        reader.ProjectDataGroup.setValue('DataSelection/local_data')

        # Create a list of dataset infos . . .
        datasetInfos = []

        # From project
        info = DatasetInfo()
        info.location = DatasetInfo.Location.ProjectInternal
        info.filePath = "This string should be ignored..."
        info._datasetId = 'dataset1'  # (Cheating a bit here...)
        info.invertColors = False
        info.convertToGrayscale = False
        datasetInfos.append(info)

        reader.Dataset.setValues(datasetInfos)

        projectInternalData = reader.Image[0][...].wait()

        assert projectInternalData.shape == self.imgData3Dc.shape, (projectInternalData.shape, self.imgData3Dc.shape)
        assert (projectInternalData == self.imgData3Dc).all()


class TestOpDataSelection_3DStacks(object):

    @classmethod
    def setup_class(cls):
        cls.tmpdir = tempfile.mkdtemp()
        cls.imgFileNameGlobs2D = []
        cls.imgFileNameGlobs2Dc = []

        cls.imgFileLists2D = defaultdict(list)

        cls.vigraExtensions = vigra.impex.listExtensions().split(' ')
        # Comparison of compressed data not possible - those types will be
        # skipped in raw comparison:
        cls.compressedExtensions = ['.jpg', '.jpeg']
        cls.projectFileName = os.path.join(cls.tmpdir, 'testProject.ilp')

        # Create a couple test images of different types
        # in order to simplify and unify testing among the different file types
        # the extra dimension is added, as vigra would add one anyway.
        # 2D Stacks ##
        cls.imgData3D = numpy.random.randint(0, 255, (9, 10, 11, 1)).astype(numpy.uint8)
        # v- image data variables in order to reflect the correct axis-order
        # otherwise the axes get scrambled when writing/reloading
        cls.removedExtensions = []
        for slice_index, slice2D in enumerate(cls.imgData3D):
            vimgData2D = vigra.VigraArray(
                slice2D,
                axistags=vigra.defaultAxistags('yxc'),
                dtype=numpy.uint8
            )

            testNpyFileName = os.path.join(
                cls.tmpdir, "testimage2D_{:02d}.npy".format(slice_index))
            numpy.save(testNpyFileName, slice2D)

            testNpzFileName = os.path.join(
                cls.tmpdir, "testimage2D_{:02d}.npz".format(slice_index))
            numpy.savez(testNpzFileName, data=slice2D)
            testNpzFileName = "{}/data".format(testNpzFileName)

            testH5FileName = os.path.join(cls.tmpdir, "testimage2D_{:02d}.h5".format(slice_index))
            vigra.impex.writeHDF5(
                data=slice2D,
                filenameOrGroup=testH5FileName,
                pathInFile='test/data'
            )

            cls.imgFileLists2D['h5'].append('{}/test/data'.format(testH5FileName))

            for extension in cls.vigraExtensions:
                if extension in cls.removedExtensions:
                    continue
                tmpFileName = os.path.join(
                    cls.tmpdir, "testImage2D_{:02d}.{}".format(slice_index, extension))
                # not all extensions support this kind of pixeltype
                try:
                    vigra.impex.writeImage(
                        vimgData2D,
                        tmpFileName,
                    )
                    cls.imgFileLists2D[extension].append(tmpFileName)
                except RuntimeError as e:
                    cls.removedExtensions.append(extension)
                    msg = str(e).replace('\n', '')
                    print(
                        "Couldn't write temp 2D image file using vigra with `{}` "
                        "extension : {}".format(extension, msg)
                    )
        for extension in cls.removedExtensions:
            cls.vigraExtensions.pop(cls.vigraExtensions.index(extension))

        for extension in cls.vigraExtensions:
            cls.imgFileNameGlobs2D.append(
                os.path.join(cls.tmpdir, "testImage2D_*.{}".format(extension)))
        cls.imgFileNameGlobs2D.extend([
            os.path.join(cls.tmpdir, "testimage2D_*.h5/test/data"),
            # uncomment once support is implemented
            # os.path.join(cls.tmpdir, "testimage2D_*.npz/data"),
            # os.path.join(cls.tmpdir, "testimage2D_*.npy"),
        ])

        # 2Dc Stacks ##
        cls.imgData3Dc = numpy.random.randint(0, 255, (9, 10, 11, 3)).astype(numpy.uint8)

        cls.removedExtensions = []
        for slice_index, slice2Dc in enumerate(cls.imgData3Dc):
            # v- image data variables in order to reflect the correct axis-order
            # otherwise the axes get scrambled when writing/reloading
            vimgData2Dc = vigra.VigraArray(
                slice2Dc,
                axistags=vigra.defaultAxistags('yxc'),
                dtype=numpy.uint8
            )

            testNpyFileName = os.path.join(
                cls.tmpdir, "testimage2Dc_{:02d}.npy".format(slice_index))
            numpy.save(testNpyFileName, slice2Dc)

            testNpzFileName = os.path.join(
                cls.tmpdir, "testimage2Dc_{:02d}.npz".format(slice_index))
            numpy.savez(testNpzFileName, data=slice2Dc)
            testNpzFileName = "{}/data".format(testNpzFileName)

            testH5FileName = os.path.join(cls.tmpdir, "testimage2Dc_{:02d}.h5".format(slice_index))
            vigra.impex.writeHDF5(
                data=slice2Dc,
                filenameOrGroup=testH5FileName,
                pathInFile='test/data'
            )

            for extension in cls.vigraExtensions:
                if extension in cls.removedExtensions:
                    continue
                tmpFileName = os.path.join(
                    cls.tmpdir, "testImage2Dc_{:02d}.{}".format(slice_index, extension))
                # not all extensions support this kind of pixeltype
                try:
                    vigra.impex.writeImage(
                        vimgData2Dc,
                        tmpFileName,
                    )
                except RuntimeError as e:
                    cls.removedExtensions.append(extension)
                    msg = str(e).replace('\n', '')
                    print(
                        "Couldn't write temp 2D image file using vigra with `{}` "
                        "extension : {}".format(extension, msg)
                    )
        for extension in cls.removedExtensions:
            cls.vigraExtensions.pop(cls.vigraExtensions.index(extension))

        for extension in cls.vigraExtensions:
            cls.imgFileNameGlobs2Dc.append(
                os.path.join(cls.tmpdir, "testImage2Dc_*.{}".format(extension)))

        cls.imgFileNameGlobs2Dc.extend([
            os.path.join(cls.tmpdir, "testimage2Dc_*.h5/test/data"),
            # uncomment once support is implemented
            # os.path.join(cls.tmpdir, "testimage2Dc_*.npz/data"),
            # os.path.join(cls.tmpdir, "testimage2Dc_*.npy"),
        ])

        # Create a 'project' file and give it some data
        cls.projectFile = h5py.File(cls.projectFileName)
        cls.projectFile.create_group('DataSelection')
        cls.projectFile['DataSelection'].create_group('local_data')
        # Use the same data as the 3d+c data (above)
        cls.projectFile['DataSelection/local_data'].create_dataset('dataset1', data=cls.imgData3D)
        cls.projectFile.flush()

    @classmethod
    def teardown_class(cls):
        cls.projectFile.close()
        try:
            shutil.rmtree(cls.tmpdir)
        except OSError as e:
            print('Exception caught while deleting temporary files: {}'.format(e))

    def testBasic3DstackFromGlobString(self):
        """Test if stacked 2d files are loaded correctly"""
        for fileName in self.imgFileNameGlobs2D:
            graph = lazyflow.graph.Graph()
            reader = OperatorWrapper(OpDataSelection, graph=graph, operator_kwargs={'forceAxisOrder': False})
            reader.ProjectFile.setValue(self.projectFile)
            reader.WorkingDirectory.setValue(os.getcwd())
            reader.ProjectDataGroup.setValue('DataSelection/local_data')

            info = DatasetInfo()
            # Will be read from the filesystem since the data won't be found in the project file.
            info.location = DatasetInfo.Location.ProjectInternal
            info.filePath = fileName
            info.internalPath = ""
            info.invertColors = False
            info.convertToGrayscale = False

            reader.Dataset.setValues([info])

            # Read the test files using the data selection operator and verify the contents
            imgData3D = reader.Image[0][...].wait()

            # Check the file name output
            assert reader.ImageName[0].value == fileName
            # Check raw images
            assert imgData3D.shape == self.imgData3D.shape, (imgData3D.shape, self.imgData3D.shape)
            # skip this if image was saved compressed:
            if any(x in fileName.lower() for x in self.compressedExtensions):
                print("Skipping raw comparison for compressed data: {}".format(fileName))
                continue
            numpy.testing.assert_array_equal(imgData3D, self.imgData3D)

    def testBasic3DstacksFromFileList(self):
        for ext, fileNames in list(self.imgFileLists2D.items()):
            fileNameString = os.path.pathsep.join(fileNames)
            graph = lazyflow.graph.Graph()
            reader = OperatorWrapper(OpDataSelection, graph=graph, operator_kwargs={'forceAxisOrder': False})
            reader.ProjectFile.setValue(self.projectFile)
            reader.WorkingDirectory.setValue(os.getcwd())
            reader.ProjectDataGroup.setValue('DataSelection/local_data')

            info = DatasetInfo(filepath=fileNameString)
            # Will be read from the filesystem since the data won't be found in the project file.
            info.location = DatasetInfo.Location.ProjectInternal
            info.internalPath = ""
            info.invertColors = False
            info.convertToGrayscale = False

            reader.Dataset.setValues([info])

            # Read the test files using the data selection operator and verify the contents
            imgData3D = reader.Image[0][...].wait()

            # Check raw images
            assert imgData3D.shape == self.imgData3D.shape, (imgData3D.shape, self.imgData3D.shape)
            # skip this if image was saved compressed:
            if any(x.strip('.') in ext.lower() for x in self.compressedExtensions):
                print("Skipping raw comparison for compressed data: {}".format(ext))
                continue
            numpy.testing.assert_array_equal(imgData3D, self.imgData3D)

    def testBasic3DcStackFromGlobString(self):
        """Test if stacked 2d 3-channel files are loaded correctly"""
        # For some reason vigra saves 2D+c data compressed in gifs, so skip!
        self.compressedExtensions.append('.gif')
        for fileName in self.imgFileNameGlobs2Dc:
            graph = lazyflow.graph.Graph()
            reader = OperatorWrapper(OpDataSelection, graph=graph, operator_kwargs={'forceAxisOrder': False})
            reader.ProjectFile.setValue(self.projectFile)
            reader.WorkingDirectory.setValue(os.getcwd())
            reader.ProjectDataGroup.setValue('DataSelection/local_data')

            info = DatasetInfo()
            # Will be read from the filesystem since the data won't be found in the project file.
            info.location = DatasetInfo.Location.ProjectInternal
            info.filePath = fileName
            info.internalPath = ""
            info.invertColors = False
            info.convertToGrayscale = False

            reader.Dataset.setValues([info])

            # Read the test files using the data selection operator and verify the contents
            imgData3Dc = reader.Image[0][...].wait()

            # Check the file name output
            assert reader.ImageName[0].value == fileName
            # Check raw images
            assert imgData3Dc.shape == self.imgData3Dc.shape, (imgData3Dc.shape, self.imgData3Dc.shape)
            # skip this if image was saved compressed:
            if any(x in fileName.lower() for x in self.compressedExtensions):
                print("Skipping raw comparison for compressed data: {}".format(fileName))
                continue
            numpy.testing.assert_array_equal(imgData3Dc, self.imgData3Dc)


class TestOpDataSelection_SingleFileH5Stacks():
    @classmethod
    def setup_class(cls):
        cls.tmpdir = tempfile.mkdtemp()
        cls.projectFileName = os.path.join(cls.tmpdir, 'testProject.ilp')
        # generate some test data 'tczyx'
        cls.imgData3Dct = numpy.random.randint(0, 256, (10, 3, 8, 7, 6)).astype(numpy.uint8)

        # write a h5-file to directory
        cls.image_file_name = os.path.join(cls.tmpdir, 'multi-h5.h5')

        h5file = h5py.File(cls.image_file_name)
        cls.file_names = []
        try:
            g1 = h5file.create_group('g1')
            for t_index, t_slice in enumerate(cls.imgData3Dct):
                file_name = 'timeslice_{:03d}'.format(t_index)
                g1.create_dataset(file_name, data=t_slice)
                cls.file_names.append("{}/g1/{}".format(cls.image_file_name, file_name))
        finally:
            h5file.close()

        cls.glob_string = '{}/g1/timeslice_*'.format(cls.image_file_name)
        # Create a 'project' file and give it some data
        cls.projectFile = h5py.File(cls.projectFileName)
        cls.projectFile.create_group('DataSelection')
        cls.projectFile['DataSelection'].create_group('local_data')
        # Use the same data as the 3d+c data (above)
        cls.projectFile['DataSelection/local_data'].create_dataset(
            'dataset1', data=cls.imgData3Dct)
        cls.projectFile.flush()

    @classmethod
    def teardown_class(cls):
        cls.projectFile.close()
        try:
            shutil.rmtree(cls.tmpdir)
        except OSError as e:
            print('Exception caught while deleting temporary files: {}'.format(e))

    def test_load_single_file_with_glob(self):
        graph = lazyflow.graph.Graph()
        reader = OperatorWrapper(OpDataSelection, graph=graph, operator_kwargs={'forceAxisOrder': False})
        reader.ProjectFile.setValue(self.projectFile)
        reader.WorkingDirectory.setValue(os.getcwd())
        reader.ProjectDataGroup.setValue('DataSelection/local_data')

        info = DatasetInfo(filepath=self.glob_string)
        # Will be read from the filesystem since the data won't be found in the project file.
        info.location = DatasetInfo.Location.ProjectInternal
        info.internalPath = ""
        info.invertColors = False
        info.convertToGrayscale = False

        reader.Dataset.setValues([info])

        # Read the test files using the data selection operator and verify the contents
        imgData = reader.Image[0][...].wait()

        # Check raw images
        assert imgData.shape == self.imgData3Dct.shape, (imgData.shape, self.imgData3Dct.shape)

        numpy.testing.assert_array_equal(imgData, self.imgData3Dct)

    def test_load_single_file_with_list(self):
        graph = lazyflow.graph.Graph()
        reader = OperatorWrapper(OpDataSelection, graph=graph, operator_kwargs={'forceAxisOrder': False})
        reader.ProjectFile.setValue(self.projectFile)
        reader.WorkingDirectory.setValue(os.getcwd())
        reader.ProjectDataGroup.setValue('DataSelection/local_data')

        fileNameString = os.path.pathsep.join(self.file_names)
        info = DatasetInfo(filepath=fileNameString)
        # Will be read from the filesystem since the data won't be found in the project file.
        info.location = DatasetInfo.Location.ProjectInternal
        info.internalPath = ""
        info.invertColors = False
        info.convertToGrayscale = False

        reader.Dataset.setValues([info])

        # Read the test files using the data selection operator and verify the contents
        imgData = reader.Image[0][...].wait()
        print('imgData', reader.Image.meta.axistags, reader.Image.meta.original_axistags)

        # Check raw images
        assert imgData.shape == self.imgData3Dct.shape, (imgData.shape, self.imgData3Dct.shape)

        numpy.testing.assert_array_equal(imgData, self.imgData3Dct)


class TestOpDataSelection_FakeDataReader():
    """
    Test whether OpDataSelection uses the real or fake dataset reader depending
    on the DatasetInfo.realDataSource attribute
    """
    @classmethod
    def setup_class(cls):
        cls.tmpdir = tempfile.mkdtemp()
        cls.projectFileName = os.path.join(cls.tmpdir, 'testProject.ilp')
        # generate some test data 'tczyx'
        cls.imgData = numpy.random.randint(0, 256, (5, 3, 10, 10, 10)).astype(numpy.uint8)

        # save as raw data file
        cls.testRawDataFileName = os.path.join(cls.tmpdir, "testRawData.npy")
        numpy.save(cls.testRawDataFileName, cls.imgData)

        # Create a 'project' file and give it some data
        cls.projectFile = h5py.File(cls.projectFileName)
        cls.projectFile.create_group('DataSelection')
        cls.projectFile['DataSelection'].create_group('local_data')
        # Use the same data as the 2d+c data (above)
        cls.projectFile['DataSelection/local_data'].create_dataset('dataset1', data=cls.imgData)
        cls.projectFile.flush()

    @classmethod
    def teardown_class(cls):
        cls.projectFile.close()
        try:
            shutil.rmtree(cls.tmpdir)
        except OSError as e:
            print('Exception caught while deleting temporary files: {}'.format(e))

    def test_real_data_source(self):
        graph = lazyflow.graph.Graph()
        reader = OperatorWrapper(OpDataSelection, graph=graph,
                                 operator_kwargs={'forceAxisOrder': False})
        reader.ProjectFile.setValue(self.projectFile)
        reader.WorkingDirectory.setValue(os.getcwd())
        reader.ProjectDataGroup.setValue('DataSelection/local_data')

        info = DatasetInfo()
        # Will be read from the filesystem since the data won't be found in the project file.
        info.location = DatasetInfo.Location.ProjectInternal
        info.filePath = self.testRawDataFileName
        info.internalPath = ""
        info.invertColors = False
        info.convertToGrayscale = False
        #Use real data source
        info.realDataSource = True

        reader.Dataset.setValues([info])

        # Read the test file using the data selection operator and verify the contents
        imgData = reader.Image[0][...].wait()

        assert imgData.shape == self.imgData.shape
        numpy.testing.assert_array_equal(imgData, self.imgData)

    def test_fake_data_source(self):
        graph = lazyflow.graph.Graph()
        reader = OperatorWrapper(OpDataSelection, graph=graph,
                                 operator_kwargs={'forceAxisOrder': False})
        reader.ProjectFile.setValue(self.projectFile)
        reader.WorkingDirectory.setValue(os.getcwd())
        reader.ProjectDataGroup.setValue('DataSelection/local_data')

        info = DatasetInfo()
        # Will be read from the filesystem since the data won't be found in the project file.
        info.location = DatasetInfo.Location.ProjectInternal
        info.filePath = self.testRawDataFileName
        info.internalPath = ""
        info.invertColors = False
        info.convertToGrayscale = False
        # Use *fake* data source
        info.realDataSource = False
        info.axistags = vigra.defaultAxistags('tczyx')
        info.laneShape = self.imgData.shape
        info.laneDtype = self.imgData.dtype

        reader.Dataset.setValues([info])

        # Verify that now data selection operator returns fake data
        # with expected shape and type
        imgData = reader.Image[0][...].wait()

        assert imgData.shape == self.imgData.shape
        assert imgData.dtype == self.imgData.dtype
        expected_fake_data = numpy.zeros(info.laneShape, dtype=info.laneDtype)
        numpy.testing.assert_array_equal(imgData, expected_fake_data)


class TestOpDataSelection_stack_along_parameter:

    @classmethod
    def setup_class(cls):
        cls.tmpdir = tempfile.mkdtemp()

        cls.rgb00c = numpy.array([[1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                                  [1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                                  [1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                                  [1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                                  [1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]], dtype=numpy.float32)

        cls.rgb10c = numpy.array([[0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0],
                                  [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                                  [0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0],
                                  [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
                                  [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0]], dtype=numpy.float32)

        cls.rgb20c = numpy.array([[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0],
                                  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1],
                                  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1],
                                  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1],
                                  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0]], dtype=numpy.float32)

        cls.grey0c = numpy.array([[1, 1, 1, 1, 0, 1, 1, 1, 0, 0, 1, 1, 1, 0, 1, 0, 1],
                                  [1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1],
                                  [1, 0, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 0, 0, 0, 1, 0],
                                  [1, 0, 0, 1, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0],
                                  [1, 1, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 1, 0, 0, 1, 0]], dtype=numpy.float32) / 2

        cls.rgb01c = cls.rgb00c[..., None]
        cls.rgb11c = cls.rgb10c[..., None]
        cls.rgb21c = cls.rgb20c[..., None]
        cls.grey1c = cls.grey0c[..., None]

        cls.rgb03c = numpy.zeros((cls.rgb00c.shape[0], cls.rgb00c.shape[1], 3), dtype=numpy.float32)
        cls.rgb13c = numpy.zeros((cls.rgb10c.shape[0], cls.rgb10c.shape[1], 3), dtype=numpy.float32)
        cls.rgb23c = numpy.zeros((cls.rgb20c.shape[0], cls.rgb20c.shape[1], 3), dtype=numpy.float32)
        cls.rgb03c[..., 0] = cls.rgb00c
        cls.rgb13c[..., 1] = cls.rgb10c
        cls.rgb23c[..., 2] = cls.rgb20c
        cls.grey3c = numpy.repeat(cls.grey1c, 3, axis=2)

        for name, c in itertools.product(['rgb0', 'rgb1', 'rgb2', 'grey'], ['0c', '1c', '3c']):
            name += c
            data = eval('cls.' + name)

            # save as h5
            vigra.impex.writeHDF5(data=data, filenameOrGroup=os.path.join(cls.tmpdir, f'{name}.h5'), pathInFile='data')

            # save as png and tiff, if possible
            if c == '0c':
                im = Image.fromarray(data)
                im.save(os.path.join(cls.tmpdir, f'{name}.tiff'))
                vigra.impex.writeImage(image=(data.T * 255).astype(numpy.uint8),
                                       filename=os.path.join(cls.tmpdir, f'{name}.png'))
            elif c == '1c':
                vigra.impex.writeImage(image=(data.transpose(1, 0, 2) * 255).astype(numpy.uint8),
                                       filename=os.path.join(cls.tmpdir, f'{name}.png'))
            elif c == '3c':
                data = (data * 255).astype(numpy.uint8)
                im = Image.fromarray(data, mode='RGB')
                im.save(os.path.join(cls.tmpdir, f'{name}.tiff'))
                vigra.impex.writeImage(image=data.transpose(1, 0, 2),
                                       filename=os.path.join(cls.tmpdir, f'{name}.png'))
            else:
                raise NotImplementedError(f'How to create PIL/png image with c == {c}?')

    def _test_stack_along(self, name, extension, sequence_axis, expected):
        fileName = os.path.join(self.tmpdir, f'{name}{extension}')
        graph = lazyflow.graph.Graph()
        reader = OpDataSelection(graph=graph, forceAxisOrder=False)
        reader.WorkingDirectory.setValue(os.getcwd())
        info = DatasetInfo(fileName, sequence_axis=sequence_axis)
        reader.Dataset.setValue(info)
        read = reader.Image[...].wait()

        assert numpy.allclose(read, expected), f'{name}: {read.shape}, {expected.shape}'

    def test_stack_along(self):

        testcases = [
            ['rgb*0c', '.h5/data', 'c', numpy.stack([self.rgb00c, self.rgb10c, self.rgb20c], axis=0)],
            ['rgb*0c', '.png    ', 'c', numpy.stack([self.rgb00c, self.rgb10c, self.rgb20c], axis=2).transpose(1, 0, 2
                                                                                                               ) * 255],
            ['rgb*0c', '.tiff   ', 'c', numpy.stack([self.rgb00c, self.rgb10c, self.rgb20c], axis=0)],
            ['rgb*1c', '.h5/data', 'c', numpy.stack([self.rgb00c, self.rgb10c, self.rgb20c], axis=2)],
            ['rgb*1c', '.png    ', 'c', numpy.stack([self.rgb00c, self.rgb10c, self.rgb20c], axis=2).transpose(1, 0, 2
                                                                                                               ) * 255],
            ['rgb*3c', '.h5/data', 'c', numpy.concatenate([self.rgb03c, self.rgb13c, self.rgb23c], axis=2)],
            ['rgb*3c', '.png    ', 'c', numpy.concatenate([self.rgb03c, self.rgb13c, self.rgb23c], axis=2).transpose(
                1, 0, 2) * 255],
            ['rgb*3c', '.tiff   ', 'c', numpy.concatenate([self.rgb03c, self.rgb13c, self.rgb23c], axis=2) * 255],
            ['rgb*0c', '.h5/data', 'z', numpy.stack([self.rgb00c, self.rgb10c, self.rgb20c], axis=0)[..., None]],
            ['rgb*0c', '.png    ', 'z', numpy.stack([self.rgb00c, self.rgb10c, self.rgb20c], axis=0)[..., None] * 255],
            ['rgb*0c', '.tiff   ', 'z', numpy.stack([self.rgb00c, self.rgb10c, self.rgb20c], axis=0)[..., None]],
            ['rgb*1c', '.h5/data', 'z', numpy.stack([self.rgb00c, self.rgb10c, self.rgb20c], axis=0)[..., None]],
            ['rgb*1c', '.png    ', 'z', numpy.stack([self.rgb00c, self.rgb10c, self.rgb20c], axis=0)[..., None] * 255],
            ['rgb*3c', '.h5/data', 'z', numpy.stack([self.rgb03c, self.rgb13c, self.rgb23c], axis=0)],
            ['rgb*3c', '.png    ', 'z', numpy.stack([self.rgb03c, self.rgb13c, self.rgb23c], axis=0) * 255],
            ['rgb*3c', '.tiff   ', 'z', numpy.stack([self.rgb03c, self.rgb13c, self.rgb23c], axis=0) * 255],
            ['rgb*0c', '.h5/data', 't', numpy.stack([self.rgb00c, self.rgb10c, self.rgb20c], axis=0)[..., None]],
            ['rgb*0c', '.png    ', 't', numpy.stack([self.rgb00c, self.rgb10c, self.rgb20c], axis=0)[..., None] * 255],
            ['rgb*0c', '.tiff   ', 't', numpy.stack([self.rgb00c, self.rgb10c, self.rgb20c], axis=0)[..., None]],
            ['rgb*1c', '.h5/data', 't', numpy.stack([self.rgb00c, self.rgb10c, self.rgb20c], axis=0)[..., None]],
            ['rgb*1c', '.png    ', 't', numpy.stack([self.rgb00c, self.rgb10c, self.rgb20c], axis=0)[..., None] * 255],
            ['rgb*3c', '.h5/data', 't', numpy.stack([self.rgb03c, self.rgb13c, self.rgb23c], axis=0)],
            ['rgb*3c', '.png    ', 't', numpy.stack([self.rgb03c, self.rgb13c, self.rgb23c], axis=0) * 255],
            ['rgb*3c', '.tiff   ', 't', numpy.stack([self.rgb03c, self.rgb13c, self.rgb23c], axis=0) * 255],
        ]

        for name, extension, sequence_axis, expected in testcases:
            yield self._test_stack_along, name, extension, sequence_axis, expected
