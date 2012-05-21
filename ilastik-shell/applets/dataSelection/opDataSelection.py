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

    # A dataset info object
    Dataset = InputSlot(stype='object')

    # Output data
    ImageName = OutputSlot(stype='string')
    RawImage = OutputSlot()
    ProcessedImage = OutputSlot()
    
    def setupOutputs(self):
        datasetInfo = self.Dataset.value

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
        
        
        # Connect our external outputs to the internal operators we chose
        self.ProcessedImage.connect(processedProviderSlot)
        self.RawImage.connect(rawProviderSlot)

        # Set the new image name
        self.ImageName.setValue(datasetInfo.filePath)

