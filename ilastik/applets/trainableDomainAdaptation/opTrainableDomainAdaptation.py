import logging

from ilastik.utility import OpMultiLaneWrapper
from lazyflow import stype
from lazyflow.graph import InputSlot, OutputSlot
from lazyflow.operators.generic import OpMultiChannelSelector

from ilastik.applets.neuralNetwork.opNNclass import OpBlockShape as OpNNBlockShape
from ilastik.applets.neuralNetwork.opNNclass import OpPredictionPipeline as OpNNPredictionPipeline
from ilastik.applets.pixelClassification.opPixelClassification import OpPixelClassification

logger = logging.getLogger(__name__)


class OpTrainableDomainAdaptation(OpPixelClassification):
    name = "OpTrainableDomainAdaptation"
    category = "Top-level"
    SelectedChannels = InputSlot(value=[])
    OverlayImages = InputSlot(level=1, optional=True)
    BIOModel = InputSlot(stype=stype.Opaque, nonlane=True)
    # Contains cached model info
    ModelSession = InputSlot()
    ServerConfig = InputSlot(stype=stype.Opaque, nonlane=True)

    NumNNClasses = InputSlot()
    FreezeNNPredictions = InputSlot(stype="bool", value=False, nonlane=True)

    NNClassifier = OutputSlot()
    EnhancerNetworkInput = OutputSlot(level=1)

    # Classification predictions (via feature cache for interactive speed)
    NNPredictionProbabilities = OutputSlot(level=1)
    NNPredictionProbabilityChannels = OutputSlot(level=2)  # Classification predictions, enumerated by channel
    CachedNNPredictionProbabilities = OutputSlot(level=1)

    def __init__(self, *args, connectionFactory, **kwargs):
        super().__init__(*args, **kwargs)
        self._connectionFactory = connectionFactory

        self.FreezeNNPredictions.setValue(True)
        self.opSelectProbs = OpMultiLaneWrapper(
            OpMultiChannelSelector, parent=self, broadcastingSlotNames=["SelectedChannels"]
        )
        self.opSelectProbs.SelectedChannels.connect(self.SelectedChannels)
        self.opSelectProbs.Input.connect(self.opPredictionPipeline.CachedPredictionProbabilities)
        self.EnhancerNetworkInput.connect(self.opSelectProbs.Output)

        # NN related connections
        self.opNNBlockShape = OpMultiLaneWrapper(OpNNBlockShape, parent=self)
        self.opNNBlockShape.RawImage.connect(self.opSelectProbs.Output)
        self.opNNBlockShape.ModelSession.connect(self.ModelSession)

        self.opNNPredictionPipeline = OpMultiLaneWrapper(OpNNPredictionPipeline, parent=self)
        self.opNNPredictionPipeline.RawImage.connect(self.opSelectProbs.Output)
        self.opNNPredictionPipeline.Classifier.connect(self.ModelSession)
        self.opNNPredictionPipeline.NumClasses.connect(self.NumNNClasses)
        self.opNNPredictionPipeline.FreezePredictions.connect(self.FreezeNNPredictions)

        self.NNPredictionProbabilities.connect(self.opNNPredictionPipeline.PredictionProbabilities)
        self.CachedNNPredictionProbabilities.connect(self.opNNPredictionPipeline.CachedPredictionProbabilities)
        self.NNPredictionProbabilityChannels.connect(self.opNNPredictionPipeline.PredictionProbabilityChannels)

    def setupOutputs(self):
        super().setupOutputs()
        if self.opNNBlockShape.BlockShapeInference.ready():
            self.opNNPredictionPipeline.BlockShape.connect(self.opNNBlockShape.BlockShapeInference)

    def cleanUp(self):
        try:
            self.ModelSession.value.close()
        except Exception as e:
            logger.warning(e)

        super().cleanUp()

    def update_config(self, partial_config: dict):
        self.ClassifierFactory.meta.hparams = partial_config

        def _send_hparams(*_args):
            classifierFactory = self.ClassifierFactory[:].wait()[0]
            classifierFactory.update_config(self.ClassifierFactory.meta.hparams)

        if self.ClassifierFactory.ready():
            _send_hparams()
        else:
            self.ClassifierFactory.notifyReady(_send_hparams)

    def propagateDirty(self, slot, subindex, roi):
        # Nothing to do here: All outputs are directly connected to
        #  internal operators that handle their own dirty propagation.
        self.PredictionProbabilityChannels.setDirty(slice(None))
        super().propagateDirty(slot, subindex, roi)
