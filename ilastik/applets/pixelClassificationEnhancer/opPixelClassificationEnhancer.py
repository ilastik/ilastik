from ..pixelClassification.opPixelClassification import OpPixelClassification

from lazyflow.graph import InputSlot, OutputSlot
from ilastik.utility import OpMultiLaneWrapper
from lazyflow.operators.generic import OpMultiChannelSelector


class OpPixelClassificationEnhancer(OpPixelClassification):
    name = "OpPixelClassificationEnhancer"
    category = "Top-level"
    SelectedChannels = InputSlot(value=[])

    EnhancerInput = OutputSlot(level=1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.opSelectProbs = OpMultiLaneWrapper(
            OpMultiChannelSelector, parent=self, broadcastingSlotNames=["SelectedChannels"]
        )
        self.opSelectProbs.SelectedChannels.connect(self.SelectedChannels)
        self.opSelectProbs.Input.connect(self.opPredictionPipeline.PredictionProbabilities)
        self.EnhancerInput.connect(self.opSelectProbs.Output)
