from lazyflow.graph import Operator, InputSlot, OutputSlot, MultiInputSlot, MultiOutputSlot

from lazyflow.operators import OpPixelFeaturesPresmoothed, OpBlockedArrayCache, OpArrayPiper, Op5ToMulti, OpBlockedSparseLabelArray, OpArrayCache, \
                               OpTrainRandomForestBlocked, OpPredictRandomForest, OpSlicedBlockedArrayCache

from utility.simpleSignal import SimpleSignal
import numpy
import copy

class OpPixelClassification( Operator ):
    """
    Top-level operator for the 
    """
    name="OpPixelClassification"
    category = "Top-level"
    
    # Graph inputs
    
    InputImages = MultiInputSlot() # Original input data.  Used for display only.

    LabelInputs = MultiInputSlot(optional = True) # Input for providing label data from an external source

    FeatureImages = MultiInputSlot() # Computed feature images (each channel is a different feature)
    CachedFeatureImages = MultiInputSlot() # Cached feature data.

    PredictionProbabilities = MultiOutputSlot() # Classification predictions
    CachedPredictionProbabilities = MultiOutputSlot() # Classification predictions (via a cache)
    
    MaxLabelValue = OutputSlot()
    LabelImages = MultiOutputSlot() # Labels from the user
    NonzeroLabelBlocks = MultiOutputSlot() # A list if slices that contain non-zero label values

    def __init__( self, graph ):
        """
        Instantiate all internal operators and connect them together.
        """
        super(OpPixelClassification, self).__init__(graph=graph)
        
#        ## Signals (non-qt) ##
        self.inputDataChangedSignal = SimpleSignal()     # Input data loaded/changed
        self.labelsChangedSignal = SimpleSignal()        # New/changed label data
        self.pipelineConfiguredSignal = SimpleSignal()   # Pipeline is fully configured (all inputs are connected and have data)
        self.predictionMetaChangeSignal = SimpleSignal() # The prediction cache has changed its shape (or dtype).
                                                         #  The prediction cache's output configuration status is passed as the parameter.
        # Create internal operators
        self.opInputShapeReader = OpShapeReader(self.graph)
        self.opLabelArray = OpBlockedSparseLabelArray( self.graph )
        self.opMaxLabel = OpMaxValue(graph=self.graph)
        self.opTrain = OpTrainRandomForestBlocked( self.graph )
        self.predict=OpPredictRandomForest( self.graph )
        self.prediction_cache = OpSlicedBlockedArrayCache( self.graph )

        self.opInputShapeReader.Input.connect( self.InputImages ) #<-- Note: Now opInputShapeReader is wrapped
        self.opLabelArray.inputs["shape"].connect( self.opInputShapeReader.OutputShape ) #<-- Note: now opLabelArray is wrapped
        self.opLabelArray.inputs["Input"].connect( self.LabelInputs )
        self.opLabelArray.inputs["blockShape"].setValue((1, 32, 32, 32, 1))
        self.opLabelArray.inputs["eraser"].setValue(100)
        
        # Initialize the delete input to -1, which means "no label".
        # Now changing this input to a positive value will cause label deletions.
        # (The deleteLabel input is monitored for changes.)
        self.opLabelArray.inputs["deleteLabel"].setValue(-1)
        
        # Find the highest label in all the label images
        self.opMaxLabel.Inputs.connect( self.opLabelArray.outputs['maxLabel'] ) # opMaxLabel is now wrapped

        # Also expose the max label as an output of this top-level operator
        self.MaxLabelValue.connect( self.opMaxLabel.Output )

        ##
        # training
        ##
        
        self.opTrain.inputs['Labels'].connect(self.opLabelArray.outputs["Output"])
        self.opTrain.inputs['Images'].connect(self.CachedFeatureImages)
        self.opTrain.inputs["nonzeroLabelBlocks"].connect(self.opLabelArray.outputs["nonzeroBlocks"])
        self.opTrain.inputs['fixClassifier'].setValue(False)

        self.classifier_cache = OpArrayCache( self.graph )
        self.classifier_cache.inputs["Input"].connect(self.opTrain.outputs['Classifier'])

        ##
        # prediction
        ##
        self.predict.inputs['Classifier'].connect(self.classifier_cache.outputs['Output']) 
        self.predict.inputs['Image'].connect(self.FeatureImages) #<-- Note: Now predict is wrapped
        self.predict.inputs['LabelsCount'].connect(self.opMaxLabel.Output)
        
        # 
        self.prediction_cache.name = "PredictionCache"
        self.prediction_cache.inputs["fixAtCurrent"].setValue(True)
        self.prediction_cache.inputs["innerBlockShape"].setValue(((1,256,256,1,2),(1,256,1,256,2),(1,1,256,256,2)))
        self.prediction_cache.inputs["outerBlockShape"].setValue(((1,256,256,4,2),(1,256,4,256,2),(1,4,256,256,2)))
        self.prediction_cache.inputs["Input"].connect(self.predict.outputs["PMaps"])

        # Connect our internal outputs to our external outputs
        self.LabelImages.connect(self.opLabelArray.Output)
        self.NonzeroLabelBlocks.connect(self.opLabelArray.nonzeroBlocks)
        self.PredictionProbabilities.connect(self.predict.PMaps)
        self.CachedPredictionProbabilities.connect(self.prediction_cache.Output)
        
        def inputResizeHandler( slot, oldsize, newsize ):
            if ( newsize == 0 ):
                self.LabelImages.resize(0)
                self.NonzeroLabelBlocks.resize(0)
                self.PredictionProbabilities.resize(0)
                self.CachedPredictionProbabilities.resize(0)
        self.InputImages.notifyResized( inputResizeHandler )

        
    def setupOutputs(self):
        numImages = len(self.InputImages)
        
        # Can't setup if all inputs haven't been set yet.
        if numImages != len(self.FeatureImages) or \
           numImages != len(self.CachedFeatureImages):
            return
        
        self.PredictionProbabilities.resize(numImages)
        self.CachedPredictionProbabilities.resize(numImages)
        self.LabelImages.resize(numImages)
        self.LabelInputs.resize(numImages)
        self.NonzeroLabelBlocks.resize(numImages)
        for i in range( 0, numImages ):
            # Special case: We have to set up the shape of our label input according to our image input shape
            channelIndex = self.InputImages[i].meta.axistags.index('c')
            shapeList = list(self.InputImages[i].meta.shape)
            shapeList[channelIndex] = 1
            self.LabelInputs[i].meta.shape = tuple(shapeList)
            self.LabelInputs[i].meta.axistags = self.InputImages[i].meta.axistags
            
            self.PredictionProbabilities[i].meta.shape = self.predict.PMaps[i].meta.shape
            self.PredictionProbabilities[i].meta.dtype = self.predict.PMaps[i].meta.dtype
            self.PredictionProbabilities[i].meta.axistags = copy.copy(self.predict.PMaps[i].meta.axistags)
            
            self.CachedPredictionProbabilities[i].meta.shape = self.prediction_cache.Output[i].meta.shape
            self.CachedPredictionProbabilities[i].meta.dtype = self.prediction_cache.Output[i].meta.dtype
            self.CachedPredictionProbabilities[i].meta.axistags = copy.copy(self.prediction_cache.Output[i].meta.axistags)
            
            self.LabelImages[i].meta.shape = self.opLabelArray.Output[i].meta.shape
            self.LabelImages[i].meta.dtype = self.opLabelArray.Output[i].meta.dtype
            self.LabelImages[i].meta.axistags = copy.copy(self.opLabelArray.Output[i].meta.axistags)

            self.NonzeroLabelBlocks[i].meta.shape = self.opLabelArray.nonzeroBlocks[i].meta.shape
            self.NonzeroLabelBlocks[i].meta.dtype = self.opLabelArray.nonzeroBlocks[i].meta.dtype
            self.NonzeroLabelBlocks[i].meta.axistags = copy.copy(self.opLabelArray.nonzeroBlocks[i].meta.axistags)
    
    def setSubInSlot(self, multislot,slot,index, key,value):
        if slot.name == 'LabelInputs':
            self.opLabelArray.Input[index][key] = value
        else:
            assert False

    def getUniqueLabels(self):
        # TODO: Assumes only one image
        nonZeroValueOutputSlot = self.opLabelArray.outputs["nonzeroValues"]
        if len(nonZeroValueOutputSlot) > 0:
            return numpy.unique(numpy.asarray(self.opLabelArray.outputs["nonzeroValues"][0][:].allocate().wait()[0]))
        else:
            # Return an empty array
            return numpy.ndarray((0,), dtype=int)

    def setInputData(self, inputProvider):
        """
        Set the pipeline input data, which is given as an operator in inputProvider.
        """

        # Connect the input data to the pipeline
        self.images.inputs["Input0"].connect(inputProvider.outputs["Output"])

        # Notify the GUI, etc. that our input data changed
        self.inputDataChangedSignal.emit(inputProvider)
        
    def setAllLabelData(self, labelData):
        """
        Replace ALL of the input label data with the given array.
        Label shape is adjusted if necessary.
        """
        # The label data should have the correct shape (last dimension should be 1)
        assert labelData.shape[-1] == 1
        self.labels.inputs["shape"].setValue(labelData.shape)

        # Load the entire set of labels into the graph
        self.labels.inputs["Input"][:] = labelData
        
        self.labelsChangedSignal.emit()

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
        
        self.Inputs.notifyInserted( self.setOutputDirty )
        self.Inputs.notifyRemove( self.setOutputDirty )
        
    def setOutputDirty(self, *args, **kwargs):
        self.Output.setDirty(slice(None))
    
    def setupOutputs(self):
        self.Output.meta.shape = (1,)
        self.Output.meta.dtype = object

    def execute(self, slot, roi, result):
        # Return the max value of all our inputs
        maxValue = None
        for i, inputSubSlot in enumerate(self.Inputs):
            # Only use inputs that are actually configured
            if inputSubSlot.configured():
                if maxValue is None:
                    maxValue = inputSubSlot.value
                else:
                    maxValue = max(maxValue, inputSubSlot.value)
        result[0] = maxValue





















