#Python
import copy
from functools import partial
import itertools
import math

#SciPy
import numpy
import vigra

#lazyflow
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.operators import OpBlockedSparseLabelArray, OpValueCache, \
                               OpArrayCache, OpMultiArraySlicer2, \
                               OpPrecomputedInput, OpPixelOperator, OpMaxChannelIndicatorOperator, \
                               Op5ifyer
from lazyflow.request import Request, RequestPool
from lazyflow.roi     import roiToSlice, sliceToRoi
                               
from ilastik.applets.counting.countingOperators import OpTrainCounter, OpPredictCounter, OpLabelPreviewer

#ilastik

from ilastik.utility.operatorSubView import OperatorSubView
from ilastik.utility import OpMultiLaneWrapper
import threading
from ilastik.applets.base.applet import DatasetConstraintError

class OpVolumeOperator(Operator):
    name = "OpVolumeOperator"
    description = "Do Operations involving the whole volume"
    inputSlots = [InputSlot("Input"), InputSlot("Function")]
    outputSlots = [OutputSlot("Output")]
    DefaultBlockSize = 128
    blockShape = InputSlot(value = DefaultBlockSize)

    def setupOutputs(self):
        testInput = numpy.ones((3,3))
        testFun = self.Function.value
        testOutput = testFun(testInput)

        self.outputs["Output"].meta.dtype = testOutput.dtype
        self.outputs["Output"].meta.shape = (1,)
        self.outputs["Output"].setDirty((slice(0,1,None),))
        self.cache = None
        self._lock = threading.Lock()


    def execute(self, slot, subindex, roi, result):
        with self._lock:
            if self.cache is None:
                fullBlockShape = numpy.array([self.blockShape.value for i in self.Input.meta.shape])
                fun = self.inputs["Function"].value
                #data = self.inputs["Input"][:].wait()
                #split up requests into blocks
                shape = self.Input.meta.shape
                numBlocks = numpy.ceil(shape/(1.0*fullBlockShape)).astype("int")
                blockCache = numpy.ndarray(shape = numpy.prod(numBlocks), dtype=self.Output.meta.dtype)
                pool = RequestPool()
                #blocks holds the different roi keys for each of the blocks
                blocks = itertools.product(*[range(i) for i in numBlocks])
                blockKeys = []
                for b in blocks:
                    start = b * fullBlockShape
                    stop = b * fullBlockShape + fullBlockShape
                    stop = numpy.min(numpy.vstack((stop, shape)), axis=0)
                    blockKey = roiToSlice(start, stop)
                    blockKeys.append(blockKey)
                
                def predict_block(i):
                    data = self.Input[blockKeys[i]].wait()
                    blockCache[i] = fun(data)
                    
                for i,f in enumerate(blockCache):
                    req = pool.request(partial(predict_block,i))

                pool.wait()
                pool.clean()

                self.cache = [fun(blockCache)]
            return self.cache

    def propagateDirty(self, slot, subindex, roi):
        key = roi.toSlice()
        if slot == self.Input or slot == self.Function:
            self.outputs["Output"].setDirty( slice(None) )
        self.cache = None

class OpUpperBound(Operator):
    name = "OpUpperBound"
    description = "Calculate the upper bound of the data for correct normalization of the output"
    inputSlots = [InputSlot("Sigma", stype = "float")]
    outputSlots = [OutputSlot("UpperBound")]

    def setupOutputs(self):
        self.UpperBound.meta.dtype = numpy.float32
        self.UpperBound.meta.shape = (1,)

    def execute(self, slot, subindex, roi, result):
            
        sigma = self.Sigma.value
        result[...] = 3 / (2 * math.pi * sigma**2)
        return result
    
    def propagateDirty(self, slot, subindex, roi):
        key = roi.toSlice()
        self.UpperBound.setDirty( key[:-1] )


class OpMean(Operator):

    name = "OpMean"
    description = "Calculate the mean of the Input"
    Input = InputSlot("Input")
    Output = OutputSlot("Output")

    def setupOutputs(self):

        self.Output.meta.assignFrom(self.Input.meta)

        taggedShape = self.Input.meta.getTaggedShape()
        taggedShape['c'] = 1
        self.Output.meta.shape = taggedShape.values()


    def execute(self, slot, subindex, roi, result):
        chanAxis = self.Input.meta.axistags.index('c')
        roi.stop[chanAxis] = self.Input.meta.getTaggedShape()['c']
        key = roi.toSlice()
        data = self.inputs["Input"][key].wait()
        result[..., 0] = numpy.mean(data, axis = 2)

    def propagateDirty(self, slot, subindex, roi):
        key = roi.toSlice()
        self.Output.setDirty( key[:-1] )

class OpCounting( Operator ):
    """
    Top-level operator for counting
    """
    name="OpCounting"
    category = "Top-level"
    
    # Graph inputs
    
    InputImages = InputSlot(level=1) # Original input data.  Used for display only.

    LabelInputs = InputSlot(optional = True, level=1) # Input for providing label data from an external source
    BoxLabelInputs = InputSlot(optional = True, level=1) # Input for providing label data from an external source
    LabelsAllowedFlags = InputSlot(stype='bool', level=1) # Specifies which images are permitted to be labeled 

    FeatureImages = InputSlot(level=1) # Computed feature images (each channel is a different feature)
    CachedFeatureImages = InputSlot(level=1) # Cached feature data.

    FreezePredictions = InputSlot(stype='bool')

    PredictionsFromDisk = InputSlot(optional=True, level=1)

    PredictionProbabilities = OutputSlot(level=1) # Classification predictions (via feature cache for interactive speed)

    #PredictionProbabilityChannels = OutputSlot(level=2) # Classification predictions, enumerated by channel
    #SegmentationChannels = OutputSlot(level=2) # Binary image of the final selections.
    
    MaxLabelValue = OutputSlot()
    LabelImages = OutputSlot(level=1) # Labels from the user
    BoxLabelImages= OutputSlot(level=1) # Input for providing label data from an external source
    NonzeroLabelBlocks = OutputSlot(level=1) # A list if slices that contain non-zero label values
    Classifier = OutputSlot() # We provide the classifier as an external output for other applets to use

    CachedPredictionProbabilities = OutputSlot(level=1) # Classification predictions (via feature cache AND prediction cache)

    HeadlessPredictionProbabilities = OutputSlot(level=1) # Classification predictions ( via no image caches (except for the classifier itself )
    #HeadlessUint8PredictionProbabilities = OutputSlot(level=1) # Same as above, but 0-255 uint8 instead of 0.0-1.0 float32

    UncertaintyEstimate = OutputSlot(level=1)

    # GUI-only (not part of the pipeline, but saved to the project)
    UpperBound = OutputSlot()
    LabelNames = OutputSlot()
    LabelColors = OutputSlot()
    PmapColors = OutputSlot()
    Density = OutputSlot(level=1)
    LabelPreview = OutputSlot(level=1)
    OutputSum = OutputSlot(level=1)

    def __init__( self, *args, **kwargs ):
        """
        Instantiate all internal operators and connect them together.
        """
        super(OpCounting, self).__init__(*args, **kwargs)
        
        # Default values for some input slots
        self.FreezePredictions.setValue(True)
        self.LabelNames.setValue( [] )
        self.LabelColors.setValue( [] )
        self.PmapColors.setValue( [] )

        # SPECIAL connection: The LabelInputs slot doesn't get it's data  
        #  from the InputImages slot, but it's shape must match.
        self.LabelInputs.connect( self.InputImages )
        self.BoxLabelInputs.connect( self.InputImages )

        # Hook up Labeling Pipeline
        self.opLabelPipeline = OpMultiLaneWrapper( OpLabelPipeline, parent=self )
        self.opLabelPipeline.RawImage.connect( self.InputImages )
        self.opLabelPipeline.LabelInput.connect( self.LabelInputs )
        self.opLabelPipeline.BoxLabelInput.connect( self.BoxLabelInputs )
        self.LabelImages.connect( self.opLabelPipeline.Output )
        self.NonzeroLabelBlocks.connect( self.opLabelPipeline.nonzeroBlocks )
                
        self.BoxLabelImages.connect( self.opLabelPipeline.BoxOutput)
        # Find the highest label in all the label images
        self.opMaxLabel = OpMaxValue( parent=self, graph=self.graph)
        self.opMaxLabel.Inputs.connect( self.opLabelPipeline.MaxLabel )
        self.MaxLabelValue.connect( self.opMaxLabel.Output )

        self.GetFore= OpMultiLaneWrapper(OpPixelOperator,parent = self)
        def conv(arr):
            numpy.place(arr, arr ==2, 0)
            return arr.astype(numpy.float)
        self.GetFore.Function.setValue(conv)
        self.GetFore.Input.connect(self.opLabelPipeline.Output)

        self.LabelPreviewer = OpMultiLaneWrapper(OpLabelPreviewer, parent = self)
        self.LabelPreviewer.Input.connect(self.GetFore.Output)

        self.LabelPreview.connect(self.LabelPreviewer.Output)


        # Hook up the Training operator
        self.opUpperBound = OpUpperBound( parent= self, graph= self.graph )
        self.UpperBound.connect(self.opUpperBound.UpperBound)
        self.opTrain = OpTrainCounter( parent=self, graph=self.graph )
        self.opTrain.inputs['ForegroundLabels'].connect( self.GetFore.Output)
        self.opTrain.inputs['BackgroundLabels'].connect( self.opLabelPipeline.Output)
        self.opTrain.inputs['Images'].connect( self.CachedFeatureImages )
        self.opTrain.inputs["nonzeroLabelBlocks"].connect( self.opLabelPipeline.nonzeroBlocks )
        self.opTrain.inputs['fixClassifier'].setValue( True )
        self.opTrain.inputs["UpperBound"].connect(self.UpperBound)

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
        #self.HeadlessUint8PredictionProbabilities.connect( self.opPredictionPipeline.HeadlessUint8PredictionProbabilities )
        #self.PredictionProbabilityChannels.connect( self.opPredictionPipeline.PredictionProbabilityChannels )
        #self.SegmentationChannels.connect( self.opPredictionPipeline.SegmentationChannels )
        self.UncertaintyEstimate.connect( self.opPredictionPipeline.UncertaintyEstimate )
        self.Density.connect(self.opPredictionPipeline.CachedPredictionProbabilities)
        

        
        
        self.opVolumeSum = OpMultiLaneWrapper(OpVolumeOperator,parent=self, graph = self.graph )
        self.opVolumeSum.Input.connect(self.Density)
        self.opVolumeSum.Function.setValue(numpy.sum)
        
        
        

        self.OutputSum.connect(self.opVolumeSum.Output)

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
                self._checkConstraints(index)
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
        
        
        self.options = self.opTrain.options

    def setupOutputs(self):
        self.LabelNames.meta.dtype = object
        self.LabelNames.meta.shape = (1,)
        self.LabelColors.meta.dtype = object
        self.LabelColors.meta.shape = (1,)
        self.PmapColors.meta.dtype = object
        self.PmapColors.meta.shape = (1,)


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
        self.BoxLabelInputs.resize(numImages)

        # Special case: We have to set up the shape of our label *input* according to our image input shape
        shapeList = list(self.InputImages[imageIndex].meta.shape)
        try:
            channelIndex = self.InputImages[imageIndex].meta.axistags.index('c')
            shapeList[channelIndex] = 1
        except:
            pass
        self.LabelInputs[imageIndex].meta.shape = tuple(shapeList)
        self.LabelInputs[imageIndex].meta.axistags = inputSlot.meta.axistags
        self.BoxLabelInputs[imageIndex].meta.shape = tuple(shapeList)
        self.BoxLabelInputs[imageIndex].meta.axistags = inputSlot.meta.axistags

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
        self.opTrain.BoxConstraintRois.resize(numLanes + 1)
        self.opTrain.BoxConstraintValues.resize(numLanes + 1)
        
    def removeLane(self, laneIndex, finalLength):
        self.InputImages.removeSlot(laneIndex, finalLength)
        self.opTrain.BoxConstraintRois.removeSlot(laneIndex, finalLength)
        self.opTrain.BoxConstraintValues.removeSlot(laneIndex, finalLength)

    def getLane(self, laneIndex):
        return OperatorSubView(self, laneIndex)
    
    def _checkConstraints(self, laneIndex):
        """
        Ensure that all input images must be 2D and have the same number of channels
        """
        
        
        thisLaneTaggedShape = self.InputImages[laneIndex].meta.getTaggedShape()
        
        if thisLaneTaggedShape.has_key('z'):
            raise DatasetConstraintError(
                "Objects Counting Workflow",
                "All input images must be 2D (they cannot contain the z dimension).  "\
                "Your new image has {} z dimension"\
                .format( thisLaneTaggedShape['z']))
                # Find a different lane and use it for comparison
        
        if thisLaneTaggedShape.has_key('t'):
            raise DatasetConstraintError(
                "Objects Counting Workflow",
                "All input images must be 2D (they cannot contain the t dimension).  "\
                "Your new image has {} t dimension"\
                .format( thisLaneTaggedShape['t']))
                # Find a different lane and use it for comparison
        
        validShape = thisLaneTaggedShape
        for i, slot in enumerate(self.InputImages):
            if slot.ready() and i != laneIndex:
                validShape = slot.meta.getTaggedShape()
                break
        
        if len(validShape) != len(thisLaneTaggedShape):
            raise DatasetConstraintError(
                 "Objects Couting Workflow Counting",
                 "All input images must have the same dimensionality.  "\
                 "Your new image has {} dimensions (including channel), but your other images have {} dimensions."\
                 .format( len(thisLaneTaggedShape), len(validShape) ) )
            
        if validShape['c'] != thisLaneTaggedShape['c']:
            raise DatasetConstraintError(
                 "Objects Counting Workflow",
                 "All input images must have the same number of channels.  "\
                 "Your new image has {} channel(s), but your other images have {} channel(s)."\
                 .format( thisLaneTaggedShape['c'], validShape['c'] ) )
        
        

class OpLabelPipeline( Operator ):
    RawImage = InputSlot()
    LabelInput = InputSlot()
    BoxLabelInput = InputSlot() 
    Output = OutputSlot()
    nonzeroBlocks = OutputSlot()
    MaxLabel = OutputSlot()
    BoxOutput = OutputSlot()
    
    def __init__(self, *args, **kwargs):
        super( OpLabelPipeline, self ).__init__( *args, **kwargs )
        self.opInputShapeReader = OpShapeReader( parent=self )
        self.opInputShapeReader.Input.connect( self.RawImage )
        
        self.opLabelArray = OpBlockedSparseLabelArray( parent=self )
        self.opLabelArray.Input.connect( self.LabelInput )
        self.opLabelArray.shape.connect( self.opInputShapeReader.OutputShape )
        self.opLabelArray.eraser.setValue(100)

        self.opBoxArray = OpBlockedSparseLabelArray( parent = self)
        self.opBoxArray.Input.connect(self.BoxLabelInput)
        self.opBoxArray.shape.connect( self.opInputShapeReader.OutputShape )
        self.opBoxArray.eraser.setValue(100)

        # Initialize the delete input to -1, which means "no label".
        # Now changing this input to a positive value will cause label deletions.
        # (The deleteLabel input is monitored for changes.)
        self.opLabelArray.deleteLabel.setValue(-1)

        # Connect external outputs to their internal sources
        self.Output.connect( self.opLabelArray.Output )
        self.nonzeroBlocks.connect( self.opLabelArray.nonzeroBlocks )
        self.MaxLabel.connect( self.opLabelArray.maxLabel )
        self.BoxOutput.connect( self.opBoxArray.Output )
    


    def setupOutputs(self):
        taggedShape = self.RawImage.meta.getTaggedShape()
        blockDims = { 't' : 1, 'x' : 64, 'y' : 64, 'z' : 64, 'c' : 1 }
        blockDims = dict( filter( lambda (k,v): k in taggedShape, blockDims.items() ) )
        taggedShape.update( blockDims )
        self.opLabelArray.blockShape.setValue( tuple( taggedShape.values() ) )
        self.opBoxArray.blockShape.setValue( tuple( taggedShape.values() ) )

    def setInSlot(self, slot, subindex, roi, value):
        # Nothing to do here: All inputs that support __setitem__
        #   are directly connected to internal operators.
        pass

    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here.  Output is assigned a value in setupOutputs()"

    def propagateDirty(self, slot, subindex, roi):
        # Our output changes when the input changed shape, not when it becomes dirty.
        pass    

class OpPredictionPipelineNoCache(Operator):
    """
    This contains only the cacheless parts of the prediction pipeline, for easy use in headless workflows.
    """
    FeatureImages = InputSlot()
    MaxLabel = InputSlot()
    Classifier = InputSlot()
    FreezePredictions = InputSlot()
    PredictionsFromDisk = InputSlot( optional=True )
    
    HeadlessPredictionProbabilities = OutputSlot() # drange is 0.0 to 1.0
    #HeadlessUint8PredictionProbabilities = OutputSlot() # drange 0 to 255

    def __init__(self, *args, **kwargs):
        super( OpPredictionPipelineNoCache, self ).__init__( *args, **kwargs )

        # Random forest prediction using the raw feature image slot (not the cached features)
        # This would be bad for interactive labeling, but it's good for headless flows 
        #  because it avoids the overhead of cache.        
        self.cacheless_predict = OpPredictCounter( parent=self )
        self.cacheless_predict.name = "OpPredictCounter (Cacheless Path)"
        self.cacheless_predict.inputs['Classifier'].connect(self.Classifier) 
        self.cacheless_predict.inputs['Image'].connect(self.FeatureImages) # <--- Not from cache
        self.cacheless_predict.inputs['LabelsCount'].connect(self.MaxLabel)
        self.meaner = OpMean(parent = self)
        self.meaner.Input.connect(self.cacheless_predict.PMaps)
        self.HeadlessPredictionProbabilities.connect(self.meaner.Output)


        # Alternate headless output: uint8 instead of float.
        # Note that drange is automatically updated.        
        #self.opConvertToUint8 = OpPixelOperator( parent=self )
        #self.opConvertToUint8.Input.connect( self.cacheless_predict.PMaps )
        #self.opConvertToUint8.Function.setValue( lambda a: (255*a).astype(numpy.uint8) )
        #self.HeadlessUint8PredictionProbabilities.connect( self.opConvertToUint8.Output )

    def setupOutputs(self):
        pass

    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here.  Output is assigned a value in setupOutputs()"

    def propagateDirty(self, slot, subindex, roi):
        # Our output changes when the input changed shape, not when it becomes dirty.
        pass

class OpPredictionPipeline(OpPredictionPipelineNoCache):
    """
    This operator extends the cacheless prediction pipeline above with additional outputs for the GUI.
    (It uses caches for these outputs, and has an extra input for cached features.)
    """        
    CachedFeatureImages = InputSlot()

    PredictionProbabilities = OutputSlot()
    CachedPredictionProbabilities = OutputSlot()
    UncertaintyEstimate = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpPredictionPipeline, self).__init__( *args, **kwargs )

        # Random forest prediction using CACHED features.
        self.predict = OpPredictCounter( parent=self )
        self.predict.name = "OpPredictCounter"
        self.predict.inputs['Classifier'].connect(self.Classifier) 
        self.predict.inputs['Image'].connect(self.CachedFeatureImages)
        self.predict.inputs['LabelsCount'].connect(self.MaxLabel)
        self.PredictionProbabilities.connect( self.predict.PMaps )

        # Prediction cache for the GUI
        self.prediction_cache_gui = OpArrayCache( parent=self )
        self.prediction_cache_gui.name = "prediction_cache_gui"
        self.prediction_cache_gui.inputs["fixAtCurrent"].connect( self.FreezePredictions )
        self.prediction_cache_gui.inputs["Input"].connect( self.predict.PMaps )
        self.prediction_cache_gui.blockShape.setValue(128)
        
        ## Also provide each prediction channel as a separate layer (for the GUI)
        self.opUncertaintyEstimator = OpEnsembleMargin( parent=self )
        self.opUncertaintyEstimator.Input.connect( self.prediction_cache_gui.Output )

        ## Cache the uncertainty so we get zeros for uncomputed points
        self.opUncertaintyCache = OpArrayCache( parent=self )
        self.opUncertaintyCache.name = "opUncertaintyCache"
        self.opUncertaintyCache.blockShape.setValue(128)
        self.opUncertaintyCache.Input.connect( self.opUncertaintyEstimator.Output )
        self.opUncertaintyCache.fixAtCurrent.connect( self.FreezePredictions )
        self.UncertaintyEstimate.connect( self.opUncertaintyCache.Output )
        
        self.meaner = OpMean(parent = self)
        self.meaner.Input.connect(self.prediction_cache_gui.Output)

        self.precomputed_predictions_gui = OpPrecomputedInput( parent=self )
        self.precomputed_predictions_gui.name = "precomputed_predictions_gui"
        self.precomputed_predictions_gui.SlowInput.connect( self.meaner.Output )
        self.precomputed_predictions_gui.PrecomputedInput.connect( self.PredictionsFromDisk )
        self.CachedPredictionProbabilities.connect(self.precomputed_predictions_gui.Output)


    def setupOutputs(self):
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
        taggedShape = self.Input.meta.getTaggedShape()

    def execute(self, slot, subindex, roi, result):
        roi = copy.copy(roi)
        taggedShape = self.Input.meta.getTaggedShape()
        chanAxis = self.Input.meta.axistags.index('c')
        roi.start[chanAxis] = 0
        roi.stop[chanAxis] = taggedShape['c']
        pmap = self.Input.get(roi).wait()
        
        pmap_sort = numpy.sort(pmap, axis=self.Input.meta.axistags.index('c')).view(vigra.VigraArray)
        pmap_sort.axistags = self.Input.meta.axistags

        res = pmap_sort.bindAxis('c', -1) - pmap_sort.bindAxis('c', -2)
        res = res.withAxes( *taggedShape.keys() ).view(numpy.ndarray)
        result[...] = res
        return result 

    def propagateDirty(self, inputSlot, subindex, roi):
        chanAxis = self.Input.meta.axistags.index('c')
        roi.start[chanAxis] = 0
        roi.stop[chanAxis] = 1
        self.Output.setDirty( roi )
