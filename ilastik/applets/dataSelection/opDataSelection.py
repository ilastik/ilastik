from lazyflow.graph import Operator, InputSlot, OutputSlot, OperatorWrapper
from lazyflow.operators.ioOperators import OpStreamingHdf5Reader, OpInputDataReader
from lazyflow.operators import OpMetadataInjector

from ilastik.utility import OpMultiLaneWrapper
from lazyflow.operators import Op5ifyer

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
        self.drange = None
        self.fromstack = False
        self.nickname = ""

        # If present, axistags supercedes axisorder member.
        self.axisorder = None
        self.axistags = None

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
    ProjectFile = InputSlot(stype='object', optional=True) #: The project hdf5 File object (already opened)
    ProjectDataGroup = InputSlot(stype='string', optional=True) #: The internal path to the hdf5 group where project-local datasets are stored within the project file
    WorkingDirectory = InputSlot(stype='filestring') #: The filesystem directory where the project file is located
    Dataset = InputSlot(stype='object') #: A DatasetInfo object

    # Outputs
    Image = OutputSlot() #: The output image
    AllowLabels = OutputSlot(stype='bool') #: A bool indicating whether or not this image can be used for training

    ImageName = OutputSlot(stype='string') #: The name of the output image
    
    def __init__(self, force5d=False, *args, **kwargs):
        super(OpDataSelection, self).__init__(*args, **kwargs)
        self.force5d = force5d
        self._opReaders = []
    
    def setupOutputs(self):
        if len(self._opReaders) > 0:
            self.Image.disconnect()
            for reader in reversed(self._opReaders):
                reader.cleanUp()
            self._opReaders = []
        
        datasetInfo = self.Dataset.value

        # Data only comes from the project file if the user said so AND it exists in the project
        datasetInProject = (datasetInfo.location == DatasetInfo.Location.ProjectInternal)
        datasetInProject &= self.ProjectFile.ready()
        if datasetInProject:
            internalPath = self.ProjectDataGroup.value + '/' + datasetInfo.datasetId
            datasetInProject &= internalPath in self.ProjectFile.value

        # If we should find the data in the project file, use a dataset reader
        if datasetInProject:
            opReader = OpStreamingHdf5Reader(parent=self)
            opReader.Hdf5File.setValue(self.ProjectFile.value)
            opReader.InternalPath.setValue(internalPath)
            providerSlot = opReader.OutputImage
            self._opReaders.append(opReader)
        else:
            # Use a normal (filesystem) reader
            opReader = OpInputDataReader(parent=self)
            if datasetInfo.axisorder is not None:
                opReader.DefaultAxisOrder.setValue( datasetInfo.axisorder )
            opReader.WorkingDirectory.setValue( self.WorkingDirectory.value )
            opReader.FilePath.setValue(datasetInfo.filePath)
            providerSlot = opReader.Output
            self._opReaders.append(opReader)

        if self.force5d:
            op5 = Op5ifyer(parent=self)
            op5.input.connect(providerSlot)
            providerSlot = op5.output
            self._opReaders.append(op5)
        
        # If there is no channel axis, use an Op5ifyer to append one.
        if providerSlot.meta.axistags.index('c') >= len( providerSlot.meta.axistags ):
            op5 = Op5ifyer( parent=self )
            providerKeys = "".join( providerSlot.meta.getTaggedShape().keys() )
            op5.order.setValue(providerKeys + 'c')
            op5.input.connect( providerSlot )
            providerSlot = op5.output
            self._opReaders.append( op5 )

        # Inject metadata if the dataset info specified any.
        if datasetInfo.drange or datasetInfo.axistags is not None:
            metadata = {}
            metadata['drange'] = datasetInfo.drange
            if datasetInfo.axistags is not None:
                metadata['axistags'] = datasetInfo.axistags
            opMetadataInjector = OpMetadataInjector( parent=self )
            opMetadataInjector.Input.connect( providerSlot )
            opMetadataInjector.Metadata.setValue( metadata )
            providerSlot = opMetadataInjector.Output
            self._opReaders.append( opMetadataInjector )
        
        # Connect our external outputs to the internal operators we chose
        self.Image.connect(providerSlot)
        
        # Set the image name and usage flag
        self.AllowLabels.setValue( datasetInfo.allowLabels )
        
        imageName = datasetInfo.nickname
        if imageName == "":
            imageName = datasetInfo.filePath
        self.ImageName.setValue(imageName)

    def propagateDirty(self, slot, subindex, roi):
        # Output slots are directly connected to internal operators
        pass

    @classmethod
    def getInternalDatasets(cls, filePath):
        return OpInputDataReader.getInternalDatasets( filePath )

class OpDataSelectionGroup( Operator ):
    # Inputs
    ProjectFile = InputSlot(stype='object', optional=True)
    ProjectDataGroup = InputSlot(stype='string', optional=True)
    WorkingDirectory = InputSlot(stype='filestring')
    DatasetRoles = InputSlot(stype='object')

    DatasetGroup = InputSlot(stype='object', level=1, optional=True) # Must mark as optional because not all subslots are required.

    # Outputs
    ImageGroup = OutputSlot(level=1)
    Image = OutputSlot() # The first dataset. Equivalent to ImageGroup[0]

    # Must be the LAST slot declared in this class.
    # When the shell detects that this slot has been resized,
    #  it assumes all the others have already been resized.
    ImageName = OutputSlot() # Name of the first dataset is used.  Other names are ignored.
    
    def __init__(self, force5d=False, *args, **kwargs):
        super(OpDataSelectionGroup, self).__init__(*args, **kwargs)
        self._opDatasets = None
        self._roles = []
        self._force5d = force5d
    
    def setupOutputs(self):
        # Create internal operators
        if self.DatasetRoles.value == self._roles:
            # No additional setup needed; Internal operators will set themselves up as needed.
            return
        self._roles = self.DatasetRoles.value
        # Clean up the old operators
        self.ImageGroup.disconnect()
        self.Image.disconnect()
        if self._opDatasets is not None:
            self._opDatasets.cleanUp()

        self._opDatasets = OperatorWrapper( OpDataSelection, parent=self, operator_kwargs={ 'force5d' : self._force5d },
                                            broadcastingSlotNames=['ProjectFile', 'ProjectDataGroup', 'WorkingDirectory'] )
        self.ImageGroup.connect( self._opDatasets.Image )
        self._opDatasets.ProjectFile.connect( self.ProjectFile )
        self._opDatasets.ProjectDataGroup.connect( self.ProjectDataGroup )
        self._opDatasets.WorkingDirectory.connect( self.WorkingDirectory )
        self._opDatasets.Dataset.connect( self.DatasetGroup )

        self.DatasetGroup.resize( len(self._roles) )
        
        if len( self._opDatasets.Image ) > 0:
            self.Image.connect( self._opDatasets.Image[0] )
            self.ImageName.connect( self._opDatasets.ImageName[0] )

    def execute(self, slot, subindex, rroi, result):
#        if slot == self.Image:
#            result[:] = self._opDatasets.Image(rroi.start, rroi.stop).wait()
#        if slot == self.ImageName:
#            result[:] = self._opDatasets.ImageName[0].value
#            return result
#        else:
            assert False, "Unknown or unconnected output slot."

    def propagateDirty(self, slot, subindex, roi):
        # Output slots are directly connected to internal operators
        pass

class OpMultiLaneDataSelectionGroup( OpMultiLaneWrapper ):
    def __init__(self, force5d=False, *args, **kwargs):
        kwargs.update( { 'operator_kwargs' : {'force5d' : force5d},
                         'broadcastingSlotNames' : ['ProjectFile', 'ProjectDataGroup', 'WorkingDirectory', 'DatasetRoles'] } )
        super( OpMultiLaneDataSelectionGroup, self ).__init__(OpDataSelectionGroup, *args, **kwargs )
    
        # 'value' slots
        assert self.ProjectFile.level == 0
        assert self.ProjectDataGroup.level == 0
        assert self.WorkingDirectory.level == 0
        assert self.DatasetRoles.level == 0
        
        # Indexed by [lane][role]
        assert self.DatasetGroup.level == 2, "DatasetGroup is supposed to be a level-2 slot, indexed by [lane][role]"
    
    def addLane(self, laneIndex):
        """Reimplemented from base class."""
        numLanes = len(self.innerOperators)
        
        # Only add this lane if we don't already have it
        # We might be called from within the context of our own insertSlot signal.
        if numLanes == laneIndex:
            super( OpMultiLaneDataSelectionGroup, self ).addLane( laneIndex )

    def removeLane(self, laneIndex, finalLength):
        """Reimplemented from base class."""
        numLanes = len(self.innerOperators)
        if numLanes > finalLength:
            super( OpMultiLaneDataSelectionGroup, self ).removeLane( laneIndex, finalLength )








