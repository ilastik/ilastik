import numpy, vigra
import time
from graph import *
import gc
import roi
import threading

from operators import OpArrayCache, OpArrayPiper
from obsoleteOperators import OpArrayBlockCache, OpArraySliceCache, OpArraySliceCacheBounding

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
        test = v()
        
        result[:] = t[:] + 1
    
    
class OpC(OpArrayPiper):
    def getOutSlot(self,slot,key,result):
        v = self.inputs["Input"][:].allocate()
        t = v()
        result[:] = t[key]
        self.outputs["Output"][:] = t





class OpMultiArrayPiper(Operator):
    inputSlots = [MultiInputSlot("MultiInput")]
    outputSlots = [MultiOutputSlot("MultiOutput")]
    
    def notifyConnect(self, inputSlot):
        self.outputs["MultiOutput"].clearAllSlots()
        for i,islot in enumerate(self.inputs["MultiInput"]):
            slot = PartialMultiOutputSlot("Out3%d" % i, self, self.outputs["MultiOutput"])
            slot._dtype = islot.dtype
            slot._shape = islot.shape
            slot._axistags = islot.axistags
            self.outputs["MultiOutput"].append(slot)
    
    def notifyPartialMultiConnect(self, multislot, slot, index):
        s = PartialMultiOutputSlot("Out%3d" % index, self, self.outputs["MultiOutput"])
        s._dtype = slot.dtype
        s._shape = slot.shape
        s._axistags = slot.axistags
        self.outputs["MultiOutput"].insert(index, s)

    
    def getOutSlot(self, slot, key, result):
        raise RuntimeError("OpMultiPipler does not support getOutSlot")

    def getPartialMultiOutSlot(self, multislot, slot, index, key, result):
        req = self.inputs["MultiInput"][index][key].writeInto(result)
        res = req()
        return res
     
    def setInSlot(self, slot, key, value):
        raise RuntimeError("OpMultiPipler does not support setInSlot")

    def setPartialMultiInSlot(self,multislot,slot,index, key,value):
        pass



g = Graph(numThreads = 2)

source0 = ArrayProvider( "Zeros", shape = (200,100), dtype=numpy.uint8)
source0.setData(numpy.zeros(source0.shape,dtype = source0.dtype))

source1 = ArrayProvider( "Zeros", shape = (300,50), dtype=numpy.uint8)
source1.setData(numpy.zeros(source1.shape,dtype = source1.dtype))


opa = OpMultiArrayPiper(g)
opb = OpMultiArrayPiper(g)
opc = OpMultiArrayPiper(g)

opd = OpArrayPiper(g)
ope = OpB(g)
ope2 = OpB(g)

opa.inputs["MultiInput"].connect(source0)
opa.inputs["MultiInput"].connect(source1)

opb.inputs["MultiInput"].connect(opa.outputs["MultiOutput"])

opd.inputs["Input"].connect(opb.outputs["MultiOutput"][0])
ope.inputs["Input"].connect(opb.outputs["MultiOutput"][1])
ope2.inputs["Input"].connect(ope.outputs["Output"])

opc.inputs["MultiInput"].connect(opd.outputs["Output"])
opc.inputs["MultiInput"].connect(ope2.outputs["Output"])

print opc.outputs["MultiOutput"][0][:,:].allocate()
print opc.outputs["MultiOutput"][1][:,:].allocate()







def runBenchmark(numThreads, cacheClass, shape, requests):    
    g = Graph(numThreads = numThreads)
    provider = ArrayProvider( "Zeros", shape = shape, dtype=numpy.uint8)
    provider.setData(numpy.zeros(provider.shape,dtype = provider.dtype))
    opa = OpA(g)
    opb = OpB(g)
    opc1 = cacheClass(g,5)
    opc2 = cacheClass(g,11)
    opfull = OpC(g)
    opc3 = cacheClass(g,7)
    opc4 = cacheClass(g,11)
    opf = OpArrayCache(g)
    
    opa.inputs["Input"].connect(provider)
    opb.inputs["Input"].connect(opa.outputs["Output"])
    opc1.inputs["Input"].connect(opb.outputs["Output"])
    opc2.inputs["Input"].connect(opc1.outputs["Output"])
    opfull.inputs["Input"].connect(opc2.outputs["Output"])
    opc3.inputs["Input"].connect(opfull.outputs["Output"])
    opc4.inputs["Input"].connect(opc3.outputs["Output"])
    opf.inputs["Input"].connect(opc1.outputs["Output"])
    
    tg1 = time.time()
    
    for r in requests:
        if r == "setDirty":
            provider.setData(numpy.zeros(provider.shape,dtype = provider.dtype))
            continue
        key = roi.roiToSlice(numpy.array(r[0]), numpy.array(r[1]))
        t1 = time.time()
        res1 = opc4.outputs["Output"][key].allocate()
        t2 = time.time()
        print "%s request %r runtime:" % (cacheClass.__name__,key) , t2-t1
        assert (res1 == 1).all(), res1
    tg2 = time.time()
    g.finalize()
    print "%s Total runtime:" % cacheClass.__name__, tg2-tg1    

    gc.collect()


shape = (200,200,200)
requests = [[[0,0,0],[100,100,1]],
            [[50,50,50],[150,150,150]],
            [[50,50,50],[150,150,150]],
            [[0,0,0],[200,200,200]],
            "setDirty",
            [[0,0,0],[200,200,200]]
            ]
numThreads = 2
#runBenchmark(numThreads,OpArrayBlockCache, shape, requests)
#runBenchmark(1,OpArrayBlockCache, shape, requests)
runBenchmark(numThreads,OpArrayCache, shape, requests)
