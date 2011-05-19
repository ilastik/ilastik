import numpy
import sys

from roi import sliceToRoi

from collections import deque
from Queue import Queue, LifoQueue, Empty
from threading import Thread, Event, current_thread, Lock
import greenlet

requestCounterLock = Lock()
requestCounter = 0

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
    
    def connect(self, partner):
        assert partner is None or isinstance(partner, OutputSlot), \
               "InputSlot(name=%s, operator=%s).connect: partner has type %r" \
               % (self.name, self.operator, type(partner))
        
        if self.partner == partner:
            return
        self.disconnect()
        self.partner = partner
        partner.connect(self)
        # do a type check
        self.connectOk(self.partner)
        self.notifyConnect()
        
    def notifyConnect(self):
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
                greenlet.getcurrent().parent.switch(None)
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
        return self.partner.axistags

    
class OutputSlot(object):
    def __init__(self, name, operator = None):
        self.name = name
        self.operator = operator
        if not hasattr(self, "_dtype"):
            self._dtype = None
        if not hasattr(self, "_shape"):
            self._shape = None
        if not hasattr(self, "_axistags"):
            self._axistags = None
        self.partners = []
    
    def connect(self, partner):
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
        return self._dtype
        
    @property
    def shape(self):
        assert self._shape is not None, "cannot access shape on Slot %s, of %r - operator did not provide the info !" % (self.name,self.operator)
        return self._shape

    @property
    def axistags(self):
        assert self._axistags is not None, "cannot access shape on Slot %s, of %r Not Connected !" % (self.name,self.operator)
        return self._axistags


class PartialMultiInputSlot(InputSlot):
    
    def __init__(self, name, operator, parent):
        InputSlot.__init__(self,name, operator)
        self.operator = operator
        self.name = name
        self.parent = parent
    
    def disconnect(self):
        if self.partner is not None:
            InputSlot.disconnect(self)
            self.parent.removeInputSlot(self)
            
    def notifyConnect(self):
        if self.parent is not None:
            self.parent.notifyPartialConnect(self)
            
    def __setitem__(self, key, value):
        if self.parent is not None:
            self.parent._partialSetItem(self, key, value)


class PartialMultiOutputSlot(OutputSlot):
    
    def __init__(self, name, operator, parent):
        OutputSlot.__init__(self,name, operator)
        self.operator = operator
        self.name = name
        self.parent = parent
    
    def getOutSlotFromOp(self, key, destination):
        self.parent.getOutSlotFromOp(self, key, destination)


class MultiInputSlot(object):
    def __init__(self, name, operator = None):
        self.name = name
        self.operator = operator
        self.partner = None
        self.inputSlots = []
    
    def __getitem__(self, key):
        return self.inputSlots[key]
    
    def __len__(self):
        return len(self.inputSlots)
        
    def _appendNew(self):
        islot = PartialMultiInputSlot(self.name+"3%d" % len(self), self.operator, self)
        self.inputSlots.append(islot)
        return islot
    
    def _insertNew(self, index):
        islot = PartialMultiInputSlot(self.name+"3%d" % index, self.operator)
        self.inputSlots.insert(index,islot)
        for i, isl in enumerate(self.inputSlots[index+1:]):
            isl.name = self.name+"3%d" % index + i + 1
        return islot
    
    def connect(self,partner):
        if isinstance(partner, MultiOutputSlot):
            if self.partner == partner:
                return
            self.disconnect()
            self.partner = partner
            partner.connect(self)
            # do a type check
            self.connectOk(self.partner)
            
            # create new self.inputSlots for each outputSlot 
            # of our partner    
            for i,p in enumerate(self.partner):
                islot = self._appendNew()
                self.inputSlots.append(islot)
                self.partner[i].connect(islot)

            self.operator.notifyConnect(self)
            
        elif isinstance(partner, OutputSlot):
            print self.name, " Connecting to ", partner.name
            for i, slot in enumerate(self):
                if slot.partner == partner:
                    raise RuntimeError("MultiInputSlot: connect is already connect to this partner %r" % partner)
            slot = self._appendNew()
            slot.connect(partner)
            self.notifyPartialConnect(slot)
            print "selflenbg", len(self)

    def notifyPartialConnect(self, slot):
        # notify operator of connection
        # the operator may do a compatibility
        # check that involves
        # more then one slot
        if self.operator is not None:
            index = self.inputSlots.index(slot)
            self.operator.notifyPartialMultiConnect(self, slot, index)
        
    def disconnect(self):
        if self.partner is not None:
            self.partner.disconnectSlot(self)
        self.inputSlots = []
        self.partner = None
    
    def removeInputSlot(self, inputSlot):
        inputSlot.disconnect()
        index = self.inputSlots.index(inputSlot)
        self.inputSlots.remove(inputSlot)
        for i, slot in enumerate(self[index:]):
            slot.name = self.name+"3%d" % index + i
        # reconfigure operator
        self.notifyConnect()
 
    def _partialSetItem(self, slot, key, value):
        index = self.inputSlots.index(slot)
        self.operator.multiSlotSetItem(self,slot,index, key,value)   
    
    #TODO RENAME? createInstance
    # def __copy__ ?
    def getInstance(self, operator):
        s = MultiInputSlot(self.name, operator)
        return s
            
    def setDirty(self):
        assert self.operator is not None, "Slot %s cannot be set dirty, slot not belonging to any actual operator instance" % self.name
        self.operator.setDirty(self)
    
    def connectOk(self, partner):
        # reimplement this method
        # if you want a more involved
        # type checking
        return True

class MultiOutputSlot(object):
    def __init__(self, name, operator = None):
        self.name = name
        self.operator = operator
        self.partners = []
        self.outputSlots = []
    
    def __getitem__(self, key):
        return self.outputSlots[key]
    
    def __setitem__(self, key, value):
        slots = self.outputSlots[key]
        for s in slots:
            s.disconnect()
        
        self.outputSlots[key] = value

        slots = self.outputSlots[key]
        for s in slots:
            index = self.outputSlots.index(s)
            for p in self.partners:
                s.connect(p[index])
        
    def __len__(self):
        return len(self.outputSlots)
    
    def append(self, outputSlot):
        self.outputSlots.append(outputSlot)
        for p in self.partners:
            pslot = p._appendNew()
            outputSlot.connect(pslot)
    
    def insert(self, index, outputSlot):
        self.outputSlots.append(outputSlot)
        for p in self.partners:
            pslot = p._insertNew(index)
            outputSlot.connect(pslot)
        
    def remove(self, outputSlot):
        index = self.outputSlots.index(outputSlot)
        self.pop(index)
    
    def pop(self, index = -1):
        oslot = self.outputSlots.pop(index)
        oslot.disconnect()
        
    def connect(self, partner):
        if partner not in self.partners:
            self.partners.append(partner)
        #Re-run the connect anyway, because we might want to
        #propagate information like this
        partner.connect(self)
        
    def disconnect(self):
        for p in self.partners:
            p.disconnect()

    def clearAllSlots(self):
        slots = self[:]
        for s in slots:
            self.remove(s)
    
    #TODO RENAME? createInstance
    # def __copy__ ?
    def getInstance(self, operator):
        s = MultiOutputSlot(self.name, operator)
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


class Operator(object):
    inputSlots  = []
    outputSlots = []
    name = ""
    
    def __init__(self, graph):
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
    
    def notifyPartialMultiConnect(self, multislot, slot, index):
        pass
    
    def getOutSlot(self, slot, key, result):
        return None

    def getPartialMultiOutSlot(self, multislot, slot, index, key, result):
        return None
    
    def setInSlot(self, slot, key, value):
        pass

    def setPartialMultiInSlot(self,multislot,slot,index, key,value):
        pass


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
            # return something that can be handeled by the innnerWork function
            ret = [None, gr, event, thread]
            return ret
        task = [runnerClosure, gr, event, thread]
        self.tasks.put(task)
        return event
    
    def finalize(self):
        print "Finalizing Graph..."
        self.running = False
    
    def registerOperator(self, op):
        self.operators.append(op)
    
    def removeOperator(self, op):
        assert op in self.operators, "Operator %r not a registered Operator" % op
        self.operators.remove(op)
        op.disconnect()