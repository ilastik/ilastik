class InputSlot(object):
    def __init__(self,name, operator = None):
        self.name = name
        self.operator = operator
        self.partner = None
    
    def connect(self,partner):
        if self.partner == partner:
            return
        self.disconnect()
        self.partner = partner
        
        partner.connect(self)
        
        # do a type check
        self.connectOk(self.partner)
        
        # notify operator of connection
        # the operator may do a compatibility
        # check that involves
        # more then one slot
        if self.operator is not None:
            self.operator.notifyConnect(self)
        
    def disconnect(self):
        if self.partner is not None:
            self.partner.disconnectSlot(self)
        self.partner = None
    
    def getInstance(self, operator):
        s = InputSlot(self.name, operator)
        return s
            
    def setDirty(self):
        assert self.operator is not None, "Slot %s Cannot be set dirty, slot not belonging to any actual operator instance" % self.name
        self.operator.setDirty(self)
    
    def connectOk(self, partner):
        # reimplement this method
        # if you want a more involved
        # type checking
        return True
    
    def __getitem__(self, key):
        assert self.partner is not None,  "cannot do __getitem__ on Slot %s, of %r Not Connected !" % (self.name,self.operator)
        print "getItem on Slot %s of Operator %s" % (self.name, self.operator.name)
        return self.partner[key]

    def __setitem_(self, key, value):
        assert self.operator is not None, "cann do __setitem__ on Slot %s -> no operator !!"
        self.operator.setInSlot(self,key,value)
        
    @property
    def shape(self):
        assert self.partner is not None,  "cannot acess shape on Slot %s, of %r Not Connected !" % (self.name,self.operator)
        return self.partner.shape

    @property
    def axistags(self):
        assert self.partner is not None,  "cannot acess shape on Slot %s, of %r Not Connected !" % (self.name,self.operator)
        return self.partner.axistags


    
class OutputSlot(object):
    def __init__(self,name,operator = None):
        self.name = name
        self.provider = None
        self.operator = operator
            
        self.partners = []
    
    def connect(self,partner):
        self.partners.append(partner)
        partner.connect(self)
        
    def disconnect(self):
        for p in self.partners:
            p.disconnect()
            
    def disconnectSlot(self, partner):
        if partner in self.partners:
            self.partners.remove(partner)
            partner.disconnect()
        
    def setDirty(self):
        for p in self.partners:
            p.setDirty()

    def getInstance(self, operator):
        s = OutputSlot(self.name, operator)
        return s

    def __getitem__(self, key):
        assert self.operator is not None, "cannot do __getitem__ on Slot %s, of %r -> now operator !!" % (self.name,self.operator)
        return self.operator.getOutSlot(self,key)

    def __setitem__(self, key, value):
        for p in self.partners:
            p[key] = value

    
    @property
    def shape(self):
        assert self.shape is not None,  "cannot acess shape on Slot %s, of %r - operator did not provide the info !" % (self.name,self.operator)
        return self.partner.shape

    @property
    def axistags(self):
        assert self.partner is not None,  "cannot acess shape on Slot %s, of %r Not Connected !" % (self.name,self.operator)
        return self.partner.axistags



class Operator(object):
    inputSlots = []
    outputSlots = []
    name = ""
    
    def __init__(self, graph):
        self.inputs = {}
        self.outputs = {}
        self.graph = graph
        
        #provide simple default name for lazy users
        if self.name == "": 
            self.name = type(self).__name__
        
        assert self.graph is not None, "Operators must be given a graph, they cannot exist alone !"
        
        # replicate input slot connections
        # defined for the operator for the instance
        for i in self.inputSlots:
            ii = i.getInstance(self)
            ii.connect(i.partner)
            self.inputs[i.name] = ii
        
        # replicate output slots
        # defined for the operator for the instance 
        for o in self.outputSlots:
            oo = o.getInstance(self)
            self.outputs[o.name] = oo         
            # output slots are connected
            # when the correspondign input slots
            # of the partner operators are created
        
        self.graph.registerOperator(self)
        
    def disconnect(self):
        for s in self.outputs.values():
            s.disconnect()
            
        for s in self.inputs.values():
            s.disconnect()
        
        self.graph = None


    def setDirty(self, inputSlot = None):
        # simple default implementation
        # -> set all outputs dirty
        
        for os in self.outputs.values():
            os.setDirty()


    def notifyConnect(self, inputSlot):
        pass
    
    
    def getOutSlot(self, slot, key):
        return None
    
    def setInSlot(self, slot, key, value):
        pass

class Graph(object):
    
    def __init__(self):
        self.operators = []
        pass
    
    def registerOperator(self, op):
        self.operators.append(op)
        pass
    
    def removeOperator(self, op):
        assert op in self.operators, "Operator %r not a registered Operator" %op
        self.operators.remove(op)
        op.disconnect()