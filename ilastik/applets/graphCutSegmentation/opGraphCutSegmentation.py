
import numpy as np
import vigra
import opengm

from context.operators.opObjectsSegment import OpObjectsSegment

from lazyflow.slot import InputSlot, OutputSlot
from lazyflow.operators.valueProviders import OpArrayCache


class OpGraphCutSegmentation(OpObjectsSegment):
    RawInput = InputSlot()
    CachedOutput = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpGraphCutSegmentation, self).__init__(*args, **kwargs)
        self._guiCache = OpArrayCache(parent=self)

        self._guiCache.Input.connect(self.Output)
        self.CachedOutput.connect(self._guiCache.Output)

