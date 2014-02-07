
import threading

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

        self._op = op

        self._lock = threading.Lock()
        self._filled = False

    def setupOutputs(self):
        self.CachedOutput.meta.assignFrom(self._guiCache.Output.meta)

    def propagateDirty(self, slot, subindex, roi):
        self._filled = False
        #FIXME okay to set whole volume dirty??
        stop = self.CachedOutput.meta.shape
        start = tuple([0]*len(stop))
        outroi = SubRegion(self.Output, start=start, stop=stop)
        #TODO set bb, cc dirty
        self.CachedOutput.setDirty(outroi)

    def execute(self, slot, subindex, roi, result):
        assert slot == self.CachedOutput

        # suspend other calls to execute, we will do the whole block anyway
        self._lock.acquire()
        if not self._filled:
            self._guiCache.Output[...].block()
            self._filled = True
        self._lock.release()

        result[:] = self._guiCache.Output.get(roi).wait()
