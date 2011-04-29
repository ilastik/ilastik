from graph import *


class OpA(Operator):
    inputSlots = []
    outputSlots = [OutputSlot("Output")]
    
    def getOutSlot(self,slot,key):
        return "A"

class OpB(Operator):
    inputSlots = []
    outputSlots = [OutputSlot("Output")]
    
    def getOutSlot(self,slot,key):
        return "B"


class OpStringAdder(Operator):
    inputSlots = [InputSlot("Input1"),InputSlot("Input2")]
    outputSlots = [OutputSlot("Output")]


    def getOutSlot(self,slot,key):
        a = self.inputs["Input1"][key]
        b = self.inputs["Input2"][key]
        
        return a() + b()
    
class OpForwarder(Operator):
    inputSlots = [InputSlot("Input")]
    outputSlots = [OutputSlot("Output")]
    
    def getOutSlot(self,slot,key):
        query = self.inputs["Input"][key]
        return query()
    
    
class OpCachingForwarder(Operator):
    inputSlots = [InputSlot("Input")]
    outputSlots = [OutputSlot("Output")]
    
    def __init__(self, args):
        Operator.__init__(self,args)
        self.cache = None
    
    def getOutSlot(self,slot,key):
        if self.cache is None:
            query = self.inputs["Input"][key]
            self.cache = query()
                    
        return self.cache
    
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
            
            res1 = oCachingForwarder1.outputs["Output"][7]
            
            res2 = oCachingForwarder1.outputs["Output"][3]
            
            oB.setDirty()
            
            res3 = oCachingForwarder1.outputs["Output"][1]
            
            g.finalize()        
            
            
            assert res1 == res2
            assert res2 == res3