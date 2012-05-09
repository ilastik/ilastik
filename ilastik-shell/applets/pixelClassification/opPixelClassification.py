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

    NumClasses = InputSlot() # The number of possible labels in the image
    LabelInputs = MultiInputSlot(optional = True) # Input for providing label data from an external source

    FeatureImages = MultiInputSlot() # Computed feature images (each channel is a different feature)
    CachedFeatureImages = MultiInputSlot() # Cached feature data.

    PredictionProbabilities = MultiOutputSlot() # Classification predictions
    CachedPredictionProbabilities = MultiOutputSlot() # Classification predictions (via a cache)
    
    LabelImages = MultiOutputSlot() # Labels from the user
    NonzeroLabelBlocks = MultiOutputSlot() # A list if slices that contain non-zero label values

    def __init__( self, graph ):
        """
        Instantiate all internal operators and connect them together.
        """
        super(OpPixelClassification, self).__init__(graph=graph)
        
#        ## Signals (non-qt) ##
        self.inputDataChangedSignal = SimpleSignal()     # Input data loaded/changed
#        self.featuresChangedSignal = SimpleSignal()      # New/changed feature selections
        self.labelsChangedSignal = SimpleSignal()        # New/changed label data
        self.pipelineConfiguredSignal = SimpleSignal()   # Pipeline is fully configured (all inputs are connected and have data)
        self.predictionMetaChangeSignal = SimpleSignal() # The prediction cache has changed its shape (or dtype).
                                                         #  The prediction cache's output configuration status is passed as the parameter.
        # Create internal operators
        self.opInputShapeReader = OpShapeReader(self.graph)
        self.opLabelArray = OpBlockedSparseLabelArray( self.graph )
        self.opTrain = OpTrainRandomForestBlocked( self.graph )
        self.predict=OpPredictRandomForest( self.graph )
        self.prediction_cache = OpSlicedBlockedArrayCache( self.graph )

        self.opInputShapeReader.Input.connect( self.InputImages ) #<-- Note: Now opInputShapeReader is wrapped
        self.opLabelArray.inputs["shape"].connect( self.opInputShapeReader.OutputShape ) #<-- Note: now opLabelArray is wrapped
        self.opLabelArray.inputs["Input"].connect( self.LabelImages )
        self.opLabelArray.inputs["blockShape"].setValue((1, 32, 32, 32, 1))
        self.opLabelArray.inputs["eraser"].setValue(100)
        
        # Initialize the delete input to -1, which means "no label".
        # Now changing this input to a positive value will cause label deletions.
        # (The deleteLabel input is monitored for changes.)
        self.opLabelArray.inputs["deleteLabel"].setValue(-1)

        ##
        # training
        ##
        # TODO: Replace these OpXToMulti operators with a MultiArrayPiper
#        opMultiL = Op5ToMulti( graph=self.graph )
#        opMultiL.inputs["Input0"].connect()
#
#        opMultiLblocks = Op5ToMulti( graph=self.graph )
#        opMultiLblocks.inputs["Input0"].connect()
        
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
        self.predict.inputs['LabelsCount'].connect(self.NumClasses)
        
        # 
        self.prediction_cache.name = "PredictionCache"
        self.prediction_cache.inputs["fixAtCurrent"].setValue(True)
        self.prediction_cache.inputs["innerBlockShape"].setValue(((1,256,256,1,2),(1,256,1,256,2),(1,1,256,256,2)))
        self.prediction_cache.inputs["outerBlockShape"].setValue(((1,256,256,4,2),(1,256,4,256,2),(1,4,256,256,2)))
        self.prediction_cache.inputs["Input"].connect(self.predict.outputs["PMaps"])

        # Default value for inputs
        self.NumClasses.setValue(0)

        # The prediction cache is the final stage our pipeline.
        # When it is configured, signal that the whole pipeline is configured
        #self.prediction_cache.notifyConfigured( self.pipelineConfiguredSignal.emit )
        
#        def emitPredictionMetaChangeSignal(slot):
#            """Closure to emit the prediction meta changed signal with the correct parameter."""
#            self.predictionMetaChangeSignal.emit( self.prediction_cache.configured() )
#        self.prediction_cache.outputs["Output"][0].notifyMetaChanged(emitPredictionMetaChangeSignal)
#    @property
#    def featureBoolMatrix(self):
#        return self.features.inputs['Matrix'].value
#    
#    @featureBoolMatrix.setter
#    def featureBoolMatrix(self, newMatrix):
#        self.features.inputs['Matrix'].setValue(newMatrix)
#        self.featuresChangedSignal.emit()
        
        def inputResizeHandler( slot, oldsize, newsize ):
            if ( newsize == 0 ):
                self.LabelImages.resize(0)
                self.NonzeroLabelBlocks.resize(0)
                self.PredictionProbabilities.resize(0)
                self.CachedPredictionProbabilities.resize(0)
        self.InputImages.notifyResized( inputResizeHandler )

        
    def setupOutputs(self):
        numImages = len(self.InputImages)
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

    def getSubOutSlot(self, slots, indexes, key, result):
        slot = slots[0]
        if slot.name == "PredictionProbabilities":
            req = self.predict.PMaps[indexes[0]][key].writeInto(result)
            return req.wait()
        elif slot.name == "CachedPredictionProbabilities":
            req = self.prediction_cache.Output[indexes[0]][key].writeInto(result)
            return req.wait()
        elif slot.name == "LabelImages":
            req = self.opLabelArray.Output[indexes[0]][key].writeInto(result)
            return req.wait()
        elif slot.name == "NonzeroLabelBlocks":
            req = self.opLabelArray.nonzeroBlocks[indexes[0]][key].writeInto(result)
            return req.wait()
        else:
            assert False, "Invalid output slot."
    
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
    
#    @property
#    def maxLabel(self):
#        """
#        Return the maximum number of labels the classifier can currently use.
#        """
#        return self.predict.inputs['LabelsCount'].value
#
#    def setMaxLabel(self, highestLabel):
#        """
#        Change the maximum number of label classes the prediction operator can handle.
#        """
#        # Count == highest label because 0 isn't a valid label
#        self.predict.inputs['LabelsCount'].setValue(highestLabel)


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


























