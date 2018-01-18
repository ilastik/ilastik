from __future__ import print_function
from builtins import range
from lazyflow.graph import Operator, InputSlot, OutputSlot, OperatorWrapper
from lazyflow.operators.opBlockedArrayCache import OpBlockedArrayCache
from lazyflow.operators.opCompressedUserLabelArray import OpCompressedUserLabelArray
from lazyflow.operators.classifierOperators import OpPixelwiseClassifierPredict
from lazyflow.operators.valueProviders import OpValueCache


from lazyflow.classifiers import TikTorchLazyflowClassifier, TikTorchLazyflowClassifierFactory

from ilastik.utility import OpMultiLaneWrapper
from ilastik.utility.operatorSubView import OperatorSubView

class OpNNClassification(Operator):

    # ClassifierFactory = InputSlot(value=TikTorchLazyflowClassifier())
    Classifier = InputSlot()
    ClassifierFactory = InputSlot()
    InputImage = InputSlot()
    # OutputImage = OutputSlot()
    NumClasses = InputSlot()
    BlockShape = InputSlot()
    # CachedOutputImage = OutputSlot()
    PredictionProbabilities = OutputSlot()
    CachedPredictionProbabilities = OutputSlot()



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


    def propagateDirty(self, slot, subindex, roi):
        # Our output changes when the input changed shape, not when it becomes dirty.
        pass



    # def addLane(self, laneIndex):
    #     numLanes = len(self.InputImages)
    #     assert numLanes == laneIndex, "Image lanes must be appended."        
    #     self.InputImages.resize(numLanes+1)
    #     self.Bookmarks.resize(numLanes+1)
    #     self.Bookmarks[numLanes].setValue([]) # Default value
        
    # def removeLane(self, laneIndex, finalLength):
    #     self.InputImages.removeSlot(laneIndex, finalLength)
        # self.Bookmarks.removeSlot(laneIndex, finalLength)

    # def getLane(self, laneIndex):
    #     return OperatorSubView(self, laneIndex)
