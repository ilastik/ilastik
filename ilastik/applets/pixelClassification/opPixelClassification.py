from functools import partial
import numpy
import vigra
from lazyflow.graph import Operator, InputSlot, OutputSlot, OperatorWrapper
from ilastik.utility.operatorSubView import OperatorSubView

from ilastik.utility import OpMultiLaneWrapper

from lazyflow.operators import OpBlockedSparseLabelArray, OpValueCache, OpTrainRandomForestBlocked, \
                               OpPredictRandomForest, OpSlicedBlockedArrayCache, OpMultiArraySlicer2, OpPrecomputedInput, OpPixelOperator

class OpPixelClassification( Operator ):
    """
    Top-level operator for the 
    """
    name="OpPixelClassification"
    category = "Top-level"
    
    # Graph inputs
    
    InputImages = InputSlot(level=1) # Original input data.  Used for display only.

    LabelInputs = InputSlot(optional = True, level=1) # Input for providing label data from an external source
    LabelsAllowedFlags = InputSlot(stype='bool', level=1) # Specifies which images are permitted to be labeled 

    FeatureImages = InputSlot(level=1) # Computed feature images (each channel is a different feature)
    CachedFeatureImages = InputSlot(level=1) # Cached feature data.

    FreezePredictions = InputSlot(stype='bool')

    PredictionsFromDisk = InputSlot(optional=True, level=1)

    PredictionProbabilities = OutputSlot(level=1) # Classification predictions (via feature cache for interactive speed)

    PredictionProbabilityChannels = OutputSlot(level=2) # Classification predictions, enumerated by channel
    SegmentationChannels = OutputSlot(level=2) # Binary image of the final selections.
    
    MaxLabelValue = OutputSlot()
    LabelImages = OutputSlot(level=1) # Labels from the user
    NonzeroLabelBlocks = OutputSlot(level=1) # A list if slices that contain non-zero label values
    Classifier = OutputSlot() # We provide the classifier as an external output for other applets to use

    CachedPredictionProbabilities = OutputSlot(level=1) # Classification predictions (via feature cache AND prediction cache)

    HeadlessPredictionProbabilities = OutputSlot(level=1) # Classification predictions ( via no image caches (except for the classifier itself )
    HeadlessUint8PredictionProbabilities = OutputSlot(level=1) # Same as above, but 0-255 uint8 instead of 0.0-1.0 float32

    UncertaintyEstimate = OutputSlot(level=1)

    # GUI-only (not part of the pipeline, but saved to the project)
    LabelNames = OutputSlot()
    LabelColors = OutputSlot()
    PmapColors = OutputSlot()

    def __init__( self, *args, **kwargs ):
        """
        Instantiate all internal operators and connect them together.
        """
        super(OpPixelClassification, self).__init__(*args, **kwargs)
        
        # Default values for some input slots
        self.FreezePredictions.setValue(True)
        self.LabelNames.setValue( [] )
        self.LabelColors.setValue( [] )
        self.PmapColors.setValue( [] )

        # SPECIAL connection: The LabelInputs slot doesn't get it's data  
        #  from the InputImages slot, but it's shape must match.
        self.LabelInputs.connect( self.InputImages )

        # Hook up Labeling Pipeline
        self.opLabelPipeline = OpMultiLaneWrapper( OpLabelPipeline, parent=self )
        self.opLabelPipeline.RawImage.connect( self.InputImages )
        self.opLabelPipeline.LabelInput.connect( self.LabelInputs )
        self.LabelImages.connect( self.opLabelPipeline.Output )
        self.NonzeroLabelBlocks.connect( self.opLabelPipeline.nonzeroBlocks )
                
        # Find the highest label in all the label images
        self.opMaxLabel = OpMaxValue( parent=self, graph=self.graph)
        self.opMaxLabel.Inputs.connect( self.opLabelPipeline.MaxLabel )
        self.MaxLabelValue.connect( self.opMaxLabel.Output )

        # Hook up the Training operator
        self.opTrain = OpTrainRandomForestBlocked( parent=self, graph=self.graph )
        self.opTrain.inputs['Labels'].connect( self.opLabelPipeline.Output )
        self.opTrain.inputs['Images'].connect( self.CachedFeatureImages )
        self.opTrain.inputs["nonzeroLabelBlocks"].connect( self.opLabelPipeline.nonzeroBlocks )
        self.opTrain.inputs['fixClassifier'].setValue( False )

        # Hook up the Classifier Cache
        # The classifier is cached here to allow serializers to force in
        #   a pre-calculated classifier (loaded from disk)
        self.classifier_cache = OpValueCache( parent=self, graph=self.graph )
        self.classifier_cache.inputs["Input"].connect(self.opTrain.outputs['Classifier'])
        self.Classifier.connect( self.classifier_cache.Output )

        # Hook up the prediction pipeline inputs
        self.opPredictionPipeline = OpMultiLaneWrapper( OpPredictionPipeline, parent=self )
        self.opPredictionPipeline.FeatureImages.connect( self.FeatureImages )
        self.opPredictionPipeline.CachedFeatureImages.connect( self.CachedFeatureImages )
        self.opPredictionPipeline.MaxLabel.connect( self.opMaxLabel.Output )
        self.opPredictionPipeline.Classifier.connect( self.classifier_cache.Output )
        self.opPredictionPipeline.FreezePredictions.connect( self.FreezePredictions )
        self.opPredictionPipeline.PredictionsFromDisk.connect( self.PredictionsFromDisk )

        # Prediction pipeline outputs -> Top-level outputs
        self.PredictionProbabilities.connect( self.opPredictionPipeline.PredictionProbabilities )
        self.CachedPredictionProbabilities.connect( self.opPredictionPipeline.CachedPredictionProbabilities )
        self.HeadlessPredictionProbabilities.connect( self.opPredictionPipeline.HeadlessPredictionProbabilities )
        self.HeadlessUint8PredictionProbabilities.connect( self.opPredictionPipeline.HeadlessUint8PredictionProbabilities )
        self.PredictionProbabilityChannels.connect( self.opPredictionPipeline.PredictionProbabilityChannels )
        self.SegmentationChannels.connect( self.opPredictionPipeline.SegmentationChannels )
        self.UncertaintyEstimate.connect( self.opPredictionPipeline.UncertaintyEstimate )

        def inputResizeHandler( slot, oldsize, newsize ):
            if ( newsize == 0 ):
                self.LabelImages.resize(0)
                self.NonzeroLabelBlocks.resize(0)
                self.PredictionProbabilities.resize(0)
                self.CachedPredictionProbabilities.resize(0)
        self.InputImages.notifyResized( inputResizeHandler )

        # Debug assertions: Check to make sure the non-wrapped operators stayed that way.
        assert self.opMaxLabel.Inputs.operator == self.opMaxLabel
        assert self.opTrain.Images.operator == self.opTrain

        def handleNewInputImage( multislot, index, *args ):
            def handleInputReady(slot):
                self.setupCaches( multislot.index(slot) )
            multislot[index].notifyReady(handleInputReady)
                
        self.InputImages.notifyInserted( handleNewInputImage )

        # All input multi-slots should be kept in sync
        # Output multi-slots will auto-sync via the graph
        multiInputs = filter( lambda s: s.level >= 1, self.inputs.values() )
        for s1 in multiInputs:
            for s2 in multiInputs:
                if s1 != s2:
                    def insertSlot( a, b, position, finalsize ):
                        a.insertSlot(position, finalsize)
                    s1.notifyInserted( partial(insertSlot, s2 ) )
                    
                    def removeSlot( a, b, position, finalsize ):
                        a.removeSlot(position, finalsize)
                    s1.notifyRemoved( partial(removeSlot, s2 ) )

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
        shapeList = list(self.InputImages[imageIndex].meta.shape)
        try:
            channelIndex = self.InputImages[imageIndex].meta.axistags.index('c')
            shapeList[channelIndex] = 1
        except:
            pass
        self.LabelInputs[imageIndex].meta.shape = tuple(shapeList)
        self.LabelInputs[imageIndex].meta.axistags = inputSlot.meta.axistags

    def setInSlot(self, slot, subindex, roi, value):
        # Nothing to do here: All inputs that support __setitem__
        #   are directly connected to internal operators.
        pass

    def propagateDirty(self, slot, subindex, roi):
        # Nothing to do here: All outputs are directly connected to 
        #  internal operators that handle their own dirty propagation.
        pass

    def addLane(self, laneIndex):
        numLanes = len(self.InputImages)
        assert numLanes == laneIndex, "Image lanes must be appended."        
        self.InputImages.resize(numLanes+1)
        
    def removeLane(self, laneIndex, finalLength):
        self.InputImages.removeSlot(laneIndex, finalLength)

    def getLane(self, laneIndex):
        return OperatorSubView(self, laneIndex)

class OpLabelPipeline( Operator ):
    RawImage = InputSlot()
    LabelInput = InputSlot()
    
    Output = OutputSlot()
    nonzeroBlocks = OutputSlot()
    MaxLabel = OutputSlot()
    
    def __init__(self, *args, **kwargs):
        super( OpLabelPipeline, self ).__init__( *args, **kwargs )
        self.opInputShapeReader = OpShapeReader( parent=self )
        self.opInputShapeReader.Input.connect( self.RawImage )
        
        self.opLabelArray = OpBlockedSparseLabelArray( parent=self )
        self.opLabelArray.Input.connect( self.LabelInput )
        self.opLabelArray.shape.connect( self.opInputShapeReader.OutputShape )
        self.opLabelArray.eraser.setValue(100)

        # Initialize the delete input to -1, which means "no label".
        # Now changing this input to a positive value will cause label deletions.
        # (The deleteLabel input is monitored for changes.)
        self.opLabelArray.deleteLabel.setValue(-1)

        # Connect external outputs to their internal sources
        self.Output.connect( self.opLabelArray.Output )
        self.nonzeroBlocks.connect( self.opLabelArray.nonzeroBlocks )
        self.MaxLabel.connect( self.opLabelArray.maxLabel )
    
    def setupOutputs(self):
        taggedShape = self.RawImage.meta.getTaggedShape()
        blockDims = { 't' : 1, 'x' : 64, 'y' : 64, 'z' : 64, 'c' : 1 }
        blockDims = dict( filter( lambda (k,v): k in taggedShape, blockDims.items() ) )
        taggedShape.update( blockDims )
        self.opLabelArray.blockShape.setValue( tuple( taggedShape.values() ) )

    def setInSlot(self, slot, subindex, roi, value):
        # Nothing to do here: All inputs that support __setitem__
        #   are directly connected to internal operators.
        pass

    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here.  Output is assigned a value in setupOutputs()"

    def propagateDirty(self, slot, subindex, roi):
        # Our output changes when the input changed shape, not when it becomes dirty.
        pass

class OpPredictionPipeline(Operator):
    FeatureImages = InputSlot()
    CachedFeatureImages = InputSlot()
    MaxLabel = InputSlot()
    Classifier = InputSlot()
    FreezePredictions = InputSlot()
    PredictionsFromDisk = InputSlot( optional=True )
    
    PredictionProbabilities = OutputSlot()
    CachedPredictionProbabilities = OutputSlot()
    HeadlessPredictionProbabilities = OutputSlot() # drange is 0.0 to 1.0
    HeadlessUint8PredictionProbabilities = OutputSlot() # drange 0 to 255

    PredictionProbabilityChannels = OutputSlot( level=1 )
    SegmentationChannels = OutputSlot( level=1 )
    UncertaintyEstimate = OutputSlot()

    def __init__(self, *args, **kwargs):
        super( OpPredictionPipeline, self ).__init__( *args, **kwargs )
        
        self.predict = OpPredictRandomForest( parent=self )
        self.predict.name = "OpPredictRandomForest"
        self.prediction_cache = OpSlicedBlockedArrayCache( parent=self )
        self.prediction_cache.name = "prediction_cache"
        self.prediction_cache_gui = OpSlicedBlockedArrayCache( parent=self )
        self.prediction_cache_gui.name = "prediction_cache_gui"
        self.precomputed_predictions = OpPrecomputedInput( parent=self )
        self.precomputed_predictions.name = "precomputed_predictions"
        self.precomputed_predictions_gui = OpPrecomputedInput( parent=self )
        self.precomputed_predictions_gui.name = "precomputed_predictions_gui"

        ##
        # 
        ##
        self.predict.inputs['Classifier'].connect(self.Classifier) 
        self.predict.inputs['Image'].connect(self.CachedFeatureImages)
        self.predict.inputs['LabelsCount'].connect(self.MaxLabel)
        self.PredictionProbabilities.connect( self.predict.PMaps )
        
        # prediction cache for downstream operators (if they want it)
        self.prediction_cache.inputs["fixAtCurrent"].setValue(False)
        self.prediction_cache.inputs["Input"].connect( self.predict.PMaps )

        # The serializer uses these operators to provide prediction data directly from the project file
        # if the predictions haven't become dirty since the project file was opened.
        self.precomputed_predictions.SlowInput.connect( self.prediction_cache.Output )
        self.precomputed_predictions.PrecomputedInput.connect( self.PredictionsFromDisk )
        self.CachedPredictionProbabilities.connect( self.precomputed_predictions.Output )

        # Prediction cache for the GUI
        self.prediction_cache_gui.inputs["fixAtCurrent"].connect( self.FreezePredictions )
        self.prediction_cache_gui.inputs["Input"].connect( self.predict.PMaps )

        self.precomputed_predictions_gui.SlowInput.connect( self.prediction_cache_gui.Output )
        self.precomputed_predictions_gui.PrecomputedInput.connect( self.PredictionsFromDisk )

        # CACHELESS FLOW (Don't pass through feature cache)
        #  This is terrible for interactive labeling, but fast for command-line predictions.
        self.cacheless_predict = OpPredictRandomForest( parent=self )
        self.cacheless_predict.name = "OpPredictRandomForest (Cacheless Path)"
        self.cacheless_predict.inputs['Classifier'].connect(self.Classifier) 
        self.cacheless_predict.inputs['Image'].connect(self.FeatureImages) # <--- Not from cache
        self.cacheless_predict.inputs['LabelsCount'].connect(self.MaxLabel)

        self.HeadlessPredictionProbabilities.connect(self.cacheless_predict.PMaps)

        # Alternate headless output: uint8 instead of float.
        # Note that drange is automatically updated.        
        self.opConvertToUint8 = OpPixelOperator( parent=self )
        self.opConvertToUint8.Input.connect( self.cacheless_predict.PMaps )
        self.opConvertToUint8.Function.setValue( lambda a: (255*a).astype(numpy.uint8) )
        self.HeadlessUint8PredictionProbabilities.connect( self.opConvertToUint8.Output )

        # Also provide each prediction channel as a separate layer (for the GUI)
        self.opPredictionSlicer = OpMultiArraySlicer2( parent=self )
        self.opPredictionSlicer.name = "opPredictionSlicer"
        self.opPredictionSlicer.Input.connect( self.precomputed_predictions_gui.Output )
        self.opPredictionSlicer.AxisFlag.setValue('c')
        self.PredictionProbabilityChannels.connect( self.opPredictionSlicer.Slices )
        
        self.opSegementor = OpPixelOperator( parent=self )
        self.opSegementor.Input.connect( self.precomputed_predictions_gui.Output )
        self.opSegementor.Function.setValue( lambda x: numpy.where(x < 0.5, 0, 1) )

        self.opSegmentationSlicer = OpMultiArraySlicer2( parent=self )
        self.opSegmentationSlicer.name = "opSegmentationSlicer"
        self.opSegmentationSlicer.Input.connect( self.opSegementor.Output )
        self.opSegmentationSlicer.AxisFlag.setValue('c')
        self.SegmentationChannels.connect( self.opSegmentationSlicer.Slices )

        # Create a layer for uncertainty estimate
        self.opUncertaintyEstimator = OpEnsembleMargin( parent=self )
        self.opUncertaintyEstimator.Input.connect( self.precomputed_predictions_gui.Output )

        # Cache the uncertainty so we get zeros for uncomputed points
        self.opUncertaintyCache = OpSlicedBlockedArrayCache( parent=self )
        self.opUncertaintyCache.name = "opUncertaintyCache"
        self.opUncertaintyCache.Input.connect( self.opUncertaintyEstimator.Output )
        self.opUncertaintyCache.fixAtCurrent.connect( self.FreezePredictions )
        self.UncertaintyEstimate.connect( self.opUncertaintyCache.Output )
        
    def setupOutputs(self):
        # Set the blockshapes for each input image separately, depending on which axistags it has.
        axisOrder = [ tag.key for tag in self.FeatureImages.meta.axistags ]

        blockDimsX = { 't' : (1,1),
                       'z' : (128,256),
                       'y' : (128,256),
                       'x' : (1,1),
                       'c' : (100, 100) }

        blockDimsY = { 't' : (1,1),
                       'z' : (128,256),
                       'y' : (1,1),
                       'x' : (128,256),
                       'c' : (100,100) }

        blockDimsZ = { 't' : (1,1),
                       'z' : (1,1),
                       'y' : (128,256),
                       'x' : (128,256),
                       'c' : (100,100) }

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

        self.opUncertaintyCache.inputs["innerBlockShape"].setValue( (innerBlockShapeX, innerBlockShapeY, innerBlockShapeZ) )
        self.opUncertaintyCache.inputs["outerBlockShape"].setValue( (outerBlockShapeX, outerBlockShapeY, outerBlockShapeZ) )


    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here.  Output is assigned a value in setupOutputs()"

    def propagateDirty(self, slot, subindex, roi):
        # Our output changes when the input changed shape, not when it becomes dirty.
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
    
    def setInSlot(self, slot, subindex, roi, value):
        pass

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

class OpEnsembleMargin(Operator):
    """
    Produces a pixelwise measure of the uncertainty of the pixelwise predictions.
    """
    Input = InputSlot()
    Output = OutputSlot()

    def setupOutputs(self):
        self.Output.meta.assignFrom(self.Input.meta)

        taggedShape = self.Input.meta.getTaggedShape()
        taggedShape['c'] = 1
        self.Output.meta.shape = taggedShape.values()

    def execute(self, slot, subindex, roi, result):
        taggedShape = self.Input.meta.getTaggedShape()
        chanAxis = self.Input.meta.axistags.index('c')
        roi.start[chanAxis] = 0
        roi.stop[chanAxis] = taggedShape['c']
        pmap = self.Input.get(roi).wait()
        
        pmap_sort = numpy.sort(pmap, axis=self.Input.meta.axistags.index('c')).view(vigra.VigraArray)
        pmap_sort.axistags = self.Input.meta.axistags

        res = pmap_sort.bindAxis('c', -1) - pmap_sort.bindAxis('c', -2)
        res = res.withAxes( *taggedShape.keys() ).view(numpy.ndarray)
        return (1-res)

    def propagateDirty(self, inputSlot, subindex, roi):
        chanAxis = self.Input.meta.axistags.index('c')
        roi.start[chanAxis] = 0
        roi.stop[chanAxis] = 1
        self.Output.setDirty( roi )


























