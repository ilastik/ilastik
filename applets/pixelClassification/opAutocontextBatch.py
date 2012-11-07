from lazyflow.graph import Operator, InputSlot, OutputSlot, OperatorWrapper

class OpAutocontextBatch( Operator ):
    
    Classifiers = InputSlot()
    FeatureImages = InputSlot()
    MaxLabelValue = InputSlot()
    
    PredictionProbabilities = OutputSlot()
    
    