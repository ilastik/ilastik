from ilastik.applets.pixelClassification import OpPixelClassification
from lazyflow.classifiers import IIBoostLazyflowClassifierFactory

class OpIiboostPixelClassification(OpPixelClassification):
    
    def __init__(self, *args, **kwargs):
        super( OpIiboostPixelClassification, self ).__init__( *args, **kwargs )
        
        # Manually override the default classifier type
        self.ClassifierFactory._defaultValue = IIBoostLazyflowClassifierFactory(numStumps=2, debugOutput=True)
        
        # We only permit two label classes.
        # In IIBoost, non-synapse is hard-coded to label 1, synapse is label 2
        self.LabelNames.setValue( ["Non-synapse", "Synapse"] )
        
        