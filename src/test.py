from graph import *


class Op1(Operator):
    inputSlots = []
    outputSlots = [OutputSlot("Output")]
    
    def getOutSlot(self,slot,key):
        return "simple test"
    
class Op2(Operator):
    inputSlots = [InputSlot("Input")]
    outputSlots = [OutputSlot("Output")]
    
    def getOutSlot(self,slot,key):
        return self.inputs["Input"][key]
    
    
class Op3(Operator):
    inputSlots = [InputSlot("Input")]
    outputSlots = [OutputSlot("Output")]
    
    def __init__(self, args):
        Operator.__init__(self,args)
        self.cache = None
    
    def getOutSlot(self,slot,key):
        if self.cache is None:
            self.cache = self.inputs["Input"][key]
        
        return self.cache
    
    def setDirty(self, inputSlot):
        self.cache = None
        Operator.setDirty(self, inputSlot)
    

g = Graph()

o1 = Op1(g)
o2 = Op2(g)
o3 = Op3(g)
o4 = Op2(g)

o2.inputs["Input"].connect(o1.outputs["Output"])
o3.inputs["Input"].connect(o2.outputs["Output"])
o4.inputs["Input"].connect(o3.outputs["Output"])

#o2.disconnect()

print o4.outputs["Output"][:]

print o4.outputs["Output"][:]

o2.setDirty()

print o4.outputs["Output"][:]





