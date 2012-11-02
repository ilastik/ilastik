from lazyflow.graph import Operator, InputSlot, OutputSlot, OperatorWrapper

from lazyflow.operators import OpBlockedSparseLabelArray

class OpLabeling( Operator ):
    """
    Top-level operator for the labeling base class.
    Provides all the slots needed by the labeling GUI, but any operator that provides the necessary slots can also be used with the LabelingGui.
    """
    name="OpLabeling"
    category = "Top-level"

    # Input slots    
    InputImages = InputSlot(level=1) #: Original input data.
    LabelInputs = InputSlot(optional = True, level=1) #: Input for providing label data from an external source
    
    LabelsAllowedFlags = InputSlot(stype='bool', level=1) #: Specifies which images are permitted to be labeled 
    LabelEraserValue = InputSlot() #: The label value that signifies the 'eraser', i.e. voxels to clear labels from
    LabelDelete = InputSlot() #: When this input is set to a value, all labels of that value are deleted from the operator's data.

    # Output slots
    MaxLabelValue = OutputSlot() #: The highest label value currently stored in the array of labels
    LabelImages = OutputSlot(level=1) #: Stored labels from the user
    NonzeroLabelBlocks = OutputSlot(level=1) #: A list if slices that contain non-zero label values

    def __init__( self, *args, **kwargs ):
        """
        Instantiate all internal operators and connect them together.
        """
        super(OpLabeling, self).__init__( *args, **kwargs )

        # Create internal operators
        self.opInputShapeReader = OperatorWrapper( OpShapeReader, parent=self, graph=self.graph )
        self.opLabelArray = OperatorWrapper( OpBlockedSparseLabelArray, parent=self, graph=self.graph )

        # NOT wrapped
        self.opMaxLabel = OpMaxValue(parent=self, graph=self.graph)

        # Set up label cache shape input
        self.opInputShapeReader.Input.connect( self.InputImages )
        self.opLabelArray.inputs["shape"].connect( self.opInputShapeReader.OutputShape )

        # Set up other label cache inputs
        self.LabelInputs.connect( self.InputImages )
        self.opLabelArray.Input.connect( self.LabelInputs )
        self.opLabelArray.eraser.connect(self.LabelEraserValue)
        self.LabelEraserValue.setValue(255)
                
        # Initialize the delete input to -1, which means "no label".
        # Now changing this input to a positive value will cause label deletions.
        # (The deleteLabel input is monitored for changes.)
        self.opLabelArray.deleteLabel.connect(self.LabelDelete)
        self.LabelDelete.setValue(-1)
        
        # Find the highest label in all the label images
        self.opMaxLabel.Inputs.connect( self.opLabelArray.outputs['maxLabel'] )

        # Connect our internal outputs to our external outputs
        self.LabelImages.connect(self.opLabelArray.Output)
        self.MaxLabelValue.connect( self.opMaxLabel.Output )
        self.NonzeroLabelBlocks.connect(self.opLabelArray.nonzeroBlocks)
        
        def inputResizeHandler( slot, oldsize, newsize ):
            if ( newsize == 0 ):
                self.LabelImages.resize(0)
                self.NonzeroLabelBlocks.resize(0)
        self.InputImages.notifyResized( inputResizeHandler )

        # Check to make sure the non-wrapped operators stayed that way.
        assert self.opMaxLabel.Inputs.operator == self.opMaxLabel
        
        def handleNewInputImage( multislot, index, *args ):
            def handleInputReady(slot):
                self.setupCaches( multislot.index(slot) )
            multislot[index].notifyReady(handleInputReady)
                
        self.InputImages.notifyInserted( handleNewInputImage )

    def setupCaches(self, imageIndex):
        numImages = len(self.InputImages)
        inputSlot = self.InputImages[imageIndex]
        self.LabelInputs.resize(numImages)

        # Special case: We have to set up the shape of our label *input* according to our image input shape
        shapeList = list(self.InputImages[imageIndex].meta.shape)
        try:
            channelIndex = self.InputImages[imageIndex].meta.axistags.index('c')
            shapeList[channelIndex] = 1
        except:
            pass
        self.LabelInputs[imageIndex].meta.shape = tuple(shapeList)
        self.LabelInputs[imageIndex].meta.axistags = inputSlot.meta.axistags

        # Set the blockshapes for each input image separately, depending on which axistags it has.
        axisOrder = [ tag.key for tag in inputSlot.meta.axistags ]
        
        ## Label Array blocks
        blockDims = { 't' : 1, 'x' : 32, 'y' : 32, 'z' : 32, 'c' : 1 }
        blockShape = tuple( blockDims[k] for k in axisOrder )
        self.opLabelArray.blockShape.setValue( blockShape )

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

