
import numpy as np
import vigra

from opObjectsSegment import OpObjectsSegment

from lazyflow.slot import InputSlot, OutputSlot
from lazyflow.operators.valueProviders import OpArrayCache
from lazyflow.operator import Operator
from lazyflow.rtype import SubRegion


class OpGraphCutSegmentation(Operator):
    RawInput = InputSlot()  # FIXME is this neccessary?
    InputImage = InputSlot()
    LabelImage = InputSlot()
    Beta = InputSlot(value=.2)
    Channel = InputSlot(value=0)

    CachedOutput = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpGraphCutSegmentation, self).__init__(*args, **kwargs)

        op = OpObjectsSegment(parent=self)

        op.Prediction.connect(self.InputImage)
        op.LabelImage.connect(self.LabelImage)
        op.Beta.connect(self.Beta)
        op.Channel.connect(self.Channel)

        self.CachedOutput.connect(op.CachedOutput)

        self._op = op

        self._filled = False

    def setupOutputs(self):
        pass

    def propagateDirty(self, slot, subindex, roi):
        pass  # Nothing to do

    def execute(self, slot, subindex, roi, result):
        assert False, "Shuld not get here"
