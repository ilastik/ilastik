from __future__ import print_function
from builtins import range
from lazyflow.graph import Operator, InputSlot, OutputSlot, OperatorWrapper
from lazyflow.operators.opBlockedArrayCache import OpBlockedArrayCache
from lazyflow.operators.opCompressedUserLabelArray import OpCompressedUserLabelArray
from lazyflow.operators.classifierOperators import OpTrainClassifierBlocked, OpClassifierPredict
from lazyflow.operators.valueProviders import OpValueCache


from lazyflow.classifiers import TikTorchLazyflowClassifier

from ilastik.utility import OpMultiLaneWrapper
from ilastik.utility.operatorSubView import OperatorSubView

class OpNNClassification(Operator):

    # ClassifierFactory = InputSlot(value=TikTorchLazyflowClassifier())
    ClassifierFactory = InputSlot()
    InputImage = InputSlot()
    OutputImage = OutputSlot()
    NumClasses = InputSlot()
    # CachedOutputImage = OutputSlot()



    def __init__(self, *args, **kwargs):

        super(OpNNClassification, self).__init__(*args, **kwargs)

        self.OutputImage.connect(self.InputImage)


        self.predict = OpClassifierPredict(parten=self)
        self.predict.name = "OpClassifierPredict"
        self.predict.Image.connect(self.InputImages)
        self.predict.Classifier.connect(self.ClassifierFactory)
        self.predict.LabelsCount.connect(self.NumClasses)
        # self.predict.PredictionProbabilities.connect( self.predict.PMaps )



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
