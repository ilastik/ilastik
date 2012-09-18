import numpy, vigra
import time
from lazyflow.graph import *
import gc
import lazyflow.roi
from lazyflow.roi import roiToSlice
import threading

from lazyflow.operators import OpArrayCache, OpArrayPiper, OpMultiArrayPiper
from lazyflow.operators import OpArrayBlockCache, OpArraySliceCache, OpArraySliceCacheBounding

__testing__ = False

import sys


class OpA(OpArrayPiper):
    def execute(self, slot, subindex, roi, result):
        key = roiToSlice(roi.start, roi.stop)
        v = self.inputs["Input"][key].writeInto(result)
        v.wait()

class OpB(OpArrayPiper):
    def execute(self, slot, subindex, roi, result):
        key = roiToSlice(roi.start, roi.stop)
        t = numpy.ndarray(result.shape, result.dtype)
        v = self.inputs["Input"][key].writeInto(t)
        v.wait()

        result[:] = t[:] + 1


class OpC(OpArrayPiper):
    def execute(self, slot, subindex, roi, result):
        key = roiToSlice(roi.start, roi.stop)
        v = self.inputs["Input"][:].allocate()
        t = v.wait()
        result[:] = t[key]
        self.outputs["Output"][:] = t
