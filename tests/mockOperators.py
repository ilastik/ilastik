import numpy, vigra
import time
from graph import *
import gc
import roi
import threading

from operators.operators import OpArrayCache, OpArrayPiper, OpMultiArrayPiper
from operators.obsoleteOperators import OpArrayBlockCache, OpArraySliceCache, OpArraySliceCacheBounding

__testing__ = False

import sys

class ArrayProvider(OutputSlot):
    def __init__(self,name,shape,dtype):
        OutputSlot.__init__(self,name)
        self._shape = shape
        self._dtype = dtype
        self._data = None
        self._axistags = "not none"
        self._lock = threading.Lock()
        
    def setData(self,d):
        assert d.dtype == self._dtype
        assert d.shape == self._shape
        self._lock.acquire()
        self._data = d
        self._lock.release()
        self.setDirty()
        

    def fireRequest(self, key, destination):
        assert self._data is not None, "cannot do __getitem__ on Slot %s,  data was not set !!" % (self.name,self,)
        self._lock.acquire()
        destination[:] = self._data.__getitem__(key)
        self._lock.release()

        
class OpA(OpArrayPiper):
    def getOutSlot(self,slot,key,result):
        v = self.inputs["Input"][key].writeInto(result)
        v()

class OpB(OpArrayPiper):    
    def getOutSlot(self,slot,key,result):
        t = numpy.ndarray(result.shape, result.dtype)
        v = self.inputs["Input"][key].writeInto(t)
        v()
        
        result[:] = t[:] + 1
    
    
class OpC(OpArrayPiper):
    def getOutSlot(self,slot,key,result):
        v = self.inputs["Input"][:].allocate()
        t = v()
        result[:] = t[key]
        self.outputs["Output"][:] = t
