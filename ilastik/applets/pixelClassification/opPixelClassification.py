from lazyflow.graph import Operator, InputSlot, OutputSlot, MultiInputSlot, MultiOutputSlot, OperatorWrapper

from lazyflow.operators import OpBlockedSparseLabelArray, OpValueCache, \
                               OpTrainRandomForestBlocked, OpPredictRandomForest, OpSlicedBlockedArrayCache

class OpPixelClassification( Operator ):
    """
    Top-level operator for the 
    """
    name="OpPixelClassification"
    category = "Top-level"
    
    # Graph inputs
    
    InputImages = MultiInputSlot() # Original input data.  Used for display only.

    LabelsAllowedFlags = MultiInputSlot(stype='bool') # Specifies which images are permitted to be labeled 
    LabelInputs = MultiInputSlot(optional = True) # Input for providing label data from an external source

    FeatureImages = MultiInputSlot() # Computed feature images (each channel is a different feature)
    CachedFeatureImages = MultiInputSlot() # Cached feature data.

    FreezePredictions = InputSlot(stype='bool')

    PredictionProbabilities = MultiOutputSlot() # Classification predictions
    CachedPredictionProbabilities = MultiOutputSlot() # Classification predictions (via a cache)
    
    MaxLabelValue = OutputSlot()
    LabelImages = MultiOutputSlot() # Labels from the user
    NonzeroLabelBlocks = MultiOutputSlot() # A list if slices that contain non-zero label values
    Classifier = OutputSlot() # We provide the classifier as an external output for other applets to use

    def __init__( self, graph ):
        """
        Instantiate all internal operators and connect them together.
        """
        super(OpPixelClassification, self).__init__(graph=graph)

        self.FreezePredictions.setValue(True) # Default
        
        # Create internal operators
        # Explicitly wrapped:
        self.opInputShapeReader = OperatorWrapper( OpShapeReader(graph=self.graph) )
        self.opLabelArray = OperatorWrapper( OpBlockedSparseLabelArray( graph=self.graph ) )
        self.predict = OperatorWrapper( OpPredictRandomForest( graph=self.graph ) )
        self.prediction_cache = OperatorWrapper( OpSlicedBlockedArrayCache( graph=self.graph ) )
        self.prediction_cache.Input.resize(0)

        # NOT wrapped
        self.opMaxLabel = OpMaxValue(graph=self.graph)
        self.opTrain = OpTrainRandomForestBlocked( graph=self.graph )

        # Set up label cache shape input
        self.opInputShapeReader.Input.connect( self.InputImages )
        self.opLabelArray.inputs["shape"].connect( self.opInputShapeReader.OutputShape )

        # Set up other label cache inputs
        self.LabelInputs.connect( self.InputImages )
        self.opLabelArray.inputs["Input"].connect( self.LabelInputs )
        self.opLabelArray.inputs["blockShape"].setValue((1, 32, 32, 32, 1))
        self.opLabelArray.inputs["eraser"].setValue(100)
                
        # Initialize the delete input to -1, which means "no label".
        # Now changing this input to a positive value will cause label deletions.
        # (The deleteLabel input is monitored for changes.)
        self.opLabelArray.inputs["deleteLabel"].setValue(-1)
        
        # Find the highest label in all the label images
        self.opMaxLabel.Inputs.connect( self.opLabelArray.outputs['maxLabel'] )

        ##
        # training
        ##
        
        self.opTrain.inputs['Labels'].connect(self.opLabelArray.outputs["Output"])
        self.opTrain.inputs['Images'].connect(self.FeatureImages)
        self.opTrain.inputs["nonzeroLabelBlocks"].connect(self.opLabelArray.outputs["nonzeroBlocks"])
        self.opTrain.inputs['fixClassifier'].setValue(False)

        # The classifier is cached here to allow serializers to force in a pre-calculated classifier...
        self.classifier_cache = OpValueCache( graph=self.graph )
        self.classifier_cache.inputs["Input"].connect(self.opTrain.outputs['Classifier'])

        ##
        # prediction
        ##
        self.predict.inputs['Classifier'].connect(self.classifier_cache.outputs['Output']) 
        self.predict.inputs['Image'].connect(self.CachedFeatureImages)
        self.predict.inputs['LabelsCount'].connect(self.opMaxLabel.Output)
        
        # 
        self.prediction_cache.name = "PredictionCache"
        self.prediction_cache.inputs["fixAtCurrent"].connect( self.FreezePredictions )
        self.prediction_cache.inputs["innerBlockShape"].setValue(((1,128,128,1,2),(1,128,1,128,2),(1,1,128,128,2)))
        self.prediction_cache.inputs["outerBlockShape"].setValue(((1,256,256,1,2),(1,256,1,256,2),(1,1,256,256,2)))
        self.prediction_cache.inputs["Input"].connect(self.predict.outputs["PMaps"])

        # Connect our internal outputs to our external outputs
        self.LabelImages.connect(self.opLabelArray.Output)
        self.MaxLabelValue.connect( self.opMaxLabel.Output )
        self.NonzeroLabelBlocks.connect(self.opLabelArray.nonzeroBlocks)
        self.PredictionProbabilities.connect(self.predict.PMaps)
        self.CachedPredictionProbabilities.connect(self.prediction_cache.Output)
        self.Classifier.connect( self.classifier_cache.Output )
        
        def inputResizeHandler( slot, oldsize, newsize ):
            if ( newsize == 0 ):
                self.LabelImages.resize(0)
                self.NonzeroLabelBlocks.resize(0)
                self.PredictionProbabilities.resize(0)
                self.CachedPredictionProbabilities.resize(0)
        self.InputImages.notifyResized( inputResizeHandler )

        # Check to make sure the non-wrapped operators stayed that way.
        assert self.opMaxLabel.Inputs.operator == self.opMaxLabel
        assert self.opTrain.Images.operator == self.opTrain
        
    def setupOutputs(self):
        numImages = len(self.InputImages)
        
        # Can't setup if all inputs haven't been set yet.
        if numImages != len(self.FeatureImages) or \
           numImages != len(self.CachedFeatureImages):
            return
        
        self.LabelImages.resize(numImages)
        self.LabelInputs.resize(numImages)

        for i in range( 0, numImages ):
            # Special case: We have to set up the shape of our label *input* according to our image input shape
            channelIndex = self.InputImages[i].meta.axistags.index('c')
            shapeList = list(self.InputImages[i].meta.shape)
            shapeList[channelIndex] = 1
            self.LabelInputs[i].meta.shape = tuple(shapeList)
            self.LabelInputs[i].meta.axistags = self.InputImages[i].meta.axistags

    def notifyDirty(self, inputSlot, key):
        # Nothing to do here: All outputs are directly connected to 
        #  internal operators that handle their own dirty propagation.
        pass

class OpShapeReader(Operator):
    """
    This operator outputs the shape of its input image, except the number of channels is set to 1.
    """
    Input = InputSlot()
    OutputShape = OutputSlot(stype='shapetuple')
    
    def setupOutputs(self):
        self.OutputShape.meta.shape = (1,)
        self.OutputShape.meta.axistags = 'shapetuple'
        self.OutputShape.meta.dtype = tuple
    
    def execute(self, slot, roi, result):
        # Our 'result' is simply the shape of our input, but with only one channel
        channelIndex = self.Input.meta.axistags.index('c')
        shapeList = list(self.Input.meta.shape)
        shapeList[channelIndex] = 1
        result[0] = tuple(shapeList)

class OpMaxValue(Operator):
    """
    Accepts a list of non-array values as an input and outputs the max of the list.
    """
    Inputs = MultiInputSlot() # A list of non-array values
    Output = OutputSlot()
    
    def __init__(self, *args, **kwargs):
        super(OpMaxValue, self).__init__(*args, **kwargs)
        self.Output.meta.shape = (1,)
        self.Output.meta.dtype = object
        self._output = 0
        
    def setupOutputs(self):
        self.updateOutput()
        self.Output.setValue(self._output)

    def execute(self, slot, roi, result):
        result[0] = self._output
        return result

    def notifySubSlotDirty(self, slots, indexes, roi):
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


