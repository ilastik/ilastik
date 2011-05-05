import numpy
import sys

from roi import sliceToRoi

from collections import deque
from Queue import Queue, LifoQueue, Empty
from threading import Thread, Event

sys.setrecursionlimit(10000)

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
        assert issubclass(type(key[-1]),numpy.ndarray), "This Inputslot %s of operator %s \
            requires a result variable of type numpy.ndarray as last \
            argument to __getitem__ in which results will be stored" %(self.name,self.operator.name)
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
        tasks = self.graph.tasks
#        if type(key) is not tuple:
#            key = (key,)
        event = self.graph.putTask(self.partner.__getitem__, origkey,result)
        
        def lambdaGetter():
            #process any unprocessed tasks
            while not event.isSet():
                try:
                    task = tasks.get(False)
                except Empty:
                    # task queue empty, e.g. our
                    # result is being calculated by some worker
                    # -> just wait for the result after loop
                    continue
#            try:
                # doe something useful while waiting for result, e.g.
                # calculate an store result of some task
                task[0](task[1]) 
                # set event, thus indicating result is ready
                task[3].set()
#            except:
#                pass              
            # wait until whatever Worker has
            # calculated the desired result 
            # that was requested
            event.wait()
            # finally return the result
            return result[0]
        
        return lambdaGetter
            

    def __setitem_(self, key, value):
        assert self.operator is not None, "cann do __setitem__ on Slot %s -> no operator !!"
        self.operator.setInSlot(self,key,value)
        
    @property
    def graph(self):
        return self.operator.graph

    @property
    def dtype(self):
        return self.partner.dtype
            
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
        if not hasattr(self,"_dtype"):
            self._dtype = None
        if not hasattr(self,"_shape"):
            self._shape = None
        if not hasattr(self,"_axistags"):
            self._axistags = None
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
        s._shape = self._shape
        s._dtype = self._dtype
        s._axistags = self._axistags
        return s

    def allocateStorage(self,key):
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
        
        self.operator.getOutSlot(self,key,result)
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
        assert self._shape is not None,  "cannot acess shape on Slot %s, of %r - operator did not provide the info !" % (self.name,self.operator)
        return self._shape

    @property
    def axistags(self):
        assert self._axistags is not None,  "cannot acess shape on Slot %s, of %r Not Connected !" % (self.name,self.operator)
        return self._axistags



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



class Worker(Thread):
    def __init__(self, graph):
        Thread.__init__(self)
        self.graph = graph
        self.working = False
        pass
    
    def run(self):
        print "Initializing Worker%d" % len(self.graph.workers)
        while self.graph.running:
            #blocking call
            try:
                # use a timeout so that
                # we do not miss the quit event of the graph
                task = self.graph.tasks.get(False)#timeout = 1.0)
            except Empty:
                continue
            if self.graph.running:
                #execute the function
                self.working = True
                task[0](task[1])
                task[3].set() #this is the lock object
                self.working = False
        print "Finalized Worker"
                
class Graph(object):
    
    def __init__(self, numThreads = 2):
        self.operators = []
        self.tasks = Queue() #Lifo <-> depth first, fifo <-> breath first
        self.workers = []
        self.running = True
        self.numThreads = numThreads
        
        for i in xrange(self.numThreads):
            w = Worker(self)
            self.workers.append(w)
            w.start()
    
    def putTask(self, func, key, result):
        event = Event()
        self.tasks.put([func, key,result, event])
        return event
    
    def finalize(self):
        print "Finalizing Graph..."
        self.running = False
        if len(self.workers) > 0:
            for w in self.workers:
                w.join()
            
    
    def registerOperator(self, op):
        self.operators.append(op)
        pass
    
    def removeOperator(self, op):
        assert op in self.operators, "Operator %r not a registered Operator" %op
        self.operators.remove(op)
        op.disconnect()