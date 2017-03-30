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
#		   http://ilastik.org/license.html
###############################################################################
import os
import shutil
import numpy
import vigra
import lazyflow
import h5py
from lazyflow.graph import OperatorWrapper
from ilastik.applets.dataSelection.opDataSelection import OpDataSelection, DatasetInfo

import tempfile


class TestOpDataSelection_Basic2D():

    @classmethod
    def setupClass(cls):
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

        for extension in vigra.impex.listExtensions().split(' '):
            tmpFileName = os.path.join(cls.tmpdir, "testImage2D.{}".format(extension))
            # not all extensions support this kind of pixeltype
            try:
                vigra.impex.writeImage(
                    vimgData2D,
                    tmpFileName,
                )
                cls.imgFileNames2D.append(tmpFileName)
            except RuntimeError, e:
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

        for extension in vigra.impex.listExtensions().split(' '):
            tmpFileName = os.path.join(cls.tmpdir, "testImage2Dc.{}".format(extension))
            # not all extensions support this kind of pixeltype
            try:
                vigra.impex.writeImage(
                    vimgData2Dc,
                    tmpFileName,
                )
                cls.imgFileNames2Dc.append(tmpFileName)
            except RuntimeError, e:
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
    def teardownClass(cls):
        cls.projectFile.close()
        try:
            shutil.rmtree(cls.tmpdir)
        except OSError, e:
            print('Exception caught while deleting temporary files: {}'.format(e))

    def testBasic2D(self):
        """Test if plane 2d files are loaded correctly"""
        for fileName in self.imgFileNames2D:
            graph = lazyflow.graph.Graph()
            reader = OperatorWrapper(OpDataSelection, graph=graph)
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
            reader = OperatorWrapper(OpDataSelection, graph=graph)
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
            assert imgData2Dc.shape == self.imgData2Dc.shape
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
        reader = OperatorWrapper( OpDataSelection, graph=graph )
        reader.ProjectFile.setValue(self.projectFile)
        reader.WorkingDirectory.setValue( os.getcwd() )
        reader.ProjectDataGroup.setValue( 'DataSelection/local_data' )
        
        # Create a list of dataset infos . . .
        datasetInfos = []

        # From project
        info = DatasetInfo()
        info.location = DatasetInfo.Location.ProjectInternal
        info.filePath = "This string should be ignored..."
        info._datasetId = 'dataset1' # (Cheating a bit here...)
        info.invertColors = False
        info.convertToGrayscale = False
        datasetInfos.append(info)

        reader.Dataset.setValues(datasetInfos)

        projectInternalData = reader.Image[0][...].wait()

        assert projectInternalData.shape == self.imgData2Dc.shape
        assert (projectInternalData == self.imgData2Dc).all()


if __name__ == "__main__":
    import nose
    nose.run(defaultTest=__file__, env={'NOSE_NOCAPTURE': 1})
































