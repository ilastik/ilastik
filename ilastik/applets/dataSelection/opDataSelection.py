from lazyflow.graph import Operator, InputSlot, OutputSlot, OperatorWrapper
from lazyflow.operators.ioOperators import OpStreamingHdf5Reader, OpInputDataReader
from ilastik.utility.operatorSubView import OperatorSubView

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
        self.axisorder = None

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
    The top-level operator for the data selection applet, implemented as a single-image operator.
    The applet uses an OperatorWrapper to make it suitable for use in a workflow.
    """
    name = "OpDataSelection"
    category = "Top-level"
    
    SupportedExtensions = OpInputDataReader.SupportedExtensions

    # Inputs    
    ProjectFile = InputSlot(stype='object') #: The project hdf5 File object (already opened)
    ProjectDataGroup = InputSlot(stype='string') #: The internal path to the hdf5 group where project-local datasets are stored within the project file
    WorkingDirectory = InputSlot(stype='filestring') #: The filesystem directory where the project file is located
    Dataset = InputSlot(stype='object') #: A DatasetInfo object

    # Outputs
    Image = OutputSlot() #: The output image
    AllowLabels = OutputSlot(stype='bool') #: A bool indicating whether or not this image can be used for training

    # Must be declared last of all slots.
    # When the shell detects that this slot has been resized, it assumes all the others have already been resized.
    ImageName = OutputSlot(stype='string') #: The name of the output image
    
    def __init__(self, *args, **kwargs):
        super(OpDataSelection, self).__init__(*args, **kwargs)
        self._opReader = None
    
    def setupOutputs(self):
        datasetInfo = self.Dataset.value
        internalPath = self.ProjectDataGroup.value + '/' + datasetInfo.datasetId

        # Data only comes from the project file if the user said so AND it exists in the project
        datasetInProject = (datasetInfo.location == DatasetInfo.Location.ProjectInternal)
        datasetInProject &= self.ProjectFile.connected() and \
                            internalPath in self.ProjectFile.value

        if self._opReader is not None:
            self.Image.disconnect()
            self._opReader.cleanUp()
        
        # If we should find the data in the project file, use a dataset reader
        if datasetInProject:
            self._opReader = OpStreamingHdf5Reader(parent=self)
            self._opReader.Hdf5File.setValue(self.ProjectFile.value)
            self._opReader.InternalPath.setValue(internalPath)
            providerSlot = self._opReader.OutputImage
        else:
            # Use a normal (filesystem) reader
            self._opReader = OpInputDataReader(parent=self)
            if datasetInfo.axisorder is not None:
                self._opReader.DefaultAxisOrder.setValue( datasetInfo.axisorder )
            self._opReader.WorkingDirectory.connect( self.WorkingDirectory )
            self._opReader.FilePath.setValue(datasetInfo.filePath)
            providerSlot = self._opReader.Output        
        
        # Connect our external outputs to the internal operators we chose
        self.Image.connect(providerSlot)
        
        # Set the image name and usage flag
        self.AllowLabels.setValue( datasetInfo.allowLabels )
        self.ImageName.setValue(datasetInfo.filePath)

    def propagateDirty(self, slot, subindex, roi):
        # Output slots are directly connected to internal operators
        pass

class OpMultiLaneDataSelection( OperatorWrapper ):
    
    def __init__(self, parent):
        super( OpMultiLaneDataSelection, self ).__init__(OpDataSelection, parent=parent, broadcastingSlotNames=['ProjectFile', 'ProjectDataGroup', 'WorkingDirectory'] )
    
    def addLane(self, laneIndex):
        """
        Add an image lane.
        """
        numLanes = len(self.innerOperators)
        
        # Only add this lane if we don't already have it
        # We might be called from within the context of our own insertSlot signal.
        if numLanes == laneIndex:
            self._insertInnerOperator(numLanes, numLanes+1)

    def removeLane(self, laneIndex, finalLength):
        """
        Remove an image lane.
        """
        numLanes = len(self.innerOperators)
        if numLanes > finalLength:
            self._removeInnerOperator(laneIndex, numLanes-1)

    def getLane(self, laneIndex):
        return OperatorSubView(self, laneIndex)
