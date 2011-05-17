import numpy
import sys

from roi import sliceToRoi

from collections import deque
from Queue import Queue, LifoQueue, Empty
from threading import Thread, Event, current_thread, Lock
import greenlet

requestCounterLock = Lock()
requestCounter = 0

class InputSlot(object):
    def __init__(self, name, operator = None):
        self.name = name
        self.operator = operator
        self.partner = None
    
    def connect(self,partner):
        #assert isinstance(partner, OutputSlot), "partner has type %r" % type(partner)
        
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
    
    #TODO RENAME? createInstance
    # def __copy__ ?
    def getInstance(self, operator):
        s = InputSlot(self.name, operator)
        return s
            
    def setDirty(self):
        assert self.operator is not None, "Slot %s cannot be set dirty, slot not belonging to any actual operator instance" % self.name
        self.operator.setDirty(self)
    
    def connectOk(self, partner):
        # reimplement this method
        # if you want a more involved
        # type checking
        return True

    def __getitem__(self, key):
        assert self.partner is not None, "cannot do __getitem__ on Slot %s, of %r Not Connected!" % (self.name,self.operator)
        assert issubclass(type(key[-1]),numpy.ndarray) or callable(key[-1]), "This Inputslot %s of operator %s \
            requires a result variable of type numpy.ndarray as last \
            argument to __getitem__ in which \
            self.realGetItem(key) results will be stored" %(self.name,self.operator.name)
        
        if callable(key[-1]):
            customClosure = key[-1]
            key = key[:-1]
        else:
            customClosure = None

        origkey = key
            
        result = key[-1]
        
        if type(key[0]) is tuple:
            # for convenience in calling
            # the user may reuse the packed tuple
            # we expand here
            key = key[0][:]
        else:
            # the user provided a real __getitem__ call
            # don't expand
            key = key[:-1]
        
        #FIXME: I use ndarray here, because?? -> thread safe
        greenletContainer = numpy.ndarray((1,), dtype = object) #FIXME dangerous? garbage collection
        event = self.graph.putTask(self.partner.__getitem__, origkey, greenletContainer, customClosure)
                        
        def closureGetter():
            greenletContainer[0] = greenlet.getcurrent()
            if not event.isSet():
                # --> wait until results are ready
                greenlet.getcurrent().parent.switch(None)
            greenletContainer[0] = None
            return result
            
        return closureGetter
            
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
        assert self.operator is not None, "cannot do __getitem__ on Slot %s, of %r -> now operator !!" % (self.name,self.operator) 
        # check wether last key element is
        # is a output storage object (always ndarray)
        # or wether we have to allocate storage...
        if type(key) is tuple and issubclass(type(key[-1]),numpy.ndarray):
            result = key[-1]
            if type(key[0]) is tuple:
                # for convenience in calling
                # the user may reuse the packed tuple
                # we expand here
                key = key[0][:]
        else:
            if type(key) is tuple and type(key[0]) is tuple:
                # for convenience in calling
                # the user may reuse the packed tuple
                # we expand here
                key = key[0][:]
            tk = key
            if type(key) is not tuple:
                tk = (key,)
            result = self.allocateStorage(tk)            
        
        gr = greenlet.getcurrent()
        
        global requestCounter
        requestCounterLock.acquire()
        requestCounter += 1
        requestCounterLock.release()
        
        if gr.parent is None:
            temp = numpy.ndarray((1,), dtype = object)
            event = self.graph.putTask(self.__getitem__, (key, result), temp)
            # loop to allow ctrl-c
            while not event.isSet():
                event.wait(timeout = 0.25) #in seconds
            print "Request finished (needed %d requests to sastisfy me)" % (requestCounter)
            
            requestCounterLock.acquire()
            requestCounter = 0
            requestCounterLock.release()
            
        else:
            self.operator.getOutSlot(self, key, result)
        
        return result

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
        assert self._shape is not None, "cannot acess shape on Slot %s, of %r - operator did not provide the info !" % (self.name,self.operator)
        return self._shape

    @property
    def axistags(self):
        assert self._axistags is not None, "cannot acess shape on Slot %s, of %r Not Connected !" % (self.name,self.operator)
        return self._axistags


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
    
    def getOutSlot(self, slot, key, result):
        return None
    
    def setInSlot(self, slot, key, value):
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
            func(key)
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
        assert op in self.operators, "Operator %r not a registered Operator" %op
        self.operators.remove(op)
        op.disconnect()