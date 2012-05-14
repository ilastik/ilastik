from lazyflow.graph import Graph, Operator, InputSlot, OutputSlot, MultiInputSlot, MultiOutputSlot

from lazyflow.operators.ioOperators import OpStreamingHdf5Reader, OpInputDataReader
from lazyflow.operators.obsolete.vigraOperators import OpGrayscaleInverter, OpRgbToGrayscale
import copy

import numpy
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
    WorkingDirectory = InputSlot(stype='filestring', optional=True)

    # Array of DatasetInfo objects (see above)
    DatasetInfos = MultiInputSlot(stype='object')

    # Output data
    ImageNames = MultiOutputSlot(stype='string')
    RawImages = MultiOutputSlot()
    ProcessedImages = MultiOutputSlot()
    
    def __init__(self, graph):
        super(OpDataSelection, self).__init__(graph=graph)

        # Create an internal operator for reading data from disk
        self.readers = []
        self.providerSlots = []
        
        def inputResizeHandler( slot, oldsize, newsize ):
            if ( newsize == 0 ):
                self.ProcessedImages.resize(0)
                self.RawImages.resize(0)
        self.DatasetInfos.notifyResized(inputResizeHandler)
    
    def setupOutputs(self):
        numInputs = len(self.DatasetInfos)

        # Ensure the proper number of outputs
        self.ProcessedImages.resize(numInputs)
        self.RawImages.resize(numInputs)

        # Rebuild the list of provider slots from scratch
        self.processedProviderSlots = []
        self.rawProviderSlots = []

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
                reader = OpStreamingHdf5Reader(graph=self.graph)
                reader.ProjectFile.setValue(self.ProjectFile.value)
                reader.InternalPath.setValue(internalPath)
                processedProviderSlot = reader.OutputImage
                rawProviderSlot = reader.OutputImage
            else:
                # Use a normal (filesystem) reader
                reader = OpInputDataReader(graph=self.graph)
                reader.FilePath.setValue(datasetInfo.filePath)
                reader.WorkingDirectory.connect( self.WorkingDirectory )
                processedProviderSlot = reader.Output
                rawProviderSlot = reader.Output

            # If the user wants to invert the image,
            #  insert an intermediate inversion operator on this subslot
            if datasetInfo.invertColors:
                inverter = OpGrayscaleInverter(graph=self.graph)
                inverter.input.connect(processedProviderSlot)
                processedProviderSlot = inverter.output
            
            # If the user wants to convert to grayscale,
            #  insert an intermediate rgb-to-grayscale operator on this subslot
            if datasetInfo.convertToGrayscale:
                converter = OpRgbToGrayscale(graph=self.graph)
                converter.input.connect(processedProviderSlot)
                processedProviderSlot = converter.output
            
            # Store the operator that is providing the output for this subslot
            self.processedProviderSlots.append(processedProviderSlot)
            self.rawProviderSlots.append(rawProviderSlot)

            # Copy the metadata for the raw image
            self.RawImages[i].meta.dtype = rawProviderSlot.meta.dtype
            self.RawImages[i].meta.shape = rawProviderSlot.meta.shape
            self.RawImages[i].meta.axistags = copy.copy(rawProviderSlot.meta.axistags)

            # Copy the metadata from the processed provider we ended up with
            self.ProcessedImages[i].meta.dtype = processedProviderSlot.meta.dtype
            self.ProcessedImages[i].meta.shape = processedProviderSlot.meta.shape
            self.ProcessedImages[i].meta.axistags = copy.copy(processedProviderSlot.meta.axistags)

        # Finally, list the new image names, too
        self.ImageNames.resize(numInputs)
        for i in range(numInputs):
            datasetInfo = self.DatasetInfos[i].value
            self.ImageNames[i].setValue(datasetInfo.filePath)

    def getSubOutSlot(self, slots, indexes, key, result):
        slot = slots[0]
        if slot.name == "ProcessedImages":
            # Request the output from the appropriate internal operator output.
            request = self.processedProviderSlots[indexes[0]][key].writeInto(result)
            result[...] = request.wait()
        if slot.name == "RawImages":
            # Request the output from the appropriate internal operator output.
            request = self.rawProviderSlots[indexes[0]][key].writeInto(result)
            result[...] = request.wait()

