from lazyflow.graph import Graph, Operator, InputSlot, OutputSlot, MultiInputSlot, MultiOutputSlot

from opProjectDatasetReader import OpProjectDatasetReader
from opInputDataReader import OpInputDataReader
from lazyflow.operators.obsolete.vigraOperators import OpGrayscaleInverter, OpRgbToGrayscale
import copy

import uuid

class OpDataSelection(Operator):
    """
    The top-level operator for the data selection applet.
    """
    name = "OpDataSelection"
    category = "Top-level"
    
    class DatasetInfo(object):
        """
        Struct-like class for describing dataset info.
        """
        class Location():
            FileSystem = 0
            ProjectInternal = 1

        def __init__(self):
            self.location = OpDataSelection.DatasetInfo.Location.FileSystem # Whether the data will be found/stored on the filesystem or in the project file
            self.invertColors = False          # Flag to invert colors before outputting
            self.convertToGrayscale = False    # Flag to convert to grayscale before outputting
            self._filePath = ""                # The original path to the data (also used as a fallback if the data isn't in the project yet)
            self._datasetId = ""               # The name of the data within the project file (if it is stored locally)            

        @property
        def filePath(self):
            return self._filePath
        
        @filePath.setter
        def filePath(self, newPath):
            self._filePath = newPath
            # Reset our id any time the filepath changes
            self._datasetId = str(uuid.uuid1())
        
        @property
        def datasetId(self):
            return self._datasetId
            

    # The project hdf5 File object (already opened)
    # Optional, but MUST be connected first if its connected
    ProjectFile = InputSlot(stype='object', optional=True)

    # Array of DatasetInfo objects (see above)
    DatasetInfos = MultiInputSlot(stype='object')

    # Output data
    OutputImages = MultiOutputSlot()
    
    def __init__(self, graph):
        super(OpDataSelection, self).__init__(graph=graph)

        # Create an internal operator for reading data from disk
        self.readers = []
        self.providerSlots = []
    
    def setupOutputs(self):
        numInputs = len(self.DatasetInfos)
        # Ensure the proper number of outputs
        self.OutputImages.resize(numInputs)

        # Rebuild the list of provider slots from scratch
        self.providerSlots = []

        for i in range(numInputs):
            datasetInfo = self.DatasetInfos[i].value

            # TODO: This shouldn't be hard-coded here.
            internalPath = 'DataSelection/local_data/' + datasetInfo.datasetId

            # Data only comes from the project file if the user said so AND it exists in the project
            datasetInProject = (datasetInfo.location == OpDataSelection.DatasetInfo.Location.ProjectInternal)
            datasetInProject &= self.ProjectFile.connected() and \
                                internalPath in self.ProjectFile.value
            
            # If we should find the data in the project file, use a dataset reader
            if datasetInProject:
                reader = OpProjectDatasetReader(graph=self.graph)
                reader.ProjectFile.setValue(self.ProjectFile.value)
                reader.InternalPath.setValue(internalPath)
                providerSlot = reader.OutputImage
            else:
                # Use a normal (filesystem) reader
                reader = OpInputDataReader(graph=self.graph)
                reader.FilePath.setValue(datasetInfo.filePath)
                providerSlot = reader.Output            

            # If the user wants to invert the image,
            #  insert an intermediate inversion operator on this subslot
            if datasetInfo.invertColors:
                inverter = OpGrayscaleInverter(graph=self.graph)
                inverter.input.connect(providerSlot)
                providerSlot = inverter.output
            
            # If the user wants to convert to grayscale,
            #  insert an intermediate rgb-to-grayscale operator on this subslot
            if datasetInfo.convertToGrayscale:
                converter = OpRgbToGrayscale(graph=self.graph)
                converter.input.connect(providerSlot)
                providerSlot = converter.output
            
            # Store the operator that is providing the output for this subslot
            self.providerSlots.append(providerSlot)

            # Copy the metadata from the provider we ended up with
            self.OutputImages[i].meta.dtype = providerSlot.meta.dtype
            self.OutputImages[i].meta.shape = providerSlot.meta.shape
            self.OutputImages[i].meta.axistags = copy.copy(providerSlot.meta.axistags)

    def getSubOutSlot(self, slots, indexes, key, result):
        # Request the output from the appropriate internal operator output.
        request = self.providerSlots[indexes[0]][key].writeInto(result)
        return request.wait()

# TODO: Put this in a unit test
if __name__ == "__main__":
    import os
    import numpy
    import vigra
    import lazyflow
    import h5py

    testNpyFileName = 'testImage1.npy'
    testPngFileName = 'testImage2.png'
    projectFileName = 'testProject.ilp'

    # Clean up: Delete any lingering test files from the previous run.
    for f in [testNpyFileName, testPngFileName, projectFileName]:
        try:
            os.remove(f)
        except:
            pass

    # Create a couple test images of different types
    # TODO: Use a temporary directory for this instead of the cwd.
    a = numpy.zeros((10, 11))
    for x in range(0,10):
        for y in range(0,11):
            a[x,y] = x+y
    numpy.save(testNpyFileName, a)
    
    a = numpy.zeros((100,200,3))
    for x in range(a.shape[0]):
        for y in range(a.shape[1]):
            for c in range(a.shape[2]):
                a[x,y,c] = (x+y) % 256
    vigra.impex.writeImage(a, testPngFileName)
    
    # Now read back our test data using an operator
    graph = lazyflow.graph.Graph()
    reader = OpDataSelection(graph=graph)

    # Create a 'project' file and give it some data
    projectFile = h5py.File(projectFileName)
    projectFile.create_group('DataSelection')
    projectFile['DataSelection'].create_group('local_data')
    projectFile['DataSelection/local_data'].create_dataset('dataset1', data=a) # Use the same data as the png data (above)
    projectFile.flush()
    reader.ProjectFile.setValue(projectFile)

    # Create a list of dataset infos . . .
    datasetInfos = []
    
    # npy
    info = OpDataSelection.DatasetInfo()
    # Will be read from the filesystem since the data won't be found in the project file.
    info.location = OpDataSelection.DatasetInfo.Location.ProjectInternal
    info.filePath = testNpyFileName
    info.internalPath = ""
    info.invertColors = False
    info.convertToGrayscale = False
    datasetInfos.append(info)
    
    # png
    info = OpDataSelection.DatasetInfo()
    info.location = OpDataSelection.DatasetInfo.Location.FileSystem
    info.filePath = testPngFileName
    info.internalPath = ""
    info.invertColors = False
    info.convertToGrayscale = False
    datasetInfos.append(info)
    
    # npy inverted
    info = OpDataSelection.DatasetInfo()
    info.location = OpDataSelection.DatasetInfo.Location.FileSystem
    info.filePath = testNpyFileName
    info.internalPath = ""
    info.invertColors = True
    info.convertToGrayscale = False
    datasetInfos.append(info)
    
    # png inverted
    info = OpDataSelection.DatasetInfo()
    info.location = OpDataSelection.DatasetInfo.Location.FileSystem
    info.filePath = testPngFileName
    info.internalPath = ""
    info.invertColors = True
    info.convertToGrayscale = False
    datasetInfos.append(info)

    # png grayscale
    info = OpDataSelection.DatasetInfo()
    info.location = OpDataSelection.DatasetInfo.Location.FileSystem
    info.filePath = testPngFileName
    info.internalPath = ""
    info.invertColors = False
    info.convertToGrayscale = True
    datasetInfos.append(info)
    
    # png grayscale & inverted
    info = OpDataSelection.DatasetInfo()
    info.location = OpDataSelection.DatasetInfo.Location.FileSystem
    info.filePath = testPngFileName
    info.internalPath = ""
    info.invertColors = True
    info.convertToGrayscale = True
    datasetInfos.append(info)
    
    # From project
    info = OpDataSelection.DatasetInfo()
    info.location = OpDataSelection.DatasetInfo.Location.ProjectInternal
    info.filePath = "This string should be ignored..."
    info.datasetId = 'dataset1'
    info.invertColors = False
    info.convertToGrayscale = False
    datasetInfos.append(info)

    reader.DatasetInfos.setValues(datasetInfos)

    # Read the test files using the data selection operator and verify the contents
    npyData = reader.OutputImages[0][...].wait()
    pngData = reader.OutputImages[1][...].wait()
    
    invertedNpyData = reader.OutputImages[2][...].wait()
    invertedPngData = reader.OutputImages[3][...].wait()
    
    grayscalePngData = reader.OutputImages[4][...].wait()

    invertedGrayscalePngData = reader.OutputImages[5][...].wait()

    projectInternalData = reader.OutputImages[6][...].wait()

    # Check raw images
    assert npyData.shape == (10,11,1)
    for x in range(npyData.shape[0]):
        for y in range(npyData.shape[1]):
            assert npyData[x,y,0] == x+y
 
    assert pngData.shape == (100, 200, 3)
    for x in range(pngData.shape[0]):
        for y in range(pngData.shape[1]):
            for c in range(a.shape[2]):
                assert pngData[x,y,c] == (x+y) % 256

    # Check inverted images
    assert invertedNpyData.shape == npyData.shape
    for x in range(invertedNpyData.shape[0]):
        for y in range(invertedNpyData.shape[1]):
            assert invertedNpyData[x,y,0] == 255-npyData[x,y]
 
    assert invertedPngData.shape == pngData.shape
    for x in range(invertedPngData.shape[0]):
        for y in range(pngData.shape[1]):
            for c in range(a.shape[2]):
                assert invertedPngData[x,y,c] == 255-pngData[x,y,0]

    # Check grayscale conversion 
    assert grayscalePngData.shape == (100, 200, 1)
    for x in range(grayscalePngData.shape[0]):
        for y in range(grayscalePngData.shape[1]):
            # (See formula in OpRgbToGrayscale)
            assert grayscalePngData[x,y,0] == int(numpy.round(  0.299*pngData[x,y,0]
                                                              + 0.587*pngData[x,y,1] 
                                                              + 0.114*pngData[x,y,2] ))

    # Check inverted grayscale conversion 
    assert invertedGrayscalePngData.shape == (100, 200, 1)
    for x in range(invertedGrayscalePngData.shape[0]):
        for y in range(invertedGrayscalePngData.shape[1]):
            # (See formula in OpRgbToGrayscale)
            assert invertedGrayscalePngData[x,y,0] == int(numpy.round(  0.299*invertedPngData[x,y,0]
                                                                      + 0.587*invertedPngData[x,y,1] 
                                                                      + 0.114*invertedPngData[x,y,2] ))

    assert projectInternalData.shape == pngData.shape
    assert (projectInternalData == pngData).all()
    
    # Clean up: Delete the test files.
    os.remove(testNpyFileName)
    os.remove(testPngFileName)
    os.remove(projectFileName)

































