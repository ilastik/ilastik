from lazyflow.graph import Operator, InputSlot, OutputSlot, MultiInputSlot, MultiOutputSlot

from lazyflow.operators import OpPixelFeaturesPresmoothed, OpBlockedArrayCache, OpArrayPiper, Op5ToMulti, OpBlockedSparseLabelArray, OpArrayCache, \
                               OpTrainRandomForestBlocked, OpPredictRandomForest, OpSlicedBlockedArrayCache

from utility.simpleSignal import SimpleSignal
import numpy

class OpPixelClassification( object ):
    """
    Represents the pipeline of pixel classification operations.
    Implemented as a composite operator so it can serve an applet "top-level" operator.
    """
    name="OpPixelClassification"
    category = "Top-level"
    
    # Graph inputs
    inputSlots = [
      # A matrix of bool values representing the features and scales 
      #  to provide to the classifier.
      # Format of the matrix is hardcoded for now.
       InputSlot("FeatureMatrix"), 
       
       # The raw input image data
       MultiInputSlot("InputImages"),
       
       # The user-provided label data associated with each image.
       # Must consist of consecutive label values, starting with 1.
       # (Zero represents no label for that pixel.)
       # Shapes must match the input image shapes.n
       MultiInputSlot("Labels"),
       
       # The value of the highest label in the label data.
       InputSlot("MaxLabelValue")
    ]
    
    # Graph Outputs
    outputSlots = [
       # The computed feature images that were provided to the classifier.
       # (Useful for display purposes.)
       MultiOutputSlot("Features"),
       
       # The probability maps for each label class after classification.
       MultiOutputSlot("PredictionProbabilities")
   ]

    @property
    def graph(self):
        return self._graph

    def __init__( self, pipelineGraph ):
        """
        Instantiate all internal operators and connect them together.
        """
        self._graph = pipelineGraph
        
        ## Signals (non-qt) ##
        self.inputDataChangedSignal = SimpleSignal()     # Input data loaded/changed
#        self.featuresChangedSignal = SimpleSignal()      # New/changed feature selections
        self.labelsChangedSignal = SimpleSignal()        # New/changed label data
        self.pipelineConfiguredSignal = SimpleSignal()   # Pipeline is fully configured (all inputs are connected and have data)
        self.predictionMetaChangeSignal = SimpleSignal() # The prediction cache has changed its shape (or dtype).
                                                         #  The prediction cache's output configuration status is passed as the parameter.
                
        #The old ilastik provided the following scale names:
        #['Tiny', 'Small', 'Medium', 'Large', 'Huge', 'Megahuge', 'Gigahuge']
        #The corresponding scales are:
        feature_scales = [0.3, 0.7, 1, 1.6, 3.5, 5.0, 10.0]

        ##
        # IO
        ##
        self.images = Op5ToMulti( self.graph )
        self.features = OpPixelFeaturesPresmoothed( self.graph )
        self.features_cache = OpBlockedArrayCache( self.graph )
        self.labels = OpBlockedSparseLabelArray( self.graph )                                

        self.features.inputs["Input"].connect(self.images.outputs["Outputs"])
        self.features.inputs["Scales"].setValue( feature_scales )        
        print self.features.inputs["Scales"]
        assert self.features.Scales.configured() , " features.Scales not configured because _value=%r, meta.shape = %r" % (self.features.Scales._value,self.features.Scales.meta.shape )
        self.features_cache.inputs["Input"].connect(self.features.outputs["Output"])
        self.features_cache.inputs["innerBlockShape"].setValue((1,32,32,32,16))
        self.features_cache.inputs["outerBlockShape"].setValue((1,128,128,128,64))
        self.features_cache.inputs["fixAtCurrent"].setValue(False)  
    
        self.labels.inputs["blockShape"].setValue((1, 32, 32, 32, 1))
        self.labels.inputs["eraser"].setValue(100)    

        ##
        ## Entry point to the pipeline: 
        ## self.images.inputs["Input0"].connect(array_like_input)
        ## shape = array_like_input.meta.shape
        ## self.labels.inputs["shape"].setValue(shape[:-1] + (1,))
        ##


        
        ##
        # training
        ##
        opMultiL = Op5ToMulti( self.graph )    
        opMultiL.inputs["Input0"].connect(self.labels.outputs["Output"])

        opMultiLblocks = Op5ToMulti( self.graph )
        opMultiLblocks.inputs["Input0"].connect(self.labels.outputs["nonzeroBlocks"])
        train = OpTrainRandomForestBlocked( self.graph )
        train.inputs['Labels'].connect(opMultiL.outputs["Outputs"])
        train.inputs['Images'].connect(self.features_cache.outputs["Output"])
        train.inputs["nonzeroLabelBlocks"].connect(opMultiLblocks.outputs["Outputs"])
        train.inputs['fixClassifier'].setValue(False)
        self.train = train

        self.classifier_cache = OpArrayCache( self.graph )
        self.classifier_cache.inputs["Input"].connect(train.outputs['Classifier'])


        ##
        # prediction
        ##
        self.predict=OpPredictRandomForest( self.graph )
        self.predict.inputs['Classifier'].connect(self.classifier_cache.outputs['Output']) 
        self.predict.inputs['Image'].connect(self.features.outputs["Output"])

        pCache = OpSlicedBlockedArrayCache( self.graph )
        pCache.name = "PredictionCache"
        pCache.inputs["fixAtCurrent"].setValue(True)
        pCache.inputs["innerBlockShape"].setValue(((1,256,256,1,2),(1,256,1,256,2),(1,1,256,256,2)))
        pCache.inputs["outerBlockShape"].setValue(((1,256,256,4,2),(1,256,4,256,2),(1,4,256,256,2)))
        pCache.inputs["Input"].connect(self.predict.outputs["PMaps"])
        self.prediction_cache = pCache

        # The prediction cache is the final stage our pipeline.
        # When it is configured, signal that the whole pipeline is configured
        #self.prediction_cache.notifyConfigured( self.pipelineConfiguredSignal.emit )
        
        def emitPredictionMetaChangeSignal(slot):
            """Closure to emit the prediction meta changed signal with the correct parameter."""
            self.predictionMetaChangeSignal.emit( self.prediction_cache.configured() )
        self.prediction_cache.outputs["Output"][0].notifyMetaChanged(emitPredictionMetaChangeSignal)
#    @property
#    def featureBoolMatrix(self):
#        return self.features.inputs['Matrix'].value
#    
#    @featureBoolMatrix.setter
#    def featureBoolMatrix(self, newMatrix):
#        self.features.inputs['Matrix'].setValue(newMatrix)
#        self.featuresChangedSignal.emit()
        
    def getUniqueLabels(self):
        return numpy.unique(numpy.asarray(self.labels.outputs["nonzeroValues"][:].allocate().wait()[0]))

    def setInputData(self, inputProvider):
        """
        Set the pipeline input data, which is given as an operator in inputProvider.
        """
        # The label shape should match the as the input data, except it has only one channel
        # The label operator is a sparse array whose shape is determined by an INPUT, not an attribute of the slot.meta
        shape = inputProvider.Output.meta.shape
        self.labels.inputs["shape"].setValue(shape[:-1] + (1,)) #<-- Note that "shape" is an INPUT SLOT here.

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
    
    @property
    def maxLabel(self):
        """
        Return the maximum number of labels the classifier can currently use.
        """
        return self.predict.inputs['LabelsCount'].value

    def setMaxLabel(self, highestLabel):
        """
        Change the maximum number of label classes the prediction operator can handle.
        """
        # Count == highest label because 0 isn't a valid label
        self.predict.inputs['LabelsCount'].setValue(highestLabel)





























