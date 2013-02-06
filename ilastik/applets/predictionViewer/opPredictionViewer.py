from lazyflow.graph import Operator, InputSlot

class OpPredictionViewer( Operator ):

    PredictionProbabilities = InputSlot()
    
    RawImage = InputSlot(optional=True)
    PmapColors = InputSlot(optional=True)
    LabelNames = InputSlot(optional=True)
    
    