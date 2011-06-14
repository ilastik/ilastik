import numpy
import sys
import copy
from roi import sliceToRoi

from collections import deque
from Queue import Queue, LifoQueue, Empty
from threading import Thread, Event, current_thread, Lock
import greenlet

requestCounterLock = Lock()
requestCounter = 0

#sys.setrecursionlimit(1000)

def itersubclasses(cls, _seen=None):
    """
    itersubclasses(cls)

    Generator over all subclasses of a given class, in depth first order.

    >>> list(itersubclasses(int)) == [bool]
    True
    >>> class A(object): pass
    >>> class B(A): pass
    >>> class C(A): pass
    >>> class D(B,C): pass
    >>> class E(D): pass
    >>> 
    >>> for cls in itersubclasses(A):
    ...     print(cls.__name__)
    B
    D
    E
    C
    >>> # get ALL (new-style) classes currently defined
    >>> [cls.__name__ for cls in itersubclasses(object)] #doctest: +ELLIPSIS
    ['type', ...'tuple', ...]
    """
    
    if not isinstance(cls, type):
        raise TypeError('itersubclasses must be called with '
                        'new-style classes, not %.100r' % cls)
    if _seen is None: _seen = set()
    try:
        subs = cls.__subclasses__()
    except TypeError: # fails only when cls is type
        subs = cls.__subclasses__(cls)
    for sub in subs:
        if sub not in _seen:
            _seen.add(sub)
            yield sub
            for sub in itersubclasses(sub, _seen):
                yield sub


class Operators(object):
    
    operators = {}
    
    @classmethod
    def register(cls, opcls):
        cls.operators[opcls.__name__] = opcls
        print "registered operator %s (%s)", (opcls.name, opcls.__name__)

    @classmethod
    def registerOperatorSubclasses(cls):
        for o in itersubclasses(Operator):
            cls.register(o)


class GetItemRequestObject(object):
    """ Enables the syntax:
        InputSlot[:,:].writeInto(array)
        for loading input data"""
    
    __slots__ = ["_key", "_slot"]
    
    def __init__(self, slot, key):
        self._key = key
        self._slot = slot
    
    def writeInto(self, destination):
        return self._slot.fireRequest(self._key, destination)     
    
    def allocate(self):
        destination = self._slot.allocateStorage(self._key)
        return self.writeInto(destination)
    
    def __call__(self):
        #TODO: remove this convenience function when
        #      everything is ported ?
        return self.allocate()


class InputSlot(object):
    def __init__(self, name, operator = None):
        self.name = name
        self.operator = operator
        self.partner = None
        self.level = 0

    def connectAdd(self, partner):
        if isinstance(self.operator,(OperatorWrapper, Operator)):
            newop = OperatorWrapper(self.operator)
            newop.inputs[self.name].connectAdd(partner)
        else:
            raise RuntimeError("InputSlot: connectAdd called for a inner slot, NOT ALLOWED")        
    
    def connect(self, partner):
        assert partner is None or isinstance(partner, (OutputSlot, MultiOutputSlot)), \
               "InputSlot(name=%s, operator=%s).connect: partner has type %r" \
               % (self.name, self.operator, type(partner))
        
        if self.partner == partner:
            return
        self.disconnect()
        if partner.level > 0:
            partner.disconnectSlot(self)
            print "InputSlot", self.name, "of op", self.operator.name, self.operator
            print "-> Wrapping operator because own level is 0 and partner is", partner.level
            newop = OperatorWrapper(self.operator)
            partner._connect(newop.inputs[self.name])
        else:
            self.partner = partner
            partner._connect(self)
            # do a type check
            self.connectOk(self.partner)
            if self.shape is not None:
                self.notifyConnect()
        
    def notifyConnect(self):
        # notify operator of connection
        # the operator may do a compatibility
        # check that involves
        # more then one slot
        if self.operator is not None:
            self.operator.notifyConnect(self)
        else:
            print "BBBBBBBBBBBBBBBBBBBBBBB operator is NONE", self.name


       
    def disconnect(self):
        if self.partner is not None:
            self.partner.disconnectSlot(self)
        self.partner = None
    
    #TODO RENAME? createInstance
    # def __copy__ ?
    def getInstance(self, operator):
        s = InputSlot(self.name, operator)
        return s
            
    def setDirty(self):
        assert self.operator is not None, \
               "Slot '%s' cannot be set dirty, slot not belonging to any actual operator instance" % self.name
        self.operator.setDirty(self)
    
    def connectOk(self, partner):
        # reimplement this method
        # if you want a more involved
        # type checking
        return True

    def __getitem__(self, key):
        return GetItemRequestObject(self, key)
        
    def fireRequest(self, key, destination):
        assert self.partner is not None, "cannot do __getitem__ on Slot %s, of %r Not Connected!" % (self.name, self.operator)
        
        customClosure = None
        
        #FIXME: I use ndarray here, because?? -> thread safe !
        greenletContainer = numpy.ndarray((1,), dtype = object) #FIXME dangerous? garbage collection
        event = self.graph.putTask(self.partner.fireRequest, (key,destination), greenletContainer, customClosure)
                        
        def closureGetter():
            greenletContainer[0] = greenlet.getcurrent()
            if not event.isSet():
                # --> wait until results are ready
                if greenlet.getcurrent().parent != None:
                    greenlet.getcurrent().parent.switch(None)
                else:
                    # loop to allow ctrl-c signal !
                    while not event.isSet():
                        event.wait(timeout = 0.25) #in seconds
            greenletContainer[0] = None
            return destination
            
        return closureGetter

    def allocateStorage(self, key):
        start, stop = sliceToRoi(key, self.shape)
        storage = numpy.ndarray(stop - start, dtype=self.dtype)
        return storage
            
    def __setitem__(self, key, value):
        assert self.operator is not None, "cannot do __setitem__ on Slot '%s' -> no operator !!"
        self.operator.setInSlot(self,key,value)
        
    @property
    def graph(self):
        return self.operator.graph

    @property
    def dtype(self):
        return self.partner.dtype
            
    @property
    def shape(self):
        assert self.partner is not None, "cannot acess shape on Slot '%s', of %r Not Connected !" % (self.name,self.operator)
        return self.partner.shape

    @property
    def axistags(self):
        assert self.partner is not None, "cannot acess shape on Slot '%s', of %r Not Connected !" % (self.name,self.operator)
        if self.partner.name is not "Sigma":
            assert self.partner.axistags is not None, "%s, %s" % (self.name, self.partner.name)
        return self.partner.axistags

    
class OutputSlot(object):
    def __init__(self, name, operator = None):
        self.name = name
        self.level = 0
        self.operator = operator
        if not hasattr(self, "_dtype"):
            self._dtype = None
        if not hasattr(self, "_shape"):
            self._shape = None
        if not hasattr(self, "_axistags"):
            self._axistags = None
        self.partners = []
    
    def _connect(self, partner):
        if partner not in self.partners:
            self.partners.append(partner)
        #Re-run the connect anyway, because we might want to
        #propagate information like this
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

    #FIXME __copy__ ?
    def getInstance(self, operator):
        s = OutputSlot(self.name, operator)
        s._shape = self._shape
        s._dtype = self._dtype
        s._axistags = self._axistags
        return s

    def allocateStorage(self, key):
        start, stop = sliceToRoi(key, self.shape)
        storage = numpy.ndarray(stop - start, dtype=self.dtype)
        return storage

    def __getitem__(self, key):
        return GetItemRequestObject(self,key)

    def fireRequest(self, key, destination):
        assert self.operator is not None, "cannot do __getitem__ on Slot %s, of %r -> now operator !!" % (self.name,self.operator) 
                
        gr = greenlet.getcurrent()
        
        global requestCounter
        requestCounterLock.acquire()
        requestCounter += 1
        requestCounterLock.release()
        
        if gr.parent is None:
            temp = numpy.ndarray((1,), dtype = object)
            event = self.graph.putTask(self.fireRequest, (key, destination), temp)
            # loop to allow ctrl-c
            while not event.isSet():
                event.wait(timeout = 0.25) #in seconds
            print "Request finished (needed %d requests to satisfy me)" % (requestCounter)
            
            requestCounterLock.acquire()
            requestCounter = 0
            requestCounterLock.release()
            
        else:
            self.getOutSlotFromOp(key, destination)
        
        return destination
    
    def getOutSlotFromOp(self, key, destination):
        self.operator.getOutSlot(self, key, destination)


    def __setitem__(self, key, value):
        for p in self.partners:
            p[key] = value

    @property
    def graph(self):
        return self.operator.graph
    
    @property
    def dtype(self):
        #assert self._dtype is not None, "cannot access dtype on Slot %s, of %r - operator did not provide the info !" % (self.name,self.operator)
        return self._dtype
        
    @property
    def shape(self):
        #assert self._shape is not None, "cannot access shape on Slot %s, of %r - operator did not provide the info !" % (self.name,self.operator)
        return self._shape

    @property
    def axistags(self):
        #assert self._axistags is not None, "cannot access axistags on Slot %s, of %r Not Connected !" % (self.name,self.operator)
        return self._axistags



class MultiInputSlot(object):
    def __init__(self, name, operator = None, level = 1):
        self.name = name
        self.operator = operator
        self.partner = None
        self.inputSlots = []
        self.level = level
    
    def __getitem__(self, key):
        return self.inputSlots[key]
    
    def __len__(self):
        return len(self.inputSlots)
        
    def resize(self, size):
        while size > len(self):
            self._appendNew()
            
        while size < len(self):
            self._removeInputSlot(self[-1])
                    
    def _appendNew(self):
        if self.level <= 1:
            islot = InputSlot(self.name ,self)
        else:
            islot = MultiInputSlot(self.name,self, level = self.level - 1)
        index = len(self) - 1
        self.inputSlots.append(islot)
        if self.partner is not None:
            if len(self.partner) >= len(self):
                self.partner[index]._connect(islot)            
        return islot
    
    def _insertNew(self, index):
        if self.level == 1:
            islot = InputSlot(self.name,self)
        else:
            islot = MultiInputSlot(self.name,self, level = self.level - 1)
        self.inputSlots.insert(index,islot)
        for i, isl in enumerate(self.inputSlots[index+1:]):
            isl.name = self.name
        if self.partner is not None:
            if len(self.partner) > index:
                islot.connect(self.partner[index])                    
        return islot
    
    def cloneConnectionsFrom(self, otherInputSlot):
        self.resize(len(otherInputSlot))
        for i, slot in enumerate(otherInputSlot):
            if slot.level == 0:
                self[i].connect(slot.partner)
            else:
                self[i].cloneConnectionsFrom(slot)
    
    
    def connectAdd(self, partner):
        self.partner = None
        if partner.level == self.level - 1 and not isinstance(self.operator, OperatorWrapper):
            slot = self._appendNew()
            partner._connect(slot)
        elif partner.level == self.level - 1 and isinstance(self.operator, OperatorWrapper):
                if len(partner)> len(self):
                    self.resize(len(partner))
                for i, pslot in enumerate(partner):
                    self.operator._ensureInputSize(len(partner))
                    innerOpSlot = self.operator.innerOperators[i].inputs[self.name]
                    if innerOpSlot.level > 0:
                        innerOpSlot.connectAdd(pslot)
                    else:
                        innerOpSlot.connect(pslot)
                    self[i].cloneConnectionsFrom(innerOpSlot)
                    
        elif partner.level > self.level - 1:
            if isinstance(self.operator,(OperatorWrapper, Operator)):
                newop = self.operator
                while partner.level >= newop.inputs[self.name].level:
                    newop = OperatorWrapper(newop)
                newop.inputs[self.name].connectAdd(partner)
            else:
                raise RuntimeError("trying to add a connection to a inner slot - NOT ALLOWED")
        else:
            raise RuntimeError("MultiInputSlot: undhandeled connectAdd case! ")
        
    def connect(self,partner):
        if self.partner == partner:
            return
        if partner is not None:
            if partner.level == self.level:
                self.disconnect()
                self.partner = partner
                partner._connect(self)
                # do a type check
                self.connectOk(self.partner)
                
                # create new self.inputSlots for each outputSlot 
                # of our partner   
                print "MultiInputSlot connecdt", self.operator, self.operator.name, len(self), partner.operator, partner.operator.name, len(partner)
                if len(self) != len(partner):
                    self.resize(len(partner))
                for i,p in enumerate(self.partner):
                    self.partner[i]._connect(self[i])

                self.operator.notifyConnect(self)
                
            elif partner.level < self.level:
                self.partner = partner
                for i, slot in enumerate(self):                
                    slot.connect(partner)
                    if self.operator is not None:
                        self.operator.notifyPartialMultiConnect((self,slot), (i,))
            elif partner.level > self.level:
                partner.disconnectSlot(self)
                #print "MultiInputSlot", self.name, "of op", self.operator.name, self.operator
                print "-> Wrapping operator because own level is", self.level, "partner level is", partner.level
                if isinstance(self.operator,(OperatorWrapper, Operator)):
                    newop = OperatorWrapper(self.operator)
                    partner._connect(newop.inputs[self.name])
                    #assert newop.inputs[self.name].level == self.level + 1, "%r, %s, %s, %d, %d" % (self.operator, self.operator.name, self.name, newop.inputs[self.name].level, self.level) 
                else:
                    raise RuntimeError("Trying to connect a higher order slot to a subslot - NOT ALLOWED")
            else:
                pass

    def notifyConnect(self, slot):
        index = self.inputSlots.index(slot)
        self.operator.notifyPartialMultiConnect((self,slot), (index,))
    
    def notifyPartialMultiConnect(self, slots, indexes):        
        index = self.inputSlots.index(slots[0])
        self.operator.notifyPartialMultiConnect( (self,) + slots, (index,) +indexes)

    def notifyDisconnect(self, slot):
        index = self.inputSlots.index(slot)
        self.operator.notifyPartialMultiDisconnect((self, slot), (index,))
    
    def notifyPartialMultiDisconnect(self, slots, indexes):
        index = self.inputSlots.index(slots[0])
        self.operator.notifyPartialMultiDisconnect((self,) + slots, (index,) + indexes)
        
    def notifyPartialMultiSlotRemove(self, slots, indexes):
        if len(slots)>0:
            index = self.inputSlots.index(slots[0])
            indexes = (index,) + indexes
        self.operator.notifyPartialMultiSlotRemove((self,) + slots, indexes)
        
    def disconnect(self):
        if self.partner is not None:
            self.partner.disconnectSlot(self)
            self.inputSlots = []
            self.partner = None
            self.operator.notifyDisconnect(self)
    
    def removeSlot(self, index, notify = True):
        slot = index
        if type(index) is int:
            slot = self[index]
        self._removeInputSlot(slot, notify)
    
    def _removeInputSlot(self, inputSlot, notify = True):
        index = self.inputSlots.index(inputSlot)
        self.inputSlots.remove(inputSlot)
        inputSlot.disconnect()
        for i, slot in enumerate(self[index:]):
            slot.name = self.name+"3%d" % (index + i)
        
        # notify parent operator of slot removal
        # index is the number of the slots while it
        # was still there
        if notify:
            self.notifyPartialMultiSlotRemove((),(index,))

    def _partialSetItem(self, slot, key, value):
        index = self.inputSlots.index(slot)
        self.operator.multiSlotSetItem(self,slot,index, key,value)   
    
    #TODO RENAME? createInstance
    # def __copy__ ?
    def getInstance(self, operator):
        s = MultiInputSlot(self.name, operator, level = self.level)
        return s
            
    def setDirty(self):
        assert self.operator is not None, "Slot %s cannot be set dirty, slot not belonging to any actual operator instance" % self.name
        self.operator.setDirty(self)
    
    def connectOk(self, partner):
        # reimplement this method
        # if you want a more involved
        # type checking
        return True

    @property
    def graph(self):
        return self.operator.graph


class MultiOutputSlot(object):
    def __init__(self, name, operator = None, level = 1):
        self.name = name
        self.operator = operator
        self.partners = []
        self.outputSlots = []
        self.level = level
    
    def __getitem__(self, key):
        return self.outputSlots[key]
    
    def __setitem__(self, key, value):
        slot = self.outputSlots[key]
        if slot != value:
            slot.disconnect()
            self.outputSlots[key] = value
    
            oldslot = slot        
            newslot = value
            for p in oldslot.partners:
                newslot._connect(p)
        
    def __len__(self):
        return len(self.outputSlots)
    
    def append(self, outputSlot):
        outputSlot.operator = self
        self.outputSlots.append(outputSlot)
        index = len(self.outputSlots) - 1
        for p in self.partners:
            p.resize(len(self))
            outputSlot._connect(p.inputSlots[index])
    
    def insert(self, index, outputSlot):
        outputSlot.operator = self
        self.outputSlots.append(outputSlot)
        for p in self.partners:
            pslot = p._insertNew(index)
            outputSlot._connect(pslot)
        
    def remove(self, outputSlot):
        index = self.outputSlots.index(outputSlot)
        self.pop(index)
    
    def pop(self, index = -1):
        oslot = self.outputSlots.pop(index)
        for p in oslot.partners:
            if isinstance(p.operator, MultiInputSlot):
                p.operator._removeInputSlot(p)
        oslot.disconnect()
        
    def _connect(self, partner):
        if partner not in self.partners:
            self.partners.append(partner)
        #Re-run the connect anyway, because we might want to
        #propagate information like this
        partner.connect(self)
        
    def disconnect(self):
        slots = self[:]
        for s in slots:
            s.disconnect()

    def disconnectSlot(self, partner):
        if partner in self.partners:
            self.partners.remove(partner)

    def clearAllSlots(self):
        slots = self[:]
        for s in slots:
            self.remove(s)
            
    def resize(self, size):
        while len(self) < size:
            if self.level == 1:
                slot = OutputSlot(self.name,self)
            else:
                slot = MultiOutputSlot(self.name,self, level = self.level - 1)
            index = len(self)
            self.outputSlots.append(slot)
            for p in self.partners:
                p.resize(size)
                slot._connect(p[index])
        
        while len(self) > size:
            self.pop()

        for p in self.partners:
            p.resize(size)
            assert len(p) == len(self)
            
    def getOutSlot(self, slot, key, result):
        index = self.outputSlots.index(slot)
        return self.operator.getPartialMultiOutSlot((self, slot,),(index,),key, result)

    def getPartialMultiOutSlot(self, slots, indexes, key, result):
        try:
            index = self.outputSlots.index(slots[0])
        except:
            #print self.name, self.operator.name, self.operator, slots
            raise
        return self.operator.getPartialMultiOutSlot((self,) + slots, (index,) + indexes, key, result)
    
    #TODO RENAME? createInstance
    # def __copy__ ?
    def getInstance(self, operator):
        s = MultiOutputSlot(self.name, operator, level = self.level)
        return s
            
    def setDirty(self):
        for partner in self.partners:
            partner.setDirty(self)
    
    def connectOk(self, partner):
        # reimplement this method
        # if you want a more involved
        # type checking
        return True

    def getOutSlotFromOp(self, slot, key, destination):
        index = self.outputSlots.index(slot)
        self.operator.getPartialMultiOutSlot(self, slot, index, key, destination)

    @property
    def graph(self):
        return self.operator.graph

class Operator(object):
    inputSlots  = []
    outputSlots = []
    name = ""
    
    def __init__(self, graph):
        self.operator = None
        self.inputs = {}
        self.outputs = {}
        self.graph = graph
        #provide simple default name for lazy users
        if self.name == "": 
            self.name = type(self).__name__
        assert self.graph is not None, "Operators must be given a graph, they cannot exist alone!" 
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
            # when the corresponding input slots
            # of the partner operators are created       
        self.graph.registerOperator(self)
         
    def disconnect(self):
        for s in self.outputs.values():
            s.disconnect()
        for s in self.inputs.values():
            s.disconnect()

    def setDirty(self, inputSlot = None):
        # simple default implementation
        # -> set all outputs dirty    
        for os in self.outputs.values():
            os.setDirty()

    def notifyConnect(self, inputSlot):
        pass
    
    def notifyPartialMultiConnect(self, slots, indexes):
        pass
   
    def notifyPartialMultiSlotRemove(self, slots, indexes):
        pass
         
    def getOutSlot(self, slot, key, result):
        return None

    def getPartialMultiOutSlot(self, slots, indexes, key, result):
        return None
    
    def setInSlot(self, slot, key, value):
        pass

    def setPartialMultiInSlot(self,slots,indexes, key,value):
        pass

    def notifyDisconnect(self, slot):
        pass
    
    def notifyPartialMultiDisconnect(self, slots, indexes):
        pass



class OperatorWrapper(Operator):
    name = ""
    
    @property
    def inputSlots(self):
        return self._inputSlots
    
    @property
    def outputSlots(self):
        return self._outputSlots
    
    def __init__(self, operator):
        self.inputs = {}
        self.outputs = {}
        self.operator = operator
        self.graph = operator.graph
        self.name = operator.name
        self.comprehensionSlots = 1
        self.innerOperators = []
        self.comprehensionCount = 0
        self.origInputs = self.operator.inputs.copy()
        self.origOutputs = self.operator.outputs.copy()
        print "wrapping ", operator.name, operator
        
        self._inputSlots = []
        self._outputSlots = []
        
        # replicate input slot definitions
        for islot in self.operator.inputSlots:
            level = islot.level + 1
            self._inputSlots.append(MultiInputSlot(islot.name, level = level))

        # replicate output slot definitions
        for oslot in self.outputSlots:
            level = oslot.level + 1
            self._outputSlots.append(MultiOutputSlot(oslot.name, level = level))

                
        # replicate input slots for the instance
        for islot in self.operator.inputs.values():
            level = islot.level + 1
            ii = MultiInputSlot(islot.name, self, level = level)
            self.inputs[islot.name] = ii
            op = self.operator
            while isinstance(op.operator, (Operator, MultiInputSlot)):
                op = op.operator
            op.inputs[islot.name] = ii
        
        # replicate output slots for the instance
        for oslot in self.operator.outputs.values():
            level = oslot.level + 1
            oo = MultiOutputSlot(oslot.name, self, level = level)
            self.outputs[oslot.name] = oo
            op = self.operator
            while isinstance(op.operator, (Operator, MultiOutputSlot)):
                op = op.operator
            op.outputs[oslot.name] = oo

        #connect input slots
        for islot in self.origInputs.values():
            ii = self.inputs[islot.name]
            partner = islot.partner
            islot.disconnect()
            self.operator.inputs[islot.name] = ii
            if partner is not None:
                partner._connect(ii)
                
        self._connectInnerOutputs()


        #connect output slots
        for oslot in self.origOutputs.values():
            oo = self.outputs[oslot.name]            
            partners = copy.copy(oslot.partners)
            oslot.disconnect()
            for p in partners:         
                oo._connect(p)

                    
    def testRestoreOriginalOperator(self):
        #TODO: only restore to the level that is needed, not to the most upper one !
        
        #print "OperatorWrapper testRestoreOriginalOperator", self.name
        needWrapping = False
        for iname, islot in self.inputs.items():
            if islot.partner is not None:
                if islot.partner.level > self.origInputs[iname].level:
                    needWrapping = True
                    
        if needWrapping is False:
            
            if isinstance(self.operator, OperatorWrapper):
                print "Restoring original operator of ", self, self.name
                #print self, self.name
                op = self
                while isinstance(op.operator, (OperatorWrapper)):
                    op = op.operator
                    #print op, op.name
                op.operator.outputs = op.origOutputs
                op.operator.inputs = op.origInputs
                
                for k, islot in self.inputs.items():
                    if islot.partner is not None:
                        op.inputs[k].connect(islot.partner)
        
                for k, oslot in self.outputs.items():
                    for p in oslot.partners:
                        op.outputs[k]._connect(p)
                    

    
    def disconnect(self):
        for s in self.outputs.values():
            s.disconnect()
        for s in self.inputs.values():
            s.disconnect()
        self.testRestoreOriginalOperator()

    def setDirty(self, inputSlot = None):
        # simple default implementation
        # -> set all outputs dirty    
        for os in self.outputs.values():
            os.setDirty()

    def createInnerOperator(self):
        if self.operator.__class__ is not OperatorWrapper:
            opcopy = self.operator.__class__(self.graph)
        else:
            print "creatInnerOperator OperatorWrapper"
            opcopy = OperatorWrapper(self.operator.createInnerOperator())
        return opcopy
    
    def removeInnerOperator(self, op):
        index = self.innerOperators.index(op)
        self.innerOperators.remove(op)
        for name, oslot in self.outputs.items():
            oslot.pop(index)
        op.disconnect()
            
    def _connectInnerOutputs(self):
        for k,mslot in self.outputs.items():
            assert isinstance(mslot,MultiOutputSlot)
                        
#            while len(mslot) > len(self.innerOperators):
#                mslot.pop()
#            while len(mslot) < len(self.innerOperators):
#                mslot.append(self.innerOperators[len(mslot)-1].outputs[mslot.name])

            mslot.resize(len(self.innerOperators))

        for index, innerOp in enumerate(self.innerOperators):
            for mslot in self.outputs.values():
                mslot[index] = innerOp.outputs[mslot.name]
                
#        print self.__class__, self.name, "_connectInnerOutputs"
#        print len(self.innerOperators)
#        for index, innerOp in enumerate(self.innerOperators):
#            for ii, mslot in enumerate(self.outputs.values()):
#                print index, ii, len(mslot)
#        print "finish _connectInnerOutputs"

    def _ensureInputSize(self, numMax = 0):
        
        newInnerOps = []
        maxLen = numMax
        for name, islot in self.inputs.items():
            assert isinstance(islot, MultiInputSlot)
            maxLen = max(len(islot), maxLen)
                
        while maxLen > len(self.innerOperators):
            newop = self.createInnerOperator()
            self.innerOperators.append(newop)
            newInnerOps.append(newop)

        while maxLen < len(self.innerOperators):
            op = self.innerOperators[-1]
            self.removeInnerOperator(op)

        for k,mslot in self.inputs.items():
            mslot.resize(maxLen)
            assert len(mslot) == maxLen
#            for i, slot in enumerate(mslot):
#                if slot.partner is not None:
#                    slot.partner._connect(self.innerOperators[i].inputs[mslot.name])
        return maxLen

    def notifyConnect(self, inputSlot):
        
        maxLen = self._ensureInputSize(len(inputSlot))
        #print "gagagagaga", maxLen, len(inputSlot),len(self.innerOperators)
        for i,islot in enumerate(inputSlot):
            if islot.partner is not None:
                self.innerOperators[i].inputs[inputSlot.name].connect(islot.partner)
                        
        self._connectInnerOutputs()
        
        for k,mslot in self.outputs.items():
            assert len(mslot) == len(self.innerOperators) == maxLen, "%d, %d" % (len(mslot), len(self.innerOperators))        

    
    def notifyPartialMultiConnect(self, slots, indexes):
        #print "OperatorWrapper notifyPartialMultiConnect", self.name, slots, indexes
        numMax = self._ensureInputSize(len(slots[0]))
        
        if slots[1].partner is not None:
            #
            # we have to connect the sub operator only
            # if it is a true inner operator, but not
            # if it is an OperatorWrapper. 
            #
            # why, is unclear.
            #
            if not isinstance(self.innerOperators[indexes[0]], OperatorWrapper):
                self.innerOperators[indexes[0]].inputs[slots[0].name].connect(slots[1].partner)
        else:            
            if isinstance(self.innerOperators[indexes[0]], OperatorWrapper):
                
                if len(indexes)>1:
                    self.innerOperators[indexes[0]].notifyPartialMultiConnect(slots[1:],indexes[1:])
                else:
                    self.innerOperators[indexes[0]].notifyConnect(slots[1],indexes[0])
            else:
                if len(indexes)>1:
                    self.innerOperators[indexes[0]].inputs[slots[0].name].resize(len(slots[1]))
                    for i, islot in enumerate(slots[1]):
                        if islot.partner is not None:
                            self.innerOperators[indexes[0]].inputs[slots[0].name][i].connect(islot.partner)
                else:
                    self.innerOperators[indexes[0]].inputs[slots[0].name].connect(slots[1].partner)
        self._connectInnerOutputs()
        return


    def notifyDisconnect(self, slot):
        self.testRestoreOriginalOperator()
        
    def notifyPartialMultiDisconnect(self, slots, indexes):
        return
        maxLen = 0
        for name, islot in self.inputs.items():
            maxLen = max(len(islot), maxLen)
        
        while len(self.innerOperators) > maxLen:
            op = self.innerOperators[-1]
            self.removeInnerOperator(op)

    def notifyPartialMultiSlotRemove(self, slots, indexes):
        print "OperatorWrapper notifyPartialMultiSlotRemove", slots, indexes, self.name
        if len(indexes) == 1:
            op = self.innerOperators[indexes[0]]
            self.removeInnerOperator(op)
        else:
            self.innerOperators[indexes[0]].notifyPartialMultiSlotRemove(slots[1:], indexes[1:])
    
    def getPartialMultiOutSlot(self, slots, indexes, key, result):
        if len(indexes) == 1:
            #print "getPartialMultiOutSlot", indexes, slots
            return self.innerOperators[indexes[0]].getOutSlot(self.innerOperators[indexes[0]].outputs[slots[0].name], key, result)
        else:
            print "???????????????????????????????????????????????????"
            self.innerOperators[indexes[0]].getPartialMultiOutSlot(slots[1:], indexes[1:], key, result)
        
    def setInSlot(self, slot, key, value):
        #TODO: code this
        pass

    def setPartialMultiInSlot(self,multislot,slot,index, key,value):
        #TODO: code this
        pass




class OperatorGroup(Operator):
    def __init__(self, graph):
        Operator.__init__(self,graph)
        self.createInnerOperators()
        self._connectInnerOutputs()
    
    def createInnerOperators(self):
        # this method must setup the
        # inner operators and connect them (internally)
        pass
        
    def getInnerInputSlots(self):
        # this method must return a hash that
        # contains the inner slots corresponding
        # to the slotname
        pass
    
    def getInnerOutputSlots(self):
        # this method must return a hash that
        # contains the inner slots corresponding
        # to the slotname
        pass
    
    def _connectInnerOutputs(self):
        innerOuts = self.getInnerOutputSlots()
        
        for key, value in innerOuts.items():
            self.outputs[key] = value
    
    def notifyConnect(self, inputSlot):
        innerIns = self.getInnerInputSlots()
        innerIns[inputSlot.name].connect(inputSlot.partner)

    
    def notifyPartialMultiConnect(self, slots, indexes):
        
        innerIns = self.getInnerInputSlots()
        
        innerSlot = innerIns[indexes[0].name]

        for i in range(len(slots)):
            if slots[i].partner is not None:
                innerSlot.connect(slots[i].partner)
                break 
            else:
                innerSlot.resize(len( slots[i] ) )
            innerSlot = innerSlot[indexes[i]]
            
    def notifyDisconnect(self, slot):
        pass
    
    def notifyPartialMultiDisconnect(self, slots, indexes):
        pass
    
    def notifyPartialMultiSlotRemove(self, slots, indexes):
        pass
    
    def getPartialMultiOutSlot(self, slots, indexes, key, result):
        raise RuntimeError("OperatorGroup: getPartialMultiOutSlot, this method should never get called!!")
   
                        
class Worker(Thread):
    def __init__(self, graph):
        Thread.__init__(self)
        self.graph = graph
        self.working = False
        self.daemon = True # kill automatically on application exit!
        self.pendingGreenlets = deque()
        print "Initializing Worker #%d" % len(self.graph.workers)
        pass
    
    def run(self):
        while self.graph.running:
            while not self.graph.tasks.empty() or len(self.pendingGreenlets) > 0:
                task = None
                if len(self.pendingGreenlets) > 0:
                    task = self.pendingGreenlets.popleft()
                    if task[1][0] is not None:
                        task = task[1][0].switch()
                    
                if task is None:
                    try:
                        task = self.graph.tasks.get(False)#timeout = 1.0)
                    except Empty:
                        continue
                    gr = greenlet.greenlet(task[0])
                    task = gr.switch()
                    
                if task is not None:
                    if task[2].isSet():
                        if task[1][0] is not None:
                            task[3].pendingGreenlets.append(task)
        print "Finalized Worker"
                
    
class Graph(object):
    def __init__(self, numThreads = 2):
        self.operators = []
        self.tasks = LifoQueue() #Lifo <-> depth first, fifo <-> breath first
        self.workers = []
        self.running = True
        self.numThreads = numThreads
        
        for i in xrange(self.numThreads):
            w = Worker(self)
            self.workers.append(w)
            w.start()
    
    def putTask(self, func, key, gr, customClosure = None):
        event = Event()
        thread = current_thread()
        
        def runnerClosure():
            func(*key)
            event.set()
            if customClosure is not None:
                customClosure()
            # return something that can be handled by the innnerWork function
            ret = [None, gr, event, thread]
            return ret
        task = [runnerClosure, gr, event, thread]
        self.tasks.put(task)
        return event
    
    def finalize(self):
        print "Finalizing Graph..."
        self.running = False
        for w in self.workers:
            w.join()
    
    def registerOperator(self, op):
        self.operators.append(op)
    
    def removeOperator(self, op):
        assert op in self.operators, "Operator %r not a registered Operator" % op
        self.operators.remove(op)
        op.disconnect()