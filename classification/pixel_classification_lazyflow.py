from lazyflow.operators import OpPixelFeaturesPresmoothed, OpBlockedArrayCache, OpArrayPiper, Op5ToMulti

class PixelClassificationLazyflow( object ):
    def __init__( self, graph, feature_scales, array_like_input ):
        self.images = Op5ToMulti( graph )
        self.features = OpPixelFeaturesPresmoothed( graph )
        self.features_cache = OpBlockedArrayCache( graph )

        # connect operators
        self.images.inputs["Input0"].connect(array_like_input)

        self.features.inputs["Scales"].setValue( feature_scales )
        self.features.inputs["Input"].connect(self.images.outputs["Outputs"])

        self.features_cache.inputs["Input"].connect(self.features.outputs["Output"])
        self.features_cache.inputs["innerBlockShape"].setValue((1,32,32,32,16))
        self.features_cache.inputs["outerBlockShape"].setValue((1,128,128,128,64))
        self.features_cache.inputs["fixAtCurrent"].setValue(False)  
    

