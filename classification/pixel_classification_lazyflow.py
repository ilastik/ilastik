from lazyflow.operators import OpPixelFeaturesPresmoothed, OpBlockedArrayCache, OpArrayPiper, Op5ToMulti, OpBlockedSparseLabelArray, OpArrayCache, \
                               OpTrainRandomForestBlocked, OpPredictRandomForest, OpSlicedBlockedArrayCache

class PixelClassificationLazyflow( object ):
    def __init__( self, graph, feature_scales, array_like_input ):
        ##
        # IO
        ##
        self.images = Op5ToMulti( graph )
        self.features = OpPixelFeaturesPresmoothed( graph )
        self.features_cache = OpBlockedArrayCache( graph )
        self.labels = OpBlockedSparseLabelArray( graph )                                

        self.images.inputs["Input0"].connect(array_like_input)

        self.features.inputs["Input"].connect(self.images.outputs["Outputs"])
        self.features.inputs["Scales"].setValue( feature_scales )        

        self.features_cache.inputs["Input"].connect(self.features.outputs["Output"])
        self.features_cache.inputs["innerBlockShape"].setValue((1,32,32,32,16))
        self.features_cache.inputs["outerBlockShape"].setValue((1,128,128,128,64))
        self.features_cache.inputs["fixAtCurrent"].setValue(False)  
    
        shape = array_like_input.meta.shape
        self.labels.inputs["shape"].setValue(shape[:-1] + (1,))
        self.labels.inputs["blockShape"].setValue((1, 32, 32, 32, 1))
        self.labels.inputs["eraser"].setValue(100)    

        
        ##
        # training
        ##
        opMultiL = Op5ToMulti( graph )    
        opMultiL.inputs["Input0"].connect(self.labels.outputs["Output"])

        opMultiLblocks = Op5ToMulti( graph )
        opMultiLblocks.inputs["Input0"].connect(self.labels.outputs["nonzeroBlocks"])
        train = OpTrainRandomForestBlocked( graph )
        train.inputs['Labels'].connect(opMultiL.outputs["Outputs"])
        train.inputs['Images'].connect(self.features_cache.outputs["Output"])
        train.inputs["nonzeroLabelBlocks"].connect(opMultiLblocks.outputs["Outputs"])
        train.inputs['fixClassifier'].setValue(False)                

        self.classifier_cache = OpArrayCache( graph )
        self.classifier_cache.inputs["Input"].connect(train.outputs['Classifier'])


        ##
        # prediction
        ##
        self.predict=OpPredictRandomForest( graph )
        self.predict.inputs['Classifier'].connect(self.classifier_cache.outputs['Output']) 
        self.predict.inputs['Image'].connect(self.features.outputs["Output"])
        

        pCache = OpSlicedBlockedArrayCache( graph )
        pCache.inputs["fixAtCurrent"].setValue(False)
        pCache.inputs["innerBlockShape"].setValue(((1,256,256,1,2),(1,256,1,256,2),(1,1,256,256,2)))
        pCache.inputs["outerBlockShape"].setValue(((1,256,256,4,2),(1,256,4,256,2),(1,4,256,256,2)))
        pCache.inputs["Input"].connect(self.predict.outputs["PMaps"])
        self.prediction_cache = pCache
        
        
