
import numpy as np
import vigra
import opengm

from context.operators.opObjectsSegment import OpObjectsSegment

from lazyflow.slot import InputSlot, OutputSlot
from lazyflow.operators.valueProviders import OpArrayCache
from lazyflow.operator import Operator


class OpGraphCutSegmentation(Operator):
    RawInput = InputSlot()  # FIXME is this neccessary?
    InputImage = InputSlot()
    Binary = InputSlot()
    Beta = InputSlot(value=.2)
    Channel = InputSlot(value=0)

    CachedOutput = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpGraphCutSegmentation, self).__init__(*args, **kwargs)

        op = OpObjectsSegment(parent=self)

        op.Prediction.connect(self.InputImage)
        op.Binary.connect(self.Binary)
        op.Beta.connect(self.Beta)
        op.Channel.connect(self.Channel)

        self._guiCache = OpArrayCache(parent=self)

        self._guiCache.Input.connect(op.Output)
        self.CachedOutput.connect(self._guiCache.Output)

        self._op = op

    def propagateDirty(self, slot, subindex, roi):
        # only applies for RawInput, which we are ignoring anyway
        pass