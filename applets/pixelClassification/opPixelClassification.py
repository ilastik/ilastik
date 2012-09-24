from lazyflow.graph import Operator, InputSlot, OutputSlot, MultiInputSlot, MultiOutputSlot, OperatorWrapper

from lazyflow.operators import OpBlockedSparseLabelArray, OpValueCache, OpTrainRandomForestBlocked, \
                               OpPredictRandomForest, OpSlicedBlockedArrayCache, OpMultiArraySlicer2, OpPrecomputedInput

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

    PredictionsFromDisk = MultiInputSlot(optional=True)

    PredictionProbabilities = MultiOutputSlot() # Classification predictions

    PredictionProbabilityChannels = MultiOutputSlot(level=2) # Classification predictions, enumerated by channel
    
    MaxLabelValue = OutputSlot()
    LabelImages = MultiOutputSlot() # Labels from the user
    NonzeroLabelBlocks = MultiOutputSlot() # A list if slices that contain non-zero label values
    Classifier = OutputSlot() # We provide the classifier as an external output for other applets to use

    CachedPredictionProbabilities = MultiOutputSlot() # Classification predictions (via a cache)

    def __init__( self, graph ):
        """
        Instantiate all internal operators and connect them together.
        """
        super(OpPixelClassification, self).__init__(graph=graph)

        self.FreezePredictions.setValue(True) # Default
        
        # Create internal operators
        # Explicitly wrapped:
        self.opInputShapeReader = OperatorWrapper( OpShapeReader, graph=self.graph)
        self.opLabelArray = OperatorWrapper( OpBlockedSparseLabelArray,  graph=self.graph )
        self.predict = OperatorWrapper( OpPredictRandomForest, graph=self.graph )
        self.prediction_cache = OperatorWrapper( OpSlicedBlockedArrayCache, graph=self.graph )
        self.prediction_cache.Input.resize(0)
        self.prediction_cache_gui = OperatorWrapper( OpSlicedBlockedArrayCache, graph=self.graph )
        self.prediction_cache_gui.Input.resize(0)
        self.precomputed_predictions = OperatorWrapper( OpPrecomputedInput, graph=self.graph)
        self.precomputed_predictions_gui = OperatorWrapper( OpPrecomputedInput, graph=self.graph)

        # NOT wrapped
        self.opMaxLabel = OpMaxValue(graph=self.graph)
        self.opTrain = OpTrainRandomForestBlocked( graph=self.graph )

        # Set up label cache shape input
        self.opInputShapeReader.Input.connect( self.InputImages )
        self.opLabelArray.inputs["shape"].connect( self.opInputShapeReader.OutputShape )

        # Set up other label cache inputs
        self.LabelInputs.connect( self.InputImages )
        self.opLabelArray.inputs["Input"].connect( self.LabelInputs )
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
        self.opTrain.inputs['Images'].connect(self.CachedFeatureImages)
        self.opTrain.inputs["nonzeroLabelBlocks"].connect(self.opLabelArray.outputs["nonzeroBlocks"])
        self.opTrain.inputs['fixClassifier'].setValue(False)

        # The classifier is cached here to allow serializers to force in a pre-calculated classifier...
        self.classifier_cache = OpValueCache( graph=self.graph )
        self.classifier_cache.inputs["Input"].connect(self.opTrain.outputs['Classifier'])

        ##
        # 
        ##
        self.predict.inputs['Classifier'].connect(self.classifier_cache.outputs['Output']) 
        self.predict.inputs['Image'].connect(self.CachedFeatureImages)
        self.predict.inputs['LabelsCount'].connect(self.opMaxLabel.Output)
        
        # prediction cache for downstream operators (if they want it)
        self.prediction_cache.name = "PredictionCache"
        self.prediction_cache.inputs["fixAtCurrent"].setValue(False)
        self.prediction_cache.inputs["Input"].connect( self.predict.PMaps )

        # The serializer uses these operators to provide prediction data directly from the project file
        # if the predictions haven't become dirty since the project file was opened.
        self.precomputed_predictions.SlowInput.connect( self.prediction_cache.Output )
        self.precomputed_predictions.PrecomputedInput.connect( self.PredictionsFromDisk )

        # Prediction cache for the GUI
        self.prediction_cache_gui.name = "PredictionCache"
        self.prediction_cache_gui.inputs["fixAtCurrent"].connect( self.FreezePredictions )
        self.prediction_cache_gui.inputs["Input"].connect( self.predict.PMaps )

        self.precomputed_predictions_gui.SlowInput.connect( self.prediction_cache_gui.Output )
        self.precomputed_predictions_gui.PrecomputedInput.connect( self.PredictionsFromDisk )

        # Connect our internal outputs to our external outputs
        self.LabelImages.connect(self.opLabelArray.Output)
        self.MaxLabelValue.connect( self.opMaxLabel.Output )
        self.NonzeroLabelBlocks.connect(self.opLabelArray.nonzeroBlocks)
        self.PredictionProbabilities.connect(self.predict.PMaps)
        self.CachedPredictionProbabilities.connect(self.precomputed_predictions.Output)
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
        
        # Also provide each prediction channel as a separate layer (for the GUI)
        self.opPredictionSlicer = OperatorWrapper( OpMultiArraySlicer2, parent=self) 
        self.opPredictionSlicer.Input.connect( self.precomputed_predictions_gui.Output )
        self.opPredictionSlicer.AxisFlag.setValue('c')
        self.PredictionProbabilityChannels.connect( self.opPredictionSlicer.Slices )

        def handleNewInputImage( multislot, index, *args ):
            def handleInputReady(slot):
                self.setupCaches( multislot.index(slot) )
            multislot[index].notifyReady(handleInputReady)
                
        self.InputImages.notifyInserted( handleNewInputImage )

    def setupCaches(self, imageIndex):
        numImages = len(self.InputImages)
        inputSlot = self.InputImages[imageIndex]
#        # Can't setup if all inputs haven't been set yet.
#        if numImages != len(self.FeatureImages) or \
#           numImages != len(self.CachedFeatureImages):
#            return
#        
#        self.LabelImages.resize(numImages)
        self.LabelInputs.resize(numImages)

        # Special case: We have to set up the shape of our label *input* according to our image input shape
        channelIndex = self.InputImages[imageIndex].meta.axistags.index('c')
        shapeList = list(self.InputImages[imageIndex].meta.shape)
        shapeList[channelIndex] = 1
        self.LabelInputs[imageIndex].meta.shape = tuple(shapeList)
        self.LabelInputs[imageIndex].meta.axistags = inputSlot.meta.axistags

        # Set the blockshapes for each input image separately, depending on which axistags it has.
        axisOrder = [ tag.key for tag in inputSlot.meta.axistags ]
        
        ## Label Array blocks
        blockDims = { 't' : 1, 'x' : 32, 'y' : 32, 'z' : 32, 'c' : 1 }
        blockShape = tuple( blockDims[k] for k in axisOrder )
        self.opLabelArray.blockShape.setValue( blockShape )

        ## Pixel Cache blocks
        blockDimsX = { 't' : (1,1),
                       'z' : (128,256),
                       'y' : (128,256),
                       'x' : (1,1),
                       'c' : (2,2) }

        blockDimsY = { 't' : (1,1),
                       'z' : (128,256),
                       'y' : (1,1),
                       'x' : (128,256),
                       'c' : (2,2) }

        blockDimsZ = { 't' : (1,1),
                       'z' : (1,1),
                       'y' : (128,256),
                       'x' : (128,256),
                       'c' : (2,2) }

        innerBlockShapeX = tuple( blockDimsX[k][0] for k in axisOrder )
        outerBlockShapeX = tuple( blockDimsX[k][1] for k in axisOrder )

        innerBlockShapeY = tuple( blockDimsY[k][0] for k in axisOrder )
        outerBlockShapeY = tuple( blockDimsY[k][1] for k in axisOrder )

        innerBlockShapeZ = tuple( blockDimsZ[k][0] for k in axisOrder )
        outerBlockShapeZ = tuple( blockDimsZ[k][1] for k in axisOrder )

        self.prediction_cache.inputs["innerBlockShape"].setValue( (innerBlockShapeX, innerBlockShapeY, innerBlockShapeZ) )
        self.prediction_cache.inputs["outerBlockShape"].setValue( (outerBlockShapeX, outerBlockShapeY, outerBlockShapeZ) )

        self.prediction_cache_gui.inputs["innerBlockShape"].setValue( (innerBlockShapeX, innerBlockShapeY, innerBlockShapeZ) )
        self.prediction_cache_gui.inputs["outerBlockShape"].setValue( (outerBlockShapeX, outerBlockShapeY, outerBlockShapeZ) )

    def notifyDirty(self, inputSlot, key):
        # Nothing to do here: All outputs are directly connected to 
        #  internal operators that handle their own dirty propagation.
        pass

    def notifySubSlotDirty(self, slots, indexes, key):
        # Nothing to do here: All outputs are directly connected to 
        #  internal operators that handle their own dirty propagation.
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
        channelIndex = self.Input.meta.axistags.index('c')
        shapeList = list(self.Input.meta.shape)
        shapeList[channelIndex] = 1
        self.OutputShape.setValue( tuple(shapeList) )
    
    def execute(self, slot, roi, result):
        assert False, "Shouldn't get here.  Output is assigned a value in setupOutputs()"

    def propagateDirty(self, inputSlot, roi):
        # Our output changes when the input changed shape, not when it becomes dirty.
        pass

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

