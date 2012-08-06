from lazyflow.graph import Operator, InputSlot, OutputSlot

from lazyflow.operators.ioOperators import OpStreamingHdf5Reader, OpInputDataReader

import uuid

class DatasetInfo(object):
    """
    Struct-like class for describing dataset info.
    """
    class Location():
        FileSystem = 0
        ProjectInternal = 1
        
    def __init__(self):
        Location = DatasetInfo.Location
        self.location = Location.FileSystem # Whether the data will be found/stored on the filesystem or in the project file
        self._filePath = ""                 # The original path to the data (also used as a fallback if the data isn't in the project yet)
        self._datasetId = ""                # The name of the data within the project file (if it is stored locally)
        self.allowLabels = True             # Whether or not this dataset should be used for training a classifier.

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

class OpDataSelection(Operator):
    """
    The top-level operator for the data selection applet.
    This implementation supports single images.
    Use an OperatorWrapper to enable multi-image support.
    """
    name = "OpDataSelection"
    category = "Top-level"
    
    ProjectFile = InputSlot(stype='object') # The project hdf5 File object (already opened)
    ProjectDataGroup = InputSlot(stype='string') # The internal path to the hdf5 group where project-local
                                                 #  datasets are stored within the project file
    WorkingDirectory = InputSlot(stype='filestring') # The filesystem directory where the project file is located

    # A dataset info object
    Dataset = InputSlot(stype='object')

    # Output data
    ImageName = OutputSlot(stype='string')
    Image = OutputSlot()
    AllowLabels = OutputSlot(stype='bool')
    
    def setupOutputs(self):
        datasetInfo = self.Dataset.value
        internalPath = self.ProjectDataGroup.value + '/' + datasetInfo.datasetId

        # Data only comes from the project file if the user said so AND it exists in the project
        datasetInProject = (datasetInfo.location == DatasetInfo.Location.ProjectInternal)
        datasetInProject &= self.ProjectFile.connected() and \
                            internalPath in self.ProjectFile.value
        
        # If we should find the data in the project file, use a dataset reader
        if datasetInProject:
            reader = OpStreamingHdf5Reader(graph=self.graph)
            reader.Hdf5File.setValue(self.ProjectFile.value)
            reader.InternalPath.setValue(internalPath)
            providerSlot = reader.OutputImage
        else:
            # Use a normal (filesystem) reader
            reader = OpInputDataReader(graph=self.graph)
            reader.FilePath.setValue(datasetInfo.filePath)
            reader.WorkingDirectory.connect( self.WorkingDirectory )
            providerSlot = reader.Output        
        
        # Connect our external outputs to the internal operators we chose
        self.Image.connect(providerSlot)
        
        # Set the image name and usage flag
        self.AllowLabels.setValue( datasetInfo.allowLabels )
        self.ImageName.setValue(datasetInfo.filePath)

