from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.operators import OpBlockedSparseLabelArray
from ilastik.utility.operatorSubView import OperatorSubView
from ilastik.utility import OpMultiLaneWrapper

class OpLabelingTopLevel( Operator ):
    """
    Top-level operator for the labelingApplet base class.
    Provides all the slots needed by the labeling GUI, but any operator that provides the necessary slots can also be used with the LabelingGui.
    """
    name = "OpLabelingTopLevel"

    # Input slots
    InputImages = InputSlot(level=1) #: Original input data.
    LabelInputs = InputSlot(level=1) #: Input for providing label data from an external source
    
    LabelsAllowedFlags = InputSlot(level=1, stype='bool') #: Specifies which images are permitted to be labeled 
    LabelEraserValue = InputSlot(value=255) #: The label value that signifies the 'eraser', i.e. voxels to clear labels from
    LabelDelete = InputSlot() #: When this input is set to a value, all labels of that value are deleted from the operator's data.

    # Output slots
    LabelImages = OutputSlot(level=1) #: Stored labels from the user
    NonzeroLabelBlocks = OutputSlot(level=1) #: A list if slices that contain non-zero label values

    MaxLabelValue = OutputSlot() #: The highest label value currently stored in the array of labels

    def __init__(self, blockDims = None, *args, **kwargs):
        super( OpLabelingTopLevel, self ).__init__( *args, **kwargs )

        # Use a wrapper to create a labeling operator for each image lane
        self.opLabelLane = OpMultiLaneWrapper( OpLabelingSingleLane, operator_kwargs={'blockDims' : blockDims}, parent=self )

        # Special connection: Label Input must get its metadata (shape, axistags) from the main input image.
        self.LabelInputs.connect( self.InputImages )

        # Connect external inputs -> internal inputs
        self.opLabelLane.InputImage.connect( self.InputImages )
        self.opLabelLane.LabelInput.connect( self.LabelInputs )
        self.opLabelLane.LabelsAllowedFlag.connect( self.LabelsAllowedFlags )
        self.opLabelLane.LabelEraserValue.connect( self.LabelEraserValue )
        self.opLabelLane.LabelDelete.connect( self.LabelDelete )

        # Initialize the delete input to -1, which means "no label".
        # Now changing this input to a positive value will cause label deletions.
        # (The deleteLabel input is monitored for changes.)
        self.LabelDelete.setValue(-1)

        # Connect internal outputs -> external outputs
        self.LabelImages.connect( self.opLabelLane.LabelImage )
        self.NonzeroLabelBlocks.connect( self.opLabelLane.NonzeroLabelBlocks )

        # Use an OpMaxValue to find the highest label in all the label image lanes
        self.opMaxLabel = OpMaxValue( parent=self )
        self.opMaxLabel.Inputs.connect( self.opLabelLane.MaxLabelValue )
        self.MaxLabelValue.connect( self.opMaxLabel.Output )

    def propagateDirty(self, slot, subindex, roi):
        # Nothing to do here: All outputs are directly connected to 
        #  internal operators that handle their own dirty propagation.
        pass

    def setInSlot(self, slot, subindex, roi, value):
        # Nothing to do here: All inputs that support __setitem__
        #   are directly connected to internal operators.
        pass

    ###
    # MultiLaneOperatorABC
    ###

    def addLane(self, laneIndex):
        """
        Add an image lane.
        """
        numLanes = len(self.InputImages)
        assert laneIndex == numLanes, "Lanes must be appended"

        # Just resize one of our multi-inputs.
        # The others will resize automatically
        self.InputImages.resize(numLanes+1)

    def removeLane(self, laneIndex, finalLength):
        """
        Remove an image lane.
        """
        numLanes = len(self.InputImages)
        self.InputImages.removeSlot(laneIndex, numLanes-1)

    def getLane(self, laneIndex):
        return OperatorSubView(self, laneIndex)

class OpLabelingSingleLane( Operator ):
    name="OpLabelingSingleLane"

    # Input slots
    InputImage = InputSlot() #: Original input data.
    LabelInput = InputSlot(optional = True) #: Input for providing label data from an external source
    
    LabelsAllowedFlag = InputSlot(stype='bool') #: Specifies which images are permitted to be labeled 
    LabelEraserValue = InputSlot(value=255) #: The label value that signifies the 'eraser', i.e. voxels to clear labels from
    LabelDelete = InputSlot() #: When this input is set to a value, all labels of that value are deleted from the operator's data.

    # Output slots
    LabelImage = OutputSlot() #: Stored labels from the user
    NonzeroLabelBlocks = OutputSlot() #: A list if slices that contain non-zero label values

    MaxLabelValue = OutputSlot()

    def __init__(self, blockDims = None, *args, **kwargs):
        """
        Instantiate all internal operators and connect them together.
        """
        super(OpLabelingSingleLane, self).__init__( *args, **kwargs )

        # Configuration options
        if blockDims is None:
            blockDims = { 't' : 1, 'x' : 32, 'y' : 32, 'z' : 32, 'c' : 1 } 
        assert isinstance(blockDims, dict)
        self._blockDims = blockDims

        # Create internal operators
        self.opInputShapeReader = OpShapeReader( parent=self )
        self.opLabelArray = OpBlockedSparseLabelArray( parent=self )

        # Set up label cache shape input
        self.opInputShapeReader.Input.connect( self.InputImage )
        # Note: 'shape' is a (poorly named) INPUT SLOT here
        self.opLabelArray.shape.connect( self.opInputShapeReader.OutputShape )

        # Set up other label cache inputs
        self.opLabelArray.Input.connect( self.LabelInput )
        self.opLabelArray.eraser.connect(self.LabelEraserValue)                
        self.opLabelArray.deleteLabel.connect(self.LabelDelete)
        
        # Connect our internal outputs to our external outputs
        self.LabelImage.connect( self.opLabelArray.Output )
        self.NonzeroLabelBlocks.connect( self.opLabelArray.nonzeroBlocks )
        self.MaxLabelValue.connect( self.opLabelArray.maxLabel )
        
    def setupOutputs(self):
        self.setupInputMeta()
        self.setupCache(self._blockDims)

    def setupInputMeta(self):
        # Special case: We have to set up the shape of our label *input* according to our image input shape
        shapeList = list(self.InputImage.meta.shape)
        try:
            # If present, LabelInput channel dim must be 1
            channelIndex = self.InputImage.meta.axistags.index('c')
            shapeList[channelIndex] = 1
        except IndexError:
            pass
        self.LabelInput.meta.shape = tuple(shapeList)
        self.LabelInput.meta.axistags = self.InputImage.meta.axistags

    def setupCache(self, blockDims):
        # Set the blockshapes for each input image separately, depending on which axistags it has.
        axisOrder = map(lambda tag: tag.key, self.InputImage.meta.axistags )
        
        ## Label Array blocks
        blockShape = tuple( blockDims[k] for k in axisOrder )
        self.opLabelArray.blockShape.setValue( blockShape )

    def cleanUp(self):
        self.LabelInput.disconnect()
        super( OpLabelingSingleLane, self ).cleanUp()

    def propagateDirty(self, slot, subindex, roi):
        # Nothing to do here: All outputs are directly connected to 
        #  internal operators that handle their own dirty propagation.
        pass

    def setInSlot(self, slot, subindex, roi, value):
        # Nothing to do here: All inputs that support __setitem__
        #   are directly connected to internal operators.
        pass

class OpShapeReader(Operator):
    """
    This operator outputs the shape of its input image, except the number of channels is set to 1.
    """
    Input = InputSlot()
    OutputShape = OutputSlot(stype='shapetuple')
    
    def __init__(self, *args, **kwargs):
        super(OpShapeReader, self).__init__(*args, **kwargs)
    
    def setupOutputs(self):
        self.OutputShape.meta.shape = (1,)
        self.OutputShape.meta.axistags = 'shapetuple'
        self.OutputShape.meta.dtype = tuple
        
        # Our output is simply the shape of our input, but with only one channel
        shapeList = list(self.Input.meta.shape)
        try:
            channelIndex = self.Input.meta.axistags.index('c')
            shapeList[channelIndex] = 1
        except:
            pass
        self.OutputShape.setValue( tuple(shapeList) )
    
    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here.  Output is assigned a value in setupOutputs()"

    def propagateDirty(self, slot, subindex, roi):
        # Our output changes when the input changed shape, not when it becomes dirty.
        pass

class OpMaxValue(Operator):
    """
    Accepts a list of non-array values as an input and outputs the max of the list.
    """
    Inputs = InputSlot(level=1) # A list of non-array values
    Output = OutputSlot()
    
    def __init__(self, *args, **kwargs):
        super(OpMaxValue, self).__init__(*args, **kwargs)
        self.Output.meta.shape = (1,)
        self.Output.meta.dtype = object
        self._output = 0
        
    def setupOutputs(self):
        self.updateOutput()
        self.Output.setValue(self._output)

    def execute(self, slot, subindex, roi, result):
        result[0] = self._output
        return result

    def propagateDirty(self, inputSlot, subindex, roi):
        self.updateOutput()
        self.Output.setValue(self._output)

    def updateOutput(self):
        # Return the max value of all our inputs
        maxValue = None
        for i, inputSubSlot in enumerate(self.Inputs):
            # Only use inputs that are actually configured
            if inputSubSlot.ready():
                if maxValue is None:
                    maxValue = inputSubSlot.value
                else:
                    maxValue = max(maxValue, inputSubSlot.value)

        self._output = maxValue

