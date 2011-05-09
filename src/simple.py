import numpy, vigra
import time
from graph import *

from operators import OpArrayPiper, OpArrayBlockCache, OpArraySliceCache, OpArraySliceCacheBounding

__testing__ = False

import sys

sys.setrecursionlimit(20000)

class ArrayProvider(OutputSlot):
    
    def __init__(self,name,shape,dtype):
        OutputSlot.__init__(self,name)
        self._shape = shape
        self._dtype = dtype
        self._data = None
        self._axistags = "not none"
        
    def setData(self,d):
        assert d.dtype == self._dtype
        assert d.shape == self._shape
        self._data = d
        self.setDirty()

    def __getitem__(self, key):
        assert self._data is not None, "cannot do __getitem__ on Slot %s,  data was not set !!" % (self.name,self,)
        result = key[-1]
        key= key[:-1]
        result[:] = self._data.__getitem__(*key)


        
class OpA(OpArrayPiper):
    def getOutSlot(self,slot,key,result):
        v = self.inputs["Input"][key,result]
        v()

class OpB(OpArrayPiper):    
    def getOutSlot(self,slot,key,result):
        t = numpy.ndarray(result.shape, result.dtype)
        v = self.inputs["Input"][key,t]
        v()
        result[:] = t[:] + 1
    
    
g = Graph(numThreads = 2)

provider = ArrayProvider( "Zeros", shape = (200,200,200), dtype=numpy.uint8)
provider.setData(numpy.zeros(provider.shape,dtype = provider.dtype))

opa = OpA(g)
opb = OpB(g)
opc1 = OpArrayBlockCache(g,5)
opc2 = OpArrayBlockCache(g,11)
opc3 = OpArrayBlockCache(g,7)
opc4 = OpArrayBlockCache(g,11)
#opc1 = OpArraySliceCacheBounding(g,5)
#opc2 = OpArraySliceCacheBounding(g,11)
#opc3 = OpArraySliceCacheBounding(g,7)
#opc4 = OpArraySliceCacheBounding(g,11)


opd = OpArraySliceCache(g)
ope = OpArraySliceCacheBounding(g)

opa.inputs["Input"].connect(provider)
opb.inputs["Input"].connect(opa.outputs["Output"])
opc1.inputs["Input"].connect(opb.outputs["Output"])
opc2.inputs["Input"].connect(opc1.outputs["Output"])
opc3.inputs["Input"].connect(opc2.outputs["Output"])
opc4.inputs["Input"].connect(opc3.outputs["Output"])
opd.inputs["Input"].connect(opc1.outputs["Output"])
ope.inputs["Input"].connect(opc1.outputs["Output"])

t1 = time.time()
res1 = opc4.outputs["Output"][:,:,:]
t2 = time.time()

#t3 = time.time()
#res2 = opd.outputs["Output"][4,:,:]
#t4 = time.time()
#
#t5 = time.time()
#res3 = ope.outputs["Output"][5,:,:]
#t6 = time.time()
#
print "Result runtime:", t2-t1

#print "Result runtime:", t2-t1, t4 - t3, t6 - t5
#print "Result average:", numpy.average(res1)
#print "Answer shape and Dtype : ",res1.shape, res1.dtype
#print "Total Shape and Dtype : ", opb.outputs["Output"].shape,opb.outputs["Output"].dtype

#for i in xrange(2):
#    t1 = time.clock()
#    res = opd.outputs["Output"][:,:,:]
#    t2 = time.clock()
#    print "Result runtime:", t2-t1
#    print "Result average:", numpy.average(res)
#    print "Answer shape and Dtype : ",res.shape, res.dtype
#    print "Total Shape and Dtype : ", opb.outputs["Output"].shape,opb.outputs["Output"].dtype


g.finalize()

assert (res1 == 1).all(), res1
#assert (res2 == 1).all()
#assert (res3 == 1).all()
