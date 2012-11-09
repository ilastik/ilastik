from lazyflow.graph import Operator, InputSlot, OutputSlot, OperatorWrapper
from lazyflow.operators import OpBlockedSparseLabelArray, OpValueCache, OpTrainRandomForestBlocked, \
                               OpPredictRandomForest, OpSlicedBlockedArrayCache, OpMultiArraySlicer2, \
                               OpPrecomputedInput, Op50ToMulti, OpArrayPiper, OpMultiArrayStacker
                               
from opAutocontextClassification import createAutocontextFeatureOperators


class OpAutocontextBatch( Operator ):
    
    Classifiers = InputSlot(level=1)
    FeatureImage = InputSlot()
    MaxLabelValue = InputSlot()
    AutocontextIterations = InputSlot()
    
    PredictionProbabilities = OutputSlot()
    
    def __init__(self, *args, **kwargs):
        super(OpAutocontextBatch, self).__init__(*args, **kwargs)
        self.prediction_caches = None
        self.predictors = None
        #self.AutocontextIterations.notifyDirty(self.setupOperators)
        
    def setupOperators(self, *args, **kwargs):
    
        print "CCCCCCCCCCCCCCCCCCCCCCCCCCCCCC, setting up operators"
        self.predictors = []
        self.prediction_caches = []
        
        #niter = len(self.Classifiers)
        niter = self.AutocontextIterations.value
        for i in range(niter):
            #predict = OperatorWrapper(OpPredictRandomForest, parent=self, graph=self.graph)
            predict = OpPredictRandomForest(graph=self.graph)
            self.predictors.append(predict)
            #prediction_cache = OperatorWrapper( OpSlicedBlockedArrayCache, parent=self, graph=self.graph ) 
            prediction_cache = OpSlicedBlockedArrayCache( graph=self.graph ) 
            self.prediction_caches.append(prediction_cache)
        
        # Setup autocontext features
        self.autocontextFeatures = []
        self.autocontextFeaturesMulti = []
        self.autocontext_caches = []
        self.featureStackers = []
        
        for i in range(niter-1):
            features = createAutocontextFeatureOperators(self, False)
            self.autocontextFeatures.append(features)
            opMulti = Op50ToMulti(graph = self.graph)
            self.autocontextFeaturesMulti.append(opMulti)
            opStacker = OpMultiArrayStacker(graph = self.graph)
            opStacker.inputs["AxisFlag"].setValue("c")
            opStacker.inputs["AxisIndex"].setValue(3)
            self.featureStackers.append(opStacker)
            autocontext_cache = OpSlicedBlockedArrayCache(graph=self.graph )
            self.autocontext_caches.append(autocontext_cache)
        
        # connect the features to predictors
        for i in range(niter-1):
            for ifeat, feat in enumerate(self.autocontextFeatures[i]):
                feat.inputs['Input'].connect( self.prediction_caches[i].Output)
                print "Multi: Connecting an output", "Input%.2d"%(ifeat)
                self.autocontextFeaturesMulti[i].inputs["Input%.2d"%(ifeat)].connect(feat.outputs["Output"])
            # connect the pixel features to the same multislot
            print "Multi: Connecting an output", "Input%.2d"%(len(self.autocontextFeatures[i]))
            self.autocontextFeaturesMulti[i].inputs["Input%.2d"%(len(self.autocontextFeatures[i]))].connect(self.FeatureImage)
            # stack the autocontext features with pixel features
            self.featureStackers[i].inputs["Images"].connect(self.autocontextFeaturesMulti[i].outputs["Outputs"])
            # cache the stacks
            self.autocontext_caches[i].inputs["Input"].connect(self.featureStackers[i].outputs["Output"])                                                  
            self.autocontext_caches[i].inputs["fixAtCurrent"].setValue(False)    
        
        for i in range(niter):        

            self.predictors[i].inputs['Classifier'].connect(self.Classifiers[i])
            self.predictors[i].inputs['LabelsCount'].connect(self.MaxLabelValue)
            
            self.prediction_caches[i].inputs["fixAtCurrent"].setValue(False)
            self.prediction_caches[i].inputs["Input"].connect(self.predictors[i].PMaps)
            
        self.predictors[0].inputs['Image'].connect(self.FeatureImage)
        for i in range(1, niter):
            self.predictors[i].inputs['Image'].connect(self.autocontext_caches[i-1].outputs["Output"])
            
        self.PredictionProbabilities.connect(self.predictors[-1].PMaps)
        
    def setupOutputs(self):
        print "calling setupOutputs"
        
        if self.AutocontextIterations.ready() and self.predictors is None:
            self.setupOperators()
            
        
        # Set the blockshapes for each input image separately, depending on which axistags it has.
        axisOrder = [ tag.key for tag in self.FeatureImage.meta.axistags ]
        ## Pixel Cache blocks
        blockDimsX = { 't' : (1,1),
                       'z' : (128,256),
                       'y' : (128,256),
                       'x' : (5,5),
                       'c' : (1000,1000) }

        blockDimsY = { 't' : (1,1),
                       'z' : (128,256),
                       'y' : (5,5),
                       'x' : (128,256),
                       'c' : (1000,1000) }

        blockDimsZ = { 't' : (1,1),
                       'z' : (5,5),
                       'y' : (128,256),
                       'x' : (128,256),
                       'c' : (1000,1000) }

        innerBlockShapeX = tuple( blockDimsX[k][0] for k in axisOrder )
        outerBlockShapeX = tuple( blockDimsX[k][1] for k in axisOrder )

        innerBlockShapeY = tuple( blockDimsY[k][0] for k in axisOrder )
        outerBlockShapeY = tuple( blockDimsY[k][1] for k in axisOrder )

        innerBlockShapeZ = tuple( blockDimsZ[k][0] for k in axisOrder )
        outerBlockShapeZ = tuple( blockDimsZ[k][1] for k in axisOrder )

        for cache in self.prediction_caches:
            cache.inputs["innerBlockShape"].setValue( (innerBlockShapeX, innerBlockShapeY, innerBlockShapeZ) )
            cache.inputs["outerBlockShape"].setValue( (outerBlockShapeX, outerBlockShapeY, outerBlockShapeZ) )
    
        for cache in self.autocontext_caches:     
            cache.innerBlockShape.setValue( (innerBlockShapeX, innerBlockShapeY, innerBlockShapeZ) )
            cache.outerBlockShape.setValue( (outerBlockShapeX, outerBlockShapeY, outerBlockShapeZ) )
            
    '''
    def execute(self, slot, subindex, roi, result):
        if slot==self.PredictionProbabilities:
            #we shouldn't be here, it's for testing
            print "opBatchPredict, who is not ready?"
            print self.Classifiers.ready(), self.FeatureImage.ready(), self.AutocontextIterations.ready(), self.MaxLabelValue.ready()
            return
    '''
    
    def setInSlot(self, slot, subindex, roi, value):
        # Nothing to do here: All inputs that support __setitem__
        #   are directly connected to internal operators.
        pass

    def propagateDirty(self, inputSlot, subindex, key):
        # Nothing to do here: All outputs are directly connected to 
        #  internal operators that handle their own dirty propagation.
        pass
        
    