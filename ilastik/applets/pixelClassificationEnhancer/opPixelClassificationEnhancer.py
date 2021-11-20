from ..pixelClassification.opPixelClassification import OpPixelClassification
from ..neuralNetwork.opNNclass import OpPredictionPipeline as OpNNPredictionPipeline
from ..neuralNetwork.opNNclass import OpBlockShape as OpNNBlockShape

from lazyflow.graph import InputSlot, OutputSlot
from ilastik.utility import OpMultiLaneWrapper
from lazyflow.operators.generic import OpMultiChannelSelector
from lazyflow import stype
from functools import partial
import logging
from ilastik.utility.operatorSubView import OperatorSubView

logger = logging.getLogger(__name__)


class OpPixelClassificationEnhancer(OpPixelClassification):
    name = "OpPixelClassificationEnhancer"
    category = "Top-level"
    SelectedChannels = InputSlot(value=[])
    ModelBinary = InputSlot(stype=stype.Opaque, nonlane=True)
    # Contains cached model info
    ModelInfo = InputSlot(stype=stype.Opaque, nonlane=True, optional=True)
    ModelSession = InputSlot()
    ServerConfig = InputSlot(stype=stype.Opaque, nonlane=True)

    NumNNClasses = InputSlot()
    FreezeNNPredictions = InputSlot(stype="bool", value=False, nonlane=True)

    NNClassifier = OutputSlot()
    EnhancerInput = OutputSlot(level=1)

    NNPredictionProbabilities = OutputSlot(
        level=1
    )  # Classification predictions (via feature cache for interactive speed)
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
        self.opSelectProbs.Input.connect(self.opPredictionPipeline.PredictionProbabilities)
        self.EnhancerInput.connect(self.opSelectProbs.Output)

        ## NN stuff

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

    def set_model(self, model_content: bytes) -> bool:
        self.ModelBinary.disconnect()
        self.ModelBinary.setValue(model_content)
        return self.opModel.TiktorchModel.ready()

    def update_config(self, partial_config: dict):
        self.ClassifierFactory.meta.hparams = partial_config

        def _send_hparams(slot):
            classifierFactory = self.ClassifierFactory[:].wait()[0]
            classifierFactory.update_config(self.ClassifierFactory.meta.hparams)

        if not self.ClassifierFactory.ready():
            self.ClassifierFactory.notifyReady(_send_hparams)
        else:
            classifierFactory = self.ClassifierFactory[:].wait()[0]
            classifierFactory.update_config(partial_config)

    def propagateDirty(self, slot, subindex, roi):
        # Nothing to do here: All outputs are directly connected to
        #  internal operators that handle their own dirty propagation.
        self.PredictionProbabilityChannels.setDirty(slice(None))
        super().propagateDirty(slot, subindex, roi)
