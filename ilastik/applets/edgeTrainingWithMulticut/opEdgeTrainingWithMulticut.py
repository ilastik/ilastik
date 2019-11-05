from lazyflow.graph import Operator, InputSlot, OutputSlot
from ilastik.applets.edgeTraining.opEdgeTraining import OpEdgeTraining
from ilastik.applets.multicut.opMulticut import OpMulticut, DEFAULT_SOLVER_NAME

from ilastik.utility import OpMultiLaneWrapper, OperatorSubView


class OpEdgeTrainingWithMulticut(Operator):

    # Edge Training parameters
    FeatureNames = InputSlot(value=OpEdgeTraining.DEFAULT_FEATURES)
    FreezeClassifier = InputSlot(value=True)
    TrainRandomForest = InputSlot(value=False)

    # Multicut parameters
    Beta = InputSlot(value=0.5)
    SolverName = InputSlot(value=DEFAULT_SOLVER_NAME)  # See opMulticut.py for list of solvers
    FreezeCache = InputSlot(value=True)
    WatershedSelectedInput = InputSlot()

    # Lane-wise input slots
    RawData = InputSlot(level=1, optional=True)  # Used by the GUI for display only
    EdgeLabelsDict = InputSlot(level=1, value={})
    VoxelData = InputSlot(level=1)
    Superpixels = InputSlot(level=1)
    GroundtruthSegmentation = InputSlot(level=1, optional=True)

    # EdgeTraining outputs
    Rag = OutputSlot(level=1)
    EdgeProbabilities = OutputSlot(level=1)
    EdgeProbabilitiesDict = OutputSlot(level=1)  # A dict of id_pair -> probabilities
    NaiveSegmentation = OutputSlot(level=1)

    # Multicut Output
    Output = OutputSlot(level=1)  # Pixelwise output (not RAG, etc.)
    EdgeLabelDisagreementDict = OutputSlot(level=1)

    def __init__(self, *args, **kwargs):
        super(OpEdgeTrainingWithMulticut, self).__init__(*args, **kwargs)

        opEdgeTraining = OpEdgeTraining(parent=self)

        opEdgeTraining.EdgeLabelsDict.connect(self.EdgeLabelsDict)

        # This is necessary because OpEdgeTraining occasionally calls self.EdgeLabelsDict.setValue()
        opEdgeTraining.EdgeLabelsDict.backpropagate_values = True

        opEdgeTraining.FeatureNames.connect(self.FeatureNames)
        opEdgeTraining.FreezeClassifier.connect(self.FreezeClassifier)
        opEdgeTraining.RawData.connect(self.RawData)
        opEdgeTraining.VoxelData.connect(self.VoxelData)
        opEdgeTraining.Superpixels.connect(self.Superpixels)
        opEdgeTraining.GroundtruthSegmentation.connect(self.GroundtruthSegmentation)
        opEdgeTraining.WatershedSelectedInput.connect(self.WatershedSelectedInput)
        opEdgeTraining.TrainRandomForest.connect(self.TrainRandomForest)

        self.Rag.connect(opEdgeTraining.Rag)
        self.EdgeProbabilities.connect(opEdgeTraining.EdgeProbabilities)
        self.EdgeProbabilitiesDict.connect(opEdgeTraining.EdgeProbabilitiesDict)
        self.NaiveSegmentation.connect(opEdgeTraining.NaiveSegmentation)

        opMulticut = OpMultiLaneWrapper(OpMulticut, parent=self)
        opMulticut.Beta.connect(self.Beta)
        opMulticut.SolverName.connect(self.SolverName)
        opMulticut.FreezeCache.connect(self.FreezeCache)
        opMulticut.RawData.connect(self.RawData)
        opMulticut.Superpixels.connect(opEdgeTraining.Superpixels)
        opMulticut.Rag.connect(opEdgeTraining.Rag)
        opMulticut.EdgeProbabilities.connect(opEdgeTraining.EdgeProbabilities)
        opMulticut.EdgeProbabilitiesDict.connect(opEdgeTraining.EdgeProbabilitiesDict)

        self.Output.connect(opMulticut.Output)
        self.EdgeLabelDisagreementDict.connect(opMulticut.EdgeLabelDisagreementDict)

        self.opEdgeTraining = opEdgeTraining
        self.opMulticut = opMulticut

        # Must expose these members, which are needed by the serializers or GUI
        # (Therefore, they are really part of those classes public API, or should be.)
        self.opRagCache = self.opEdgeTraining.opRagCache
        self.opEdgeFeaturesCache = self.opEdgeTraining.opEdgeFeaturesCache
        self.opClassifierCache = self.opEdgeTraining.opClassifierCache
        self.setEdgeLabelsFromGroundtruth = self.opEdgeTraining.setEdgeLabelsFromGroundtruth

    def setupOutputs(self):
        pass

    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here."

    def propagateDirty(self, slot, subindex, roi):
        pass

    ##
    ## MultiLaneOperatorABC
    ##
    def addLane(self, laneIndex):
        numLanes = len(self.VoxelData)
        assert numLanes == laneIndex, "Image lanes must be appended."
        self.VoxelData.resize(numLanes + 1)

    def removeLane(self, laneIndex, finalLength):
        self.VoxelData.removeSlot(laneIndex, finalLength)

    def getLane(self, laneIndex):
        return OperatorSubView(self, laneIndex)
