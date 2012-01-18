import numpy, vigra
import time
from lazyflow.graph import *
import gc
import lazyflow.roi
import threading

from lazyflow.operators import OpArrayCache, OpArrayPiper, OpMultiArrayPiper
from lazyflow.operators import OpArrayBlockCache, OpArraySliceCache, OpArraySliceCacheBounding

__testing__ = False

import sys

        
class OpA(OpArrayPiper):
    def getOutSlot(self,slot,key,result):
        v = self.inputs["Input"][key].writeInto(result)
        v.wait()

class OpB(OpArrayPiper):    
    def getOutSlot(self,slot,key,result):
        t = numpy.ndarray(result.shape, result.dtype)
        v = self.inputs["Input"][key].writeInto(t)
        v.wait()
        
        result[:] = t[:] + 1
    
    
class OpC(OpArrayPiper):
    def getOutSlot(self,slot,key,result):
        v = self.inputs["Input"][:].allocate()
        t = v.wait()
        result[:] = t[key]
        self.outputs["Output"][:] = t
