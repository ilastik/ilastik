import os
import numpy
import vigra
import lazyflow
import h5py
from lazyflow.graph import Graph
from applets.dataSelection.opDataSelection import OpDataSelection

class TestOpDataSelection_Basic():
    
    @classmethod
    def setupClass(cls):
        cls.testNpyFileName = 'testImage1.npy'
        cls.testPngFileName = 'testImage2.png'
        cls.projectFileName = 'testProject.ilp'

        # Create a couple test images of different types
        cls.npyData = numpy.zeros((10, 11))
        for x in range(0,10):
            for y in range(0,11):
                cls.npyData[x,y] = x+y
        numpy.save(cls.testNpyFileName, cls.npyData)
        
        cls.pngData = numpy.zeros((100,200,3))
        for x in range(cls.pngData.shape[0]):
            for y in range(cls.pngData.shape[1]):
                for c in range(cls.pngData.shape[2]):
                    cls.pngData[x,y,c] = (x+y) % 256
        vigra.impex.writeImage(cls.pngData, cls.testPngFileName)

        # Create a 'project' file and give it some data
        cls.projectFile = h5py.File(cls.projectFileName)
        cls.projectFile.create_group('DataSelection')
        cls.projectFile['DataSelection'].create_group('local_data')
        # Use the same data as the png data (above)
        cls.projectFile['DataSelection/local_data'].create_dataset('dataset1', data=cls.pngData)
        cls.projectFile.flush()
    
    @classmethod
    def teardownClass(cls):
        os.remove(cls.testNpyFileName)
        os.remove(cls.testPngFileName)
        os.remove(cls.projectFileName)
    
    def testBasic(self):
        graph = lazyflow.graph.Graph()
        reader = OpDataSelection(graph=graph)
        reader.ProjectFile.setValue(self.projectFile)
        reader.WorkingDirectory.setValue( os.path.split(__file__)[0] )
        
        # Create a list of dataset infos . . .
        datasetInfos = []
        
        # npy
        info = OpDataSelection.DatasetInfo()
        # Will be read from the filesystem since the data won't be found in the project file.
        info.location = OpDataSelection.DatasetInfo.Location.ProjectInternal
        info.filePath = self.testNpyFileName
        info.internalPath = ""
        info.invertColors = False
        info.convertToGrayscale = False
        datasetInfos.append(info)
        
        # png
        info = OpDataSelection.DatasetInfo()
        info.location = OpDataSelection.DatasetInfo.Location.FileSystem
        info.filePath = self.testPngFileName
        info.internalPath = ""
        info.invertColors = False
        info.convertToGrayscale = False
        datasetInfos.append(info)

        reader.DatasetInfos.setValues(datasetInfos)

        # Read the test files using the data selection operator and verify the contents
        npyData = reader.ProcessedImages[0][...].wait()
        pngData = reader.ProcessedImages[1][...].wait()

        # Check the file name output
        assert reader.ImageNames[0].value == self.testNpyFileName
        assert reader.ImageNames[1].value == self.testPngFileName

        # Check raw images
        assert npyData.shape == (10,11,1)
        for x in range(npyData.shape[0]):
            for y in range(npyData.shape[1]):
                assert npyData[x,y,0] == x+y
        
        assert pngData.shape == (100, 200, 3)
        for x in range(pngData.shape[0]):
            for y in range(pngData.shape[1]):
                for c in range(pngData.shape[2]):
                    assert pngData[x,y,c] == (x+y) % 256
        

    def testColorInversion(self):
        graph = lazyflow.graph.Graph()
        reader = OpDataSelection(graph=graph)
        reader.ProjectFile.setValue(self.projectFile)
        reader.WorkingDirectory.setValue( os.path.split(__file__)[0] )
        
        # Create a list of dataset infos . . .
        datasetInfos = []
        
        # npy inverted
        info = OpDataSelection.DatasetInfo()
        info.location = OpDataSelection.DatasetInfo.Location.FileSystem
        info.filePath = self.testNpyFileName
        info.internalPath = ""
        info.invertColors = True
        info.convertToGrayscale = False
        datasetInfos.append(info)
        
        # png inverted
        info = OpDataSelection.DatasetInfo()
        info.location = OpDataSelection.DatasetInfo.Location.FileSystem
        info.filePath = self.testPngFileName
        info.internalPath = ""
        info.invertColors = True
        info.convertToGrayscale = False
        datasetInfos.append(info)

        reader.DatasetInfos.setValues(datasetInfos)

        invertedNpyData = reader.ProcessedImages[0][...].wait()
        invertedPngData = reader.ProcessedImages[1][...].wait()

        # Check inverted images
        assert invertedNpyData.shape == self.npyData.shape + (1,) # (Reader appends a channel dimension for this data)
        for x in range(invertedNpyData.shape[0]):
            for y in range(invertedNpyData.shape[1]):
                assert invertedNpyData[x,y,0] == 255-self.npyData[x,y]
        
        assert invertedPngData.shape == self.pngData.shape
        for x in range(invertedPngData.shape[0]):
            for y in range(invertedPngData.shape[1]):
                for c in range(invertedPngData.shape[2]):
                    assert invertedPngData[x,y,c] == 255-self.pngData[x,y,0]        

    def testGrayscaling(self):
        graph = lazyflow.graph.Graph()
        reader = OpDataSelection(graph=graph)
        reader.ProjectFile.setValue(self.projectFile)
        reader.WorkingDirectory.setValue( os.path.split(__file__)[0] )
        
        # Create a list of dataset infos . . .
        datasetInfos = []
        
        # png grayscale
        info = OpDataSelection.DatasetInfo()
        info.location = OpDataSelection.DatasetInfo.Location.FileSystem
        info.filePath = self.testPngFileName
        info.internalPath = ""
        info.invertColors = False
        info.convertToGrayscale = True
        datasetInfos.append(info)

        reader.DatasetInfos.setValues(datasetInfos)
        
        grayscalePngData = reader.ProcessedImages[0][...].wait()

        # Check grayscale conversion 
        assert grayscalePngData.shape == self.pngData.shape[:-1] + (1,) # Only one channel
        for x in range(grayscalePngData.shape[0]):
            for y in range(grayscalePngData.shape[1]):
                # (See formula in OpRgbToGrayscale)
                assert grayscalePngData[x,y,0] == int(numpy.round(  0.299*self.pngData[x,y,0]
                                                                  + 0.587*self.pngData[x,y,1] 
                                                                  + 0.114*self.pngData[x,y,2] ))
    def testInvertedGrayscaling(self):
        graph = lazyflow.graph.Graph()
        reader = OpDataSelection(graph=graph)
        reader.ProjectFile.setValue(self.projectFile)
        reader.WorkingDirectory.setValue( os.path.split(__file__)[0] )
        
        # Create a list of dataset infos . . .
        datasetInfos = []

        # png grayscale & inverted
        info = OpDataSelection.DatasetInfo()
        info.location = OpDataSelection.DatasetInfo.Location.FileSystem
        info.filePath = self.testPngFileName
        info.internalPath = ""
        info.invertColors = True
        info.convertToGrayscale = True
        datasetInfos.append(info)

        reader.DatasetInfos.setValues(datasetInfos)
        
        invertedGrayscalePngData = reader.ProcessedImages[0][...].wait()
        

        # Check inverted grayscale conversion 
        assert invertedGrayscalePngData.shape == (100, 200, 1)
        for x in range(invertedGrayscalePngData.shape[0]):
            for y in range(invertedGrayscalePngData.shape[1]):
                # (See formula in OpRgbToGrayscale)
                assert invertedGrayscalePngData[x,y,0] == int(numpy.round(  0.299*(255-self.pngData[x,y,0])
                                                                          + 0.587*(255-self.pngData[x,y,1]) 
                                                                          + 0.114*(255-self.pngData[x,y,2]) ))
    def testProjectLocalData(self):
        graph = lazyflow.graph.Graph()
        reader = OpDataSelection(graph=graph)
        reader.ProjectFile.setValue(self.projectFile)
        reader.WorkingDirectory.setValue( os.path.split(__file__)[0] )
        
        # Create a list of dataset infos . . .
        datasetInfos = []

        # From project
        info = OpDataSelection.DatasetInfo()
        info.location = OpDataSelection.DatasetInfo.Location.ProjectInternal
        info.filePath = "This string should be ignored..."
        info._datasetId = 'dataset1' # (Cheating a bit here...)
        info.invertColors = False
        info.convertToGrayscale = False
        datasetInfos.append(info)

        reader.DatasetInfos.setValues(datasetInfos)

        projectInternalData = reader.ProcessedImages[0][...].wait()
        
        assert projectInternalData.shape == self.pngData.shape
        assert (projectInternalData == self.pngData).all()

if __name__ == "__main__":
    import nose
    nose.run(defaultTest=__file__, env={'NOSE_NOCAPTURE' : 1})
































