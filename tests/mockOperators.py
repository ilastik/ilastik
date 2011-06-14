import numpy, vigra
import time
from lazyflow.graph import *
import gc
import lazyflow.roi
import threading

from lazyflow.operators.operators import OpArrayCache, OpArrayPiper, OpMultiArrayPiper
from lazyflow.operators.obsoleteOperators import OpArrayBlockCache, OpArraySliceCache, OpArraySliceCacheBounding

__testing__ = False

import sys

class SingleValueProvider(OutputSlot):
    def __init__(self, name, dtype):
        OutputSlot.__init__(self,name)
        self._shape = (1,)
        self._dtype = dtype
        self._data = numpy.array( self._shape, self._dtype)
        self._lock = threading.Lock()
        
    def setValue(self, v):
        assert isinstance(v,self._dtype)
        self._lock.acquire()
        self._data[0] = v
        self._lock.release()
        self.setDirty()

    def fireRequest(self, key, destination):
        assert self._data is not None, "cannot do __getitem__ on Slot %s,  data was not set !!" % (self.name,self,)
        self._lock.acquire()
        print "lllllllllllll", destination.shape, self._data.__getitem__(key).shape
        destination[:] = self._data.__getitem__(key)
        self._lock.release()


class ArrayProvider(OutputSlot):
    def __init__(self, name, shape, dtype, axistags="not none"):
        OutputSlot.__init__(self,name)
        self._shape = shape
        self._dtype = dtype
        self._data = None
        self._axistags = axistags
        self._lock = threading.Lock()
        
    def setData(self,d):
        assert d.dtype == self._dtype
        assert d.shape == self._shape
        self._lock.acquire()
        self._data = d
        self._lock.release()
        self.setDirty()
        
    def fireRequest(self, key, destination):
        assert self._data is not None, "cannot do __getitem__ on Slot %s,  data was not set !!" % self.name
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
