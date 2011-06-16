import numpy, vigra
import time
from lazyflow.graph import *
import gc
import lazyflow.roi
import threading

from lazyflow.operators.operators import OpArrayCache, OpArrayPiper, OpMultiArrayPiper
from lazyflow.operators.obsoleteOperators import OpArrayBlockCache, OpArraySliceCache, OpArraySliceCacheBounding



class SingleValueProvider(OutputSlot):
    def __init__(self, name, dtype = object):
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
        self.setDirty(slice(None,None,None))

    def fireRequest(self, key, destination):
        assert self._data is not None, "cannot do __getitem__ on Slot %s,  data was not set !!" % (self.name,self,)
        self._lock.acquire()
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
        self.setDirty(slice(None,None,None))
        
    def fireRequest(self, key, destination):
        assert self._data is not None, "cannot do __getitem__ on Slot %s,  data was not set !!" % self.name
        self._lock.acquire()
        destination[:] = self._data.__getitem__(key)
        self._lock.release()
        
        
        
class ListToMultiOperator(Operator):
    name = "List to Multislot converter"
    inputSlots = [InputSlot("List")]
    outputSlots = [MultiOutputSlot("Items", level = 1)]
    
    def notifyConnect(self, inputSlot):
        list = self.inputs["List"][:].allocate().wait()[0]
        self.list= list
        self.outputs["Items"].resize(len(list))
        for o in self.outputs["Items"]:
            o._dtype = object
            o._shape = (1,)
    
    def getSubOutSlot(self, slots, indexes, key, result):
        result[0] = self.list[indexes[0]]