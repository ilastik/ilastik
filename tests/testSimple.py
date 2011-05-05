from graph import *

class StringOut(OutputSlot):
    def __init__(self,name):
        self._dtype = object
        self._shape = (1,)
        self._axistags = "something"
        OutputSlot.__init__(self,name)

class OpPropagator(Operator):  
    
    def notifyConnect(self, inputSlot):
        self.outputs["Output"]._dtype = inputSlot.dtype
        self.outputs["Output"]._shape = inputSlot.shape
        self.outputs["Output"]._axistags = inputSlot.axistags


class OpA(Operator):
    inputSlots = []
    outputSlots = [StringOut("Output")]
    
    def getOutSlot(self,slot,key,destination):
        destination[:] = "A"

class OpB(Operator):
    inputSlots = []
    outputSlots = [StringOut("Output")]
    
    def getOutSlot(self,slot,key,destination):
        destination[:] = "B"


class OpStringAdder(OpPropagator):
    inputSlots = [InputSlot("Input1"),InputSlot("Input2")]
    outputSlots = [OutputSlot("Output")]


    def getOutSlot(self,slot,key,destination):
        temp = (1,2,3)
        t = numpy.ndarray((1,), dtype = object)
        a = self.inputs["Input1"][key,destination]
        b = self.inputs["Input2"][key,t]
        
        a()
        b()

        destination[:] += t
    
class OpForwarder(OpPropagator):
    inputSlots = [InputSlot("Input")]
    outputSlots = [OutputSlot("Output")]
    
    def getOutSlot(self,slot,key,destination):
        query = self.inputs["Input"][key,destination]
        query()
    
    
class OpCachingForwarder(OpPropagator):
    inputSlots = [InputSlot("Input")]
    outputSlots = [OutputSlot("Output")]
    
    def __init__(self, args):
        Operator.__init__(self,args)
        self.cache = None
    
    def getOutSlot(self,slot,key,destination):
#        if self.cache is None:
#            query = self.inputs["Input"][key,destination]
#            query()
#            self.cache = destination.copy()
#        else:
#            destination[:] = self.cache[key]         
        query = self.inputs["Input"][key,destination]
        query()
    
    def setDirty(self, inputSlot):
        self.cache = None
        Operator.setDirty(self, inputSlot)
        
        

class TestSimple(object):
    
    def testSimple(self):
        for t in xrange(3):
            print
            print
            print "Beginning tests with %d threads..." % t
            g = Graph(numThreads=t)
            #import time
            #time.sleep(2)
            #print "Beginning tests...."
            
            oA = OpA(g)
            oB = OpB(g)
            oAdder1 = OpStringAdder(g)
            oAdder2 = OpStringAdder(g)
            oForwarder1 = OpForwarder(g)
            oCachingForwarder1 = OpCachingForwarder(g)
            
            oAdder1.inputs["Input1"].connect(oA.outputs["Output"])
            oAdder1.inputs["Input2"].connect(oB.outputs["Output"])
            
            oForwarder1.inputs["Input"].connect(oAdder1.outputs["Output"])
            oAdder2.inputs["Input1"].connect(oForwarder1.outputs["Output"])
            oAdder2.inputs["Input2"].connect(oA.outputs["Output"])
            
            oCachingForwarder1.inputs["Input"].connect(oAdder2.outputs["Output"])
            
            #o2.disconnect()
            
            res1 = oCachingForwarder1.outputs["Output"][0]
            res2 = oCachingForwarder1.outputs["Output"][0]
            
            oB.setDirty()
            
            res3 = oCachingForwarder1.outputs["Output"][0]
            
            g.finalize()        
            
            print res1,res2,res3
            assert res1 == res2 == res3 == "ABA"