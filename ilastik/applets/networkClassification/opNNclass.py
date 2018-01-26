from __future__ import print_function
from builtins import range
from lazyflow.graph import Operator, InputSlot, OutputSlot, OperatorWrapper
from lazyflow.operators.opBlockedArrayCache import OpBlockedArrayCache
from lazyflow.operators.opCompressedUserLabelArray import OpCompressedUserLabelArray
from lazyflow.operators.classifierOperators import OpPixelwiseClassifierPredict
from lazyflow.operators.valueProviders import OpValueCache
from lazyflow.operators import OpMultiArraySlicer2


from lazyflow.classifiers import TikTorchLazyflowClassifier, TikTorchLazyflowClassifierFactory

from ilastik.utility import OpMultiLaneWrapper
from ilastik.utility.operatorSubView import OperatorSubView

class OpNNClassification(Operator):

    Classifier = InputSlot()
    InputImage = InputSlot()
    NumClasses = InputSlot()
    BlockShape = InputSlot()
    PredictionProbabilities = OutputSlot()
    CachedPredictionProbabilities = OutputSlot()
    PredictionProbabilityChannels = OutputSlot(level=1)



    def __init__(self, *args, **kwargs):

        super(OpNNClassification, self).__init__(*args, **kwargs)

        self.predict = OpPixelwiseClassifierPredict(parent=self)
        self.predict.name = "OpClassifierPredict"
        self.predict.Image.connect(self.InputImage)
        self.predict.Classifier.connect(self.Classifier)
        self.predict.LabelsCount.connect(self.NumClasses)
        self.PredictionProbabilities.connect( self.predict.PMaps)

        self.prediction_cache = OpBlockedArrayCache(parent=self)
        self.prediction_cache.name = "BlockedArrayCache"
        self.prediction_cache.inputs["Input"].connect( self.predict.PMaps )
        self.prediction_cache.BlockShape.connect( self.BlockShape )
        self.CachedPredictionProbabilities.connect(self.prediction_cache.Output )

        self.opPredictionSlicer = OpMultiArraySlicer2( parent=self )
        self.opPredictionSlicer.name = "opPredictionSlicer"
        self.opPredictionSlicer.Input.connect( self.prediction_cache.Output )
        self.opPredictionSlicer.AxisFlag.setValue('c')
        self.PredictionProbabilityChannels.connect( self.opPredictionSlicer.Slices )


    def propagateDirty(self, slot, subindex, roi):

        print ("BOOM")
        self.PredictionProbabilityChannels.setDirty(slice(None))
