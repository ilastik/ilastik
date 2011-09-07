"""
This module implements the basic flow graph
of the lazyflow module.

Basic usage example:
    
---
import numpy
import lazyflow.graph
from lazyflow.operators.operators import  OpArrayPiper


g = lazyflow.graph.Graph()

operator1 = OpArrayPiper(g)
operator2 = OpArrayPiper(g)

operator1.inputs["Input"].setValue(numpy.zeros((10,20,30), dtype = numpy.uint8))

operator2.inputs["Input"].connect( operator1.outputs["Output"])

result = operator2.outputs["Output"][:].allocate().wait()

g.finalize()
---


"""

import lazyflow
import numpy
import vigra
import sys
import copy
import psutil

if int(psutil.__version__.split(".")[0]) < 1 and int(psutil.__version__.split(".")[1]) < 3:
    print "Lazyflow: Please install a psutil python module version of at least >= 0.3.0"
    sys.exit(1)
    
import os
import time
import gc
import ConfigParser
import string
import itertools

from h5dumprestore import instanceClassToString, stringToClass
from helpers import itersubclasses, detectCPUs
from roi import sliceToRoi, roiToSlice
from collections import deque
from Queue import Queue, LifoQueue, Empty, PriorityQueue
from threading import Thread, Event, current_thread, Lock
import greenlet
import weakref
import threading

greenlet.GREENLET_USE_GC = True #use garbage collection

class DefaultConfigParser(ConfigParser.SafeConfigParser):
    """
    Simple extension to the default SafeConfigParser that
    accepts a default parameter in its .get method and
    returns its valaue when the parameter cannot be found
    in the config file instead of throwing an exception
    """
    def __init__(self):
        ConfigParser.SafeConfigParser.__init__(self)
        if not os.path.exists(CONFIG_DIR+"config"):
            self.configfile = open(CONFIG_DIR+"config", "w+")
        else:
            self.configfile = open(CONFIG_DIR+"config", "r+")
        self.readfp(self.configfile)
        self.configfile.close()
    
    def get(self, section, option, default = None):
        """
        accepts a default parameter and returns its value
        instead of throwing an exception when the section
        or option is not found in the config file
        """
        try:
            ans = ConfigParser.SafeConfigParser.get(self, section, option)
            print ans
            return ans
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError), e:
            if default is not None:
                if e == ConfigParser.NoSectionError:
                    self.add_section(section)
                    self.set(section, option, default)
                if e == ConfigParser.NoOptionError:
                    self.set(section, option, default)
                return default
            else:
                raise e

try:
    if LAZYFLOW_LOADED == None:
        pass
except:
    LAZYFLOW_LOADED = True
    
    CONFIG_DIR = os.path.expanduser("~/.lazyflow/")
    if not os.path.exists(CONFIG_DIR):
        os.mkdir(CONFIG_DIR)
    CONFIG = DefaultConfigParser()


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
        cls.operators.pop("OperatorGroup")
        cls.operators.pop("OperatorWrapper")
        #+cls.operators.pop("Operator")


class CopyOnWriteView(object):
    
    def __init__(self, shape, dtype):
        self._data = None
        self._allocated = False
        self.shape = shape
        self.dtype = dtype
        
    def __setitem__(self,key, value):
        if key == slice(None,None):
            if isinstance(value, numpy.ndarray):
                self._data = value
                self._allocated = False
                return value
        if self._allocated is False:
            temp = None
            if self._data is not None:
                temp = self._data
            self._data = numpy.ndarray(self.shape, self.dtype)
            if temp is not None:
                self._data[:] = temp
            self._allocated = True
        self._data[key] = value
        return value
    
    def __getitem__(self,key):
        return self._data[key]

      
      
class GetItemWriterObject(object):
    """
    Enables the syntax:

    InputSlot[:,:].writeInto(array)
    InputSlot[:,:].allocate()
    
    for requesting data from an input or output slot of an operator.
    
    An instance of this class is returned by a call to a __getitem__ (i.e. [key])
    method call of any InputSlot or OutputSlot.
    """
    
    __slots__ = ["_key", "_start", "_stop","_slot"]
    
    def __init__(self, slot, key):
        self._start, self._stop = sliceToRoi(key, slot.shape)
        self._key = roiToSlice(self._start,self._stop)        
        self._slot = slot
    
    def writeInto(self, destination, priority = 0):
        """
        the writeInto method ensures that the data
        that is requested from an InputSlot or OutputSlot is written
        into the specified numpy.ndarray
        
        of course the destination numpy.ndarray must have
        the same size/shape/dimension as the slot will
        return in reponse to the requested key
        """
        if destination is not None:
            diff = self._start - self._stop
            shape = list(destination.shape)
            assert len(diff) == len(shape), "GetItemWriterObject: writeInto - somebody provided result area that has a different shape then the request key itself ! resultarea shape = %r, key = %r" % (destination.shape, self._key)
            assert diff == shape, "GetItemWriterObject: writeInto - somebody provided result area that has a different shape then the request key itself ! resultarea shape = %r, key = %r" % (destination.shape, self._key)
        return  GetItemRequestObject(self, self._slot, self._key, destination, priority)
  
    def allocate(self, axistags = False, priority = 0):
        """
        if the user does not want lazyflow to write calculation
        results into a specific numpy array he can use
        the .allocate() call.
        
        a destination array of required size,shape,dtype will
        be constructed in which the results will be written.
        """
        #destination = self._slot._allocateStorage(self._start, self._stop, axistags)
        #destination = CopyOnWriteView(self._slot.shape, self._slot.dtype)
        return self.writeInto(None, priority)
    
    def __call__(self):
        #TODO: remove this convenience function when
        #      everything is ported ?
        return self.allocate()

      
class CustomGreenlet(greenlet.greenlet):
    
    def __init__(self, func):
        self.lastRequest = None
        self.currentRequest = None
        greenlet.greenlet.__init__(self, func)
        self.thread = None

setattr(current_thread(), "finishedRequestGreenlets", deque())
setattr(current_thread(), "workAvailableEvent", Event())
setattr(current_thread(), "process", psutil.Process(os.getpid()))


class GetItemRequestObject(object):
    """ 
    Enables the syntax
    InputSlot[:,:].writeInto(array).wait() or
    InputSlot[:,:].writeInto(array).notify(someFunction)
    
    the GetItemRequestObject is responsible for the
    .wait() and .notify() part of the above statements.
    
    It is returned by all method calls to an GetItemWriterObject (which
    in turn is returned by a call to the __getitem__ method of an
    InputSlot and OutputSlot) 
    """

    __slots__ = ["_writer", "key", "destination", "slot", "func", "canceled",
                 "_finished", "inProcess", "parentRequest", "childRequests",
                 "graph", "waitQueue", "notifyQueue", "cancelQueue",
                 "_requestLevel", "arg1", "lock", "_priority"]
        
    def __init__(self, writer, slot, key, destination, priority):
        self._writer = writer        
        self.key = key
        self._priority = priority
        self.destination = destination
        self.slot = slot
        self.func = None
        self.canceled = False
        self._finished = False
        self.inProcess = False
        self.parentRequest = None
        self.childRequests = {}
        #self.requestID = graph.lastRequestID.next()
        self.graph = slot.graph
        self.waitQueue = deque()
        self.notifyQueue = deque()
        self.cancelQueue = deque()
        self._requestLevel = -1
        
        if isinstance(slot, InputSlot) and self.slot._value is None:
            self.func = slot.partner.operator.getOutSlot
            self.arg1 = slot.partner            
        elif isinstance(slot, OutputSlot):
            self.func =  slot.operator.getOutSlot
            self.arg1 = slot
        else:
            # we are in the ._value case of an inputSlot
            if self.destination is None:
                self.destination = self.slot._allocateStorage(self._writer._start, self._writer._stop, False)            
            gr = greenlet.getcurrent()
            if hasattr(gr, "currentRequest"):
                self.parentRequest = gr.currentRequest                
            self.wait() #this sets self._finished and copies the results over
        if not self._finished:
            self.lock = Lock()
            #self._putOnTaskQueue()
            #return
            
            gr = greenlet.getcurrent()
            if hasattr(gr, "currentRequest"):
                # we delay the firing of an request until
                # another one arrives 
                # by this we make sure that one call path
                # through the graph is done in one greenlet/thread
                
                lr = gr.lastRequest
                self.parentRequest = gr.currentRequest
                gr.currentRequest.lock.acquire()
                gr.currentRequest.childRequests[self] = self
                self._requestLevel = gr.currentRequest._requestLevel + self._priority + 1
                gr.lastRequest = self
                gr.currentRequest.lock.release()                
                if lr is not None:
                    lr._putOnTaskQueue()

            else:
                # we are in main thread
                self._requestLevel = self._priority

    def _execute(self, gr):
        if self.destination is None:
            self.destination = self.slot._allocateStorage(self._writer._start, self._writer._stop, False)
        gr.currentRequest = self
        assert self.destination is not None
        self.func(self.arg1,self.key, self.destination)
        assert self.destination is not None
        self._finalize()        

    def _putOnTaskQueue(self):
        self.inProcess = True
        self.graph.putTask(self)
    
    def getResult(self):
        assert self._finished, "Please make sure the request is completed before calling getResult()!"
        return self.destination
    
    def adjustPriority(self, delta):
        self.lock.acquire()
        self._priority += delta 
        self._requestLevel += delta
        childs = list(self.childRequests.values())
        self.lock.release()
        for c in childs:
            c.adjustPriority(delta)
        
    def wait(self, timeout = 0):
        """
        calling .wait() on an RequestObject is a blocking
        call that will only return once the results
        of a requested Slot are calculated and stored in
        the  result area.
        """
        if isinstance(self.slot, OutputSlot) or self.slot._value is None:
            self.lock.acquire()
            if not self._finished:
                gr = greenlet.getcurrent()
                if self.inProcess:   
                    if hasattr(gr, "currentRequest"):                         
                        lr = gr.lastRequest
                        if lr is not None:
                            lr._putOnTaskQueue()
                        self.waitQueue.append((gr.thread, gr.currentRequest, gr))
                        self.lock.release()                    
                        gr.parent.switch(None)
                    else:
                        tr = current_thread()                    
                        cgr = CustomGreenlet(self.wait)
                        cgr.currentRequest = self
                        cgr.thread = tr                        
                        self.lock.release()
                        cgr.switch(self)
                        self._waitFor(cgr,tr) #wait for finish
                else:
                    if hasattr(gr, "currentRequest"):
                        lr = gr.lastRequest
                        if lr == self:
                            gr.lastRequest = None
                        elif lr is not None:
                            lr._putOnTaskQueue()
                        self.inProcess = True
                        self.lock.release()
                        self._execute(gr)
                    else:
                        tr = current_thread()                    
                        cgr = CustomGreenlet(self.wait)
                        cgr.currentRequest = self
                        cgr.thread = tr                        
                        self.lock.release()
                        cgr.switch(self)
                        self._waitFor(cgr,tr) #wait for finish
            else:
                self.lock.release()
        else:
            if self.destination is None:
                self.destination = self.slot._allocateStorage(self._writer._start, self._writer._stop, False)
            
            if isinstance(self.slot._value, (numpy.ndarray, vigra.VigraArray)):
                self.destination[:] = self.slot._value[self.key]
            else:
                self.destination[:] = self.slot._value
            self._finished = True
        return self.destination   
  
      
    def processReqObject(self,reqObject):
        reqObject.func(reqObject.arg1, reqObject.key, reqObject.destination)
        reqObject._finalize()
      
    def _waitFor(self, cgr, tr):
        while not cgr.dead:
            tr.workAvailableEvent.wait()
            tr.workAvailableEvent.clear()
            while len(tr.finishedRequestGreenlets) > 0:
                req, gr = tr.finishedRequestGreenlets.popleft()
                gr.currentRequest = req                 
                gr.switch()
                del gr
        del cgr
        self._finalize()

       
    def notify(self, closure, **kwargs): 
        """
        calling .notify(someFunction) on an RequestObject is a NON-blocking
        call that will return immediately.
        once the results are calculated and stored in the result
        are, the provided someFunction will be called by lazyflow.
        """
        self.lock.acquire()
        if self._finished is True:
            self.lock.release()
            assert self.destination is not None
            closure(self.destination, **kwargs)
        else:
            self.notifyQueue.append((closure, kwargs))
            
            if not self.inProcess:
                self._putOnTaskQueue()
            self.lock.release()
            
    def onCancel(self, closure, **kwargs):
        self.lock.acquire()       
        if self.canceled:
            self.lock.release()
            closure(**kwargs)
        else:
            self.cancelQueue.append((closure, kwargs))
            self.lock.release()

    def _finalize(self):
        self.lock.acquire()
        self._finished = True
        self.lock.release()
        if self.graph.suspended is False or self.parentRequest is not None:
            if self.canceled is False:
                while len(self.notifyQueue) > 0:
                    try:
                        func, kwargs = self.notifyQueue.pop()
                    except:
                        break
                    func(self.destination, **kwargs)
    
                while len(self.waitQueue) > 0:
                    try:
                        tr, req, gr = self.waitQueue.pop()
                    except:
                        break
                    req.lock.acquire()
                    if not req.canceled:
                        tr.finishedRequestGreenlets.append((req, gr))
                        tr.workAvailableEvent.set()
                    req.lock.release()
        else:
            self.graph.putFinalize(self)
        self.parentRequest = None
        self.childRequests = {}

        
    def _cancel(self):
        self.lock.acquire()
        if not self._finished:
            self.canceled = True
            self.lock.release()
            while len(self.cancelQueue) > 0:
                try:
                    closure, kwargs = self.cancelQueue.pop()
                except:
                    break
                closure(**kwargs)
        else:
            self.lock.release()
            pass
        self._finalize()
#            while len(self.waitQueue) > 0:
#                tr, req, gr = self.waitQueue.popleft()
#                if req.canceled is False:
#                    tr.finishedRequestGreenlets.append((req, gr))
#                    tr.workAvailableEvent.set()

    def _cancelChildren(self):
        if not self._finished:
            self._cancel()
            self.lock.acquire()
            childs = list(self.childRequests.values())
            self.lock.release()
            for r in childs:
                r._cancelChildren()            
            self.childRequests = {}

    def _cancelParents(self):
        if not self._finished:
            self._cancel()
            if self.parentRequest is not None:
                self.parentRequest._cancelParents()


    def cancel(self):
        if not self._finished:
            self.canceled = True
            self._cancelChildren()
            #self._cancelParents()
        
    def __call__(self):
        assert 1==2, "Please use the .wait() method, () is deprecated !"

class InputSlot(object):
    """
    The base class for input slots, it provides methods
    to connect the InputSlot to an OutputSlot of another
    operator (i.e. .connect(partner) call) or allows 
    to directly provide a value as input (i.e. .setValue(value) call)
    """
    
    __slots__ = ["name", "operator", "partner", "level", 
                 "_value", "_stype", "axistags", "shape", "dtype"]    
    
    def __init__(self, name, operator = None, stype = "ndarray"):
        self.name = name
        self.operator = operator
        self.partner = None
        self.level = 0
        self._value = None
        self._stype = stype
        self.axistags = None
        self.shape = None
        self.dtype = None

    def setValue(self, value):
        """
        This methods allows to directly provide an array
        or other entitiy as input the the InputSlot instead
        of connecting it to a partner OutputSlot.
        """
        assert self.partner == None, "InputSlot %s (%r): Cannot dot setValue, because it is connected !" %(self.name, self)
        self._value = value
        if isinstance(value, (numpy.ndarray, vigra.VigraArray)):
            self.shape = value.shape
            self.dtype = value.dtype
            if hasattr(value, "axistags"):
                self.axistags = value.axistags
            else:
                self.axistags = vigra.defaultAxistags(len(value.shape))
        else:
            self.shape = (1,)
            self.dtype = object
            self.axistags = vigra.defaultAxistags(1)
        self._checkNotifyConnect()

    @property
    def value(self):
        """
        a convenience method for retrieving the value
        from an (1,) shaped ndarray of dtype object, 
        used slots that contain single strings, floats, integers etc.
        """
        if self.partner is not None:
            temp = self[:].allocate().wait()[0]
            return temp
        else:
            assert self._value is not None, "InputSlot %s (%r): Cannot access .value since slot is not connected and setValue has not been called !" %(self.name, self)
            return self._value

    def connected(self):
        answer = True
        if self._value is None and self.partner is None or (self.partner is not None and self.partner.shape is None):
            answer = False
        return answer


    def connect(self, partner):
        """
        connects the InputSlot to a partner OutputSlot
        
        when all InputSlots of an Operator are connected (or
        are given a value by calling .setvalue(value))
        the Operator is notified via its notifyConnectAll() method.
        """
        assert partner is None or isinstance(partner, (OutputSlot, MultiOutputSlot)), \
               "InputSlot(name=%s, operator=%s).connect: partner has type %r" \
               % (self.name, self.operator, type(partner))
        
        if partner is None:
            self.disconnect()
            return        
        
        if self.partner == partner and partner.level == self.level:
            return
        self.disconnect()
        if partner.level > 0:
            partner.disconnectSlot(self)
            if lazyflow.verboseWrapping:
                print "Operator [self=%r] '%s', slot '%s':" % (self.operator, self.operator.name, self.name)
                print "  -> wrapping because operator.level=0 and partner.level=%d" % partner.level
            newop = OperatorWrapper(self.operator)
            newop.inputs[self.name].connect(partner)
            
        else:
            self.partner = partner
            self.dtype = partner.dtype
            self.axistags = partner.axistags
            self.shape = partner.shape
            partner._connect(self)
            # do a type check
            self.connectOk(self.partner)
            if self.shape is not None:
                self._checkNotifyConnect()
    
    def _checkNotifyConnect(self):
        if self.operator is not None:
            self.operator._notifyConnect(self)
            self._checkNotifyConnectAll()
            
    def _checkNotifyConnectAll(self):
        """
        notify operator of connection
        the operator may do a compatibility
        check that involves
        more then one slot
        """
        
        assert self.operator is not None
        
        # check wether all slots are connected and notify operator            
        if isinstance(self.operator,Operator):
            allConnected = True
            for slot in self.operator.inputs.values():
                if slot.connected() is False:
                    allConnected = False
                    break
            if allConnected:
                self.operator._notifyConnectAll()
                
    def disconnect(self):
        """
        Disconnect a InputSlot from its partner
        """
        #TODO: also reset ._value ??
        self.operator._notifyDisconnect(self)
        if self.partner is not None:
            self.partner.disconnectSlot(self)
        self.partner = None
        self.dtype = None
        self.axistags = None
        self.shape = None
    
    #TODO RENAME? createInstance
    # def __copy__ ?, clone ?
    def getInstance(self, operator):
        s = InputSlot(self.name, operator, stype = self._stype)
        return s
            
    def setDirty(self, key):
        """
        this method is called by a partnering OutputSlot
        when its content changes.
        
        the key parameter identifies the changed region
        of an numpy.ndarray
        """
        assert self.operator is not None, \
               "Slot '%s' cannot be set dirty, slot not belonging to any actual operator instance" % self.name
        self.operator.notifyDirty(self, key)
    
    def connectOk(self, partner):
        # reimplement this method
        # if you want a more involved
        # type checking
        return True

    def __getitem__(self, key):
        """
        retrieve the array content from the partner OutputSlot
        
        the method supports the array access interface.
        
        allows to call inputslot[0,:,3:11] 
        """
        gr = greenlet.getcurrent()
        assert hasattr(gr,"currentRequest")
        start, stop = sliceToRoi(key, self.shape)
        assert len(stop) == len(self.shape)
        assert stop <= list(self.shape)
        assert start >= [0]*len(self.shape)
        assert self.partner is not None or self._value is not None, "cannot do __getitem__ on Slot %s, of %r Not Connected!" % (self.name, self.operator)
        return GetItemWriterObject(self, key)

    def _allocateStorage(self, start, stop, axistags = True):
        storage = numpy.ndarray(stop - start, dtype=self.dtype)
        if axistags is True:
           storage = vigra.VigraArray(storage, storage.dtype, axistags = copy.copy(self.axistags))
#        key = roiToSlice(start,stop) #we need a fully specified key e.g. not [:] but [0:10,0:17] !!
        return storage
            
    def __setitem__(self, key, value):
        assert self.operator is not None, "cannot do __setitem__ on Slot '%s' -> no operator !!"     
        if self._value is not None:
            self._value[key] = value
            self.setDirty(key) # only propagate the dirty key at the very beginning of the chain
        self.operator.setInSlot(self,key,value)
        
    @property
    def graph(self):
        return self.operator.graph

    def dumpToH5G(self, h5g, patchBoard):
        h5g.dumpSubObjects({
            "name" : self.name,
            "level" : self.level,
            "operator" : self.operator,
            "partner" : self.partner,
            "value" : self._value,
            "stype" : self._stype,
            "dtype" : self.dtype,
            "axistags" : self.axistags,
            "shape" : self.shape
            
        },patchBoard)
    
    @classmethod
    def reconstructFromH5G(cls, h5g, patchBoard):
        
        s = cls("temp")

        patchBoard[h5g.attrs["id"]] = s
        
        h5g.reconstructSubObjects(s,{
            "name" : "name",
            "level" : "level",
            "operator" : "operator",
            "partner" : "partner",
            "value" : "_value",
            "stype" : "stype",
            "dtype" : "dtype",
            "axistags" : "axistags",
            "shape" : "shape"
            
        },patchBoard)

        return s
    
class OutputSlot(object):
    """
    The base class for output slots, it provides methods
    to connect the OutputSlot to an InputSlot of another
    operator (i.e. .connect(partner) call).
    
    the content of the OutputSlot e.g. the result of the operator
    it belongs to can be requested with the usual
    python array slicing syntax, i.e.
    
    outputslot[3,:,14:32]
    
    this call returns an GetItemWriterObject.
    """    
    
    __slots__ = ["name", "_metaParent", "level", "operator",
                 "dtype", "shape", "axistags", "partners", "_stype",
                 "_dirtyCallbacks"]    
    
    def __init__(self, name, operator = None, stype = "ndarray"):
        self.name = name
        self._metaParent = operator
        self.level = 0
        self.operator = operator
        if not hasattr(self, "dtype"):
            self.dtype = None
        if not hasattr(self, "shape"):
            self.shape = None
        if not hasattr(self, "axistags"):
            self.axistags = None
        self.partners = []
        self._stype = stype
        
        self._dirtyCallbacks = []
    
    @property
    def _shape(self):
        return self.shape
        
    @_shape.setter
    def _shape(self, value):
        if value is not None:
            if value != self.shape:
                self.shape = value
                for p in self.partners:
                    #p._checkNotifyConnectAll()
                    #p.disconnect()
                    #p.connect(self)
                    p.shape = value
                    p.operator._notifyConnect(p)
                    p._checkNotifyConnectAll()
            #else:
            #    self.setDirty(slice(None,None,None)) #set everything to dirty! BEWARE; DANGER;
        else:
            self.shape = None
            #for p in self.partners:
                #p.operator.notifyConnect(p)
                #p._checkNotifyConnectAll()
    
    @property
    def _axistags(self):
        return self.axistags
        
    @_axistags.setter
    def _axistags(self, value):
        if value is not None:
            if value != self.axistags:
                self.axistags = value
                for p in self.partners:
                    p.axistags = value
                    # check for connect propagation 
                    #p.operator.notifyConnect(p)
                    #p._checkNotifyConnectAll()                    
        else:
            self.axistags = None

    @property
    def _dtype(self):
        return self.dtype

    @_dtype.setter
    def _dtype(self, value):
        self.dtype = value
                
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
           
    def registerDirtyCallback(self, function, **kwargs):
        self._dirtyCallbacks.append([function, kwargs])
    
    def unregisterDirtyCallback(self, function):
        element = None
        for e in self._dirtyCallbacks:
            if e[0] == function:
                element = e
        if element is not None:
            self._dirtyCallbacks.remove(element)
            
    def setDirty(self, key):
        """
        This method can be called by an operator
        to indicate that a region (identified by key)
        has changed and needs recalculation.
        
        the method notifies all InputSlots that are connected to
        this output slot
        """
        start, stop = sliceToRoi(key, self.shape)
        key = roiToSlice(start,stop)
        for p in self.partners:
            p.setDirty(key) #set everything dirty
            
        for cb in self._dirtyCallbacks:
            cb[0](key, **cb[1])

    #FIXME __copy__ ?
    def getInstance(self, operator):
        s = OutputSlot(self.name, operator, stype = self._stype)
        s.shape = self.shape
        s.dtype = self.dtype
        s.axistags = self.axistags
        return s

    def _allocateStorage(self, start, stop, axistags = True):
        storage = numpy.ndarray(stop - start, dtype=self.dtype)
        if axistags is True:
            storage = vigra.VigraArray(storage, storage.dtype, axistags = copy.copy(self.axistags))
            #storage = storage.view(vigra.VigraArray)
            #storage.axistags = copy.copy(self.axistags)
        return storage

    def __getitem__(self, key):
        assert self.shape is not None, "OutputSlot.__getitem__: self.shape=None (operator [self=%r] '%s'" % (self.operator, self.name)

        #start, stop = sliceToRoi(key, self.shape)
        #assert numpy.min(start) >= 0, "Somebody is requesting shit from slot %s of operator %s (%r)" %(self.name, self.operator.name, self.operator)
        #assert (stop <= numpy.array(self.shape)).all(), "Somebody is requesting shit from slot %s of operator %s (%r) :  start: %r, stop %r, shape %r" %(self.name, self.operator.name, self.operator, start, stop, self.shape)
                
        return GetItemWriterObject(self,key)
    
    def getOutSlotFromOp(self, key, destination):
        self.operator.getOutSlot(self, key, destination)


    def __setitem__(self, key, value):
        for p in self.partners:
            p[key] = value

    @property
    def graph(self):
        return self.operator.graph
    
    def dumpToH5G(self, h5g, patchBoard):
        h5g.dumpSubObjects({
            "name" : self.name,
            "level" : self.level,
            "operator" : self.operator,
            "shape" : self.shape,
            "axistags" : self.axistags,
            "dtype" : self.dtype,
            "partners" : self.partners,
            "stype" : self._stype
            
        },patchBoard)
    
    @classmethod
    def reconstructFromH5G(cls, h5g, patchBoard):
        
        s = cls("temp")

        patchBoard[h5g.attrs["id"]] = s
        
        h5g.reconstructSubObjects(s,{
            "name" : "name",
            "level" : "level",
            "operator" : "operator",
            "shape" : "shape",
            "axistags" : "axistags",
            "dtype" : "dtype",
            "partners" : "partners",
            "stype" : "stype"
            
        },patchBoard)
            
        return s
        

class MultiInputSlot(object):
    """
    The MultiInputSlot is a multidimensional InputSlot.
    
    it contains nested lists of InputSlot objects.
    """
    
    __slots__ = ["name", "operator", "partner", "inputSlots", "level",
                 "_stype", "_value"]    
    
    def __init__(self, name, operator = None, stype = "ndarray", level = 1):
        self.name = name
        self.operator = operator
        self.partner = None
        self.inputSlots = []
        self.level = level
        self._stype = stype
        self._value = None
    
    @property
    def value(self):
        return self._value

    def setValue(self, value):
        self._value = value
        for i,s in enumerate(self.inputSlots):
            s.disconnect()
            s.setValue(self._value)
        self.operator._notifyConnect(self)
        self._checkNotifyConnectAll()
    
    def __getitem__(self, key):
        return self.inputSlots[key]
    
    def __len__(self):
        return len(self.inputSlots)
        
    def resize(self, size):
        oldsize = len(self)
        
        while size > len(self):
            self._appendNew()
            
        while size < len(self):
            self._removeInputSlot(self[-1])

        if oldsize < size:
            for index in range(oldsize-1,size):
                islot = self.inputSlots[index]
        
                    
    def _appendNew(self):
        if self.level <= 1:
            islot = InputSlot(self.name ,self, stype = self._stype)
        else:
            islot = MultiInputSlot(self.name,self, stype = self._stype, level = self.level - 1)
        index = len(self) - 1
        self.inputSlots.append(islot)
    
        if self.partner is not None:
            if self.partner.level > 0:
                if len(self.partner) >= len(self):
                    self.partner[index]._connect(islot)
            else:
                self.partner._connect(islot)
        if self._value is not None:
            islot.setValue(self._value)    

        return islot 

    def _insertNew(self, index):
        if self.level == 1:
            islot = InputSlot(self.name,self, self._stype)
        else:
            islot = MultiInputSlot(self.name,self, stype = self._stype, level = self.level - 1)
        self.inputSlots.insert(index,islot)
        for i, isl in enumerate(self.inputSlots[index+1:]):
            isl.name = self.name
        if self.partner is not None:
            if len(self.partner) > index:
                islot.connect(self.partner[index])
        elif self._value is not None:
            islot.setValue(self._value)                
        return islot
    
    
    def _checkNotifyConnectAll(self):
        
        # check wether all slots are connected and eventuall notify operator            
        if issubclass(self.operator.__class__, Operator):
            allConnected = True
            for slot in self.operator.inputs.values():
                if not slot.connected():
                    allConnected = False
                    break
            if allConnected:
                self.operator._notifyConnectAll()
        else: #the .operator is a MultiInputSlot itself
            self.operator._checkNotifyConnectAll()
        
    
    def cloneConnectionsFrom(self, otherInputSlot):
        self.resize(len(otherInputSlot))
        for i, slot in enumerate(otherInputSlot):
            if slot.level == 0:
                if slot.partner is not None:
                    self[i].connect(slot.partner)
                elif slot._value is not None:
                    self[i].setValue(slot._value)
                    
            else:
                self[i].cloneConnectionsFrom(slot)

    def connected(self):
        answer = True
        if self._value is None and self.partner is None:
            answer = False
        if answer is False and len(self.inputSlots) > 0:
            answer = True
            for s in self.inputSlots:
                if s.connected() is False:
                    answer = False
                    break
        
        return answer

    def _requiredLength(self):
        if self.partner is not None:
            if self.partner.level == self.level:
                return len(self.partner)
            elif self.partner.level < self.level:
                return 1
        elif self._value is not None:
            return 1
        else:
            return 0

        
    def connect(self,partner):
        if partner is None:
            self.disconnect()
            return
            
        if self.partner == partner and partner.level == self.level:
            return
        
        if partner is not None:
            if partner.level == self.level:
                if self.partner is not None:
                    self.partner.disconnectSlot(self)
                self.partner = partner
                partner._connect(self)
                # do a type check
                self.connectOk(self.partner)
                
                # create new self.inputSlots for each outputSlot 
                # of our partner 
                if len(self) != len(partner):
                    self.resize(len(partner))
                    
                for i,p in enumerate(self.partner):
                    self.partner[i]._connect(self[i])
                
                self.operator._notifyConnect(self)
                self._checkNotifyConnectAll()
                
            elif partner.level < self.level:
                #if self.partner is not None:
                #    self.partner.disconnectSlot(self)                
                self.partner = partner
                for i, slot in enumerate(self):                
                    slot.connect(partner)
                    if self.operator is not None:
                        self.operator._notifySubConnect((self,slot), (i,))
                self._checkNotifyConnectAll()
            elif partner.level > self.level:
                #if self.partner is not None:
                #    self.partner.disconnectSlot(self)
                partner.disconnectSlot(self)
                #print "MultiInputSlot", self.name, "of op", self.operator.name, self.operator
                print "-> Wrapping operator because own level is", self.level, "partner level is", partner.level
                if isinstance(self.operator,(OperatorWrapper, Operator, OperatorGroup)):
                    newop = OperatorWrapper(self.operator)
                    partner._connect(newop.inputs[self.name])
                    #assert newop.inputs[self.name].level == self.level + 1, "%r, %s, %s, %d, %d" % (self.operator, self.operator.name, self.name, newop.inputs[self.name].level, self.level) 
                else:
                    raise RuntimeError("Trying to connect a higher order slot to a subslot - NOT ALLOWED")
            else:
                pass

    def _notifyConnect(self, slot):
        index = self.inputSlots.index(slot)
        self.operator._notifySubConnect((self,slot), (index,))
                
    
    def _notifySubConnect(self, slots, indexes):      
        index = self.inputSlots.index(slots[0])
        self.operator._notifySubConnect( (self,) + slots, (index,) +indexes)

    def _notifyDisconnect(self, slot):
        index = self.inputSlots.index(slot)
        self.operator._notifySubDisconnect((self, slot), (index,))
    
    def _notifySubDisconnect(self, slots, indexes):
        index = self.inputSlots.index(slots[0])
        self.operator._notifySubDisconnect((self,) + slots, (index,) + indexes)
        
    def _notifySubSlotRemove(self, slots, indexes):
        if len(slots)>0:
            index = self.inputSlots.index(slots[0])
            indexes = (index,) + indexes
        self.operator._notifySubSlotRemove((self,) + slots, indexes)
            
        
    def disconnect(self):
        for slot in self.inputSlots:
            slot.disconnect()
        if self.partner is not None:
            self.operator._notifyDisconnect(self)
            self.partner.disconnectSlot(self)
            self.inputSlots = []
            self.partner = None
    
    def removeSlot(self, index, notify = True):
        slot = index
        if type(index) is int:
            slot = self[index]
        self._removeInputSlot(slot, notify)
    
    def _removeInputSlot(self, inputSlot, notify = True):
        try:
            index = self.inputSlots.index(inputSlot)
        except:
            err =  "MultiInputSlot._removeInputSlot:"
            err += "  name='%s', operator='%s', operator=%r" % (self.name, self.operator.name, self.operator)
            err += "  inputSlots = %r" % (self.inputSlots,)
            err += "  partner    = %r" % (self.partner,)
            raise RuntimeError(str)
            sys.exit(1)
        inputSlot.disconnect()
        # notify parent operator of slot removal
        # index is the number of the slots while it
        # was still there
        if notify:
            self._notifySubSlotRemove((),(index,))
        self.inputSlots.remove(inputSlot)
        for i, slot in enumerate(self[index:]):
            slot.name = self.name+"3%d" % (index + i)

        

    def _partialSetItem(self, slot, key, value):
        index = self.inputSlots.index(slot)
        self.operator.multiSlotSetItem(self,slot,index, key,value)   
    
    #TODO RENAME? createInstance
    # def __copy__ ?
    def getInstance(self, operator):
        s = MultiInputSlot(self.name, operator, stype = self._stype, level = self.level)
        return s
            
    def setDirty(self, key = None):
        assert self.operator is not None, "Slot %s cannot be set dirty, slot not belonging to any actual operator instance" % self.name
        self.operator.notifyDirty(self, key)

    def notifyDirty(self, slot, key):
        index = self.inputSlots.index(slot)
        self.operator.notifySubSlotDirty((self,slot),(index,),key)
        pass
    
    def notifySubSlotDirty(self, slots, indexes, key):
        index = self.inputSlots.index(slots[0])
        self.operator.notifySubSlotDirty((self,)+slots,(index,) + indexes,key)
        pass
   
    def connectOk(self, partner):
        # reimplement this method
        # if you want a more involved
        # type checking
        return True

    @property
    def graph(self):
        return self.operator.graph

    def dumpToH5G(self, h5g, patchBoard):
        h5g.dumpSubObjects({
            "name" : self.name,
            "level" : self.level,
            "operator" : self.operator,
            "partner" : self.partner,
            "stype" : self._stype,
            "inputSlots": self.inputSlots
            
        },patchBoard)
    
    @classmethod
    def reconstructFromH5G(cls, h5g, patchBoard):
        
        s = cls("temp")

        patchBoard[h5g.attrs["id"]] = s
        
        h5g.reconstructSubObjects(s,{
            "name" : "name",
            "level" : "level",
            "operator" : "operator",
            "partner" : "partner",
            "stype" : "stype",
            "inputSlots": "inputSlots"
            
        },patchBoard)
            
        return s


class MultiOutputSlot(object):
    """
    The MultiOutputSlot is a multidimensional OutputSlot.
    
    it contains nested lists of OutputSlot objects.
    """
    
    __slots__ = ["name", "operator", "_metaParent",
                 "partners", "outputSlots", "level", "_stype"]
    
    def __init__(self, name, operator = None, stype = "ndarray",level = 1):
        self.name = name
        self.operator = operator
        self._metaParent = operator
        self.partners = []   
        self.outputSlots = []
        self.level = level
        self._stype = stype
    
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
        oslot = self.outputSlots[index]
        for p in oslot.partners:
            if isinstance(p.operator, MultiInputSlot):
                p.operator._removeInputSlot(p)
        
        oslot.disconnect()
        oslot = self.outputSlots.pop(index)
        
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
                slot = OutputSlot(self.name,self, stype = self._stype)
            else:
                slot = MultiOutputSlot(self.name,self, stype = self._stype, level = self.level - 1)
            index = len(self)
            self.outputSlots.append(slot)

        
        while len(self) > size:
            self.pop()

        for p in self.partners:
            p.resize(size)
            assert len(p) == len(self)
                
            
    def getOutSlot(self, slot, key, result):
        index = self.outputSlots.index(slot)
        return self.operator.getSubOutSlot((self, slot,),(index,),key, result)

    def getSubOutSlot(self, slots, indexes, key, result):
        try:
            index = self.outputSlots.index(slots[0])
        except:
            raise RuntimeError("MultiOutputSlot.getSubOutSlot: name=%r, operator.name=%r, slots=%r" % \
                               (self.name, self.operator.name, self.operator, slots))
        return self.operator.getSubOutSlot((self,) + slots, (index,) + indexes, key, result)
    
    #TODO RENAME? createInstance
    # def __copy__ ?
    def getInstance(self, operator):
        s = MultiOutputSlot(self.name, operator, stype = self._stype, level = self.level)
        return s
            
    def setDirty(self, key):
        for partner in self.partners:
            partner.setDirty(key)
    
    def connectOk(self, partner):
        # reimplement this method
        # if you want a more involved
        # type checking
        return True

    def getOutSlotFromOp(self, slot, key, destination):
        index = self.outputSlots.index(slot)
        self.operator.getSubOutSlot(self, slot, index, key, destination)

    @property
    def graph(self):
        return self.operator.graph


    def dumpToH5G(self, h5g, patchBoard):
        h5g.dumpSubObjects({
            "name" : self.name,
            "level" : self.level,
            "operator" : self.operator,
            "partners" : self.partners,
            "stype" : self._stype,
            "outputSlots" : self.outputSlots
            
        },patchBoard)
    
    @classmethod
    def reconstructFromH5G(cls, h5g, patchBoard):
        
        s = cls("temp")

        patchBoard[h5g.attrs["id"]] = s
        
        h5g.reconstructSubObjects(s,{
            "name" : "name",
            "level" : "level",
            "operator" : "operator",
            "partners" : "partners",
            "stype" : "stype",
            "outputSlots" : "outputSlots"
            
        },patchBoard)
            
        return s


class OutputDict(dict):
    
    def __setitem__(self, key, value):
        assert isinstance(value, (OutputSlot, MultiOutputSlot)), "ERROR: all elements of .outputs must be of type OutputSlot or MultiOutputSlot, you provided %r !" % (value,)
        return dict.__setitem__(self, key, value)

class Operator(object):
    """
    The base class for all Operators.
    
    Operators consist of a class inheriting from this class
    and need to specify their inputs and outputs via
    thei inputSlot and outputSlot class properties.
    
    Each instance of an operator obtains individual
    copies of the inputSlots and outputSlots, which are
    available in the self.inputs and self.outputs instance
    properties.
    
    these instance properties can be used to connect
    the inputs and outputs of different operators.
    
    Example:
        operator1.inputs["InputA"].connect(operator2.outputs["OutputC"])
    
    
    Different examples for simple operators are provided
    in an example directory. plese read through the
    examples to learn how to implement your own operators...
    """
    
    #definition of inputs slots
    inputSlots  = [] 

    #definition of output slots -> operators instances 
    outputSlots = [] 
    name = ""
    description = ""
    category = "lazyflow"
    
    def __init__(self, graph, register = True):
        self.operator = None
        self.inputs = {}
        self.outputs = OutputDict()
        self.graph = graph
        self.register = register
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
        if self.register:
            self.graph.registerOperator(self)
         
    def _getOriginalOperator(self):
        return self
        
    def disconnect(self):
        for s in self.outputs.values():
            s.disconnect()
        for s in self.inputs.values():
            s.disconnect()

    def notifyDirty(self, inputSlot, key):
        # simple default implementation
        # -> set all outputs dirty    
        for os in self.outputs.values():
            os.setDirty(slice(None,None,None))
            
    def notifySubSlotDirty(self, slots, indexes, key):
        # simple default implementation
        # -> set all outputs dirty    
        for os in self.outputs.values():
            os.setDirty(slice(None,None,None))

    def _notifyConnect(self, inputSlot):
        self.notifyConnect(inputSlot)
    
    def _notifyConnectAll(self):
        self.notifyConnectAll()

    def _notifySubConnect(self, slots, indexes):
        self.notifySubConnect(slots,indexes)

    def _notifySubSlotRemove(self, slots, indexes):
        self.notifySubSlotRemove(slots, indexes)
        

    def notifyConnect(self, inputSlot):
        pass
    
    def notifyConnectAll(self):
        pass
    
    def notifySubConnect(self, slots, indexes):
        pass
   
    def notifySubSlotRemove(self, slots, indexes):
        pass
         
    def getOutSlot(self, slot, key, result):
        return None

    def getSubOutSlot(self, slots, indexes, key, result):
        return None
    
    def setInSlot(self, slot, key, value):
        pass

    def setSubInSlot(self,slots,indexes, key,value):
        pass

    def _notifyDisconnect(self, slot):
        self.notifyDisconnect(slot)
    
    def _notifySubDisconnect(self, slots, indexes):
        self.notifySubDisconnect(slots,indexes)


    def notifyDisconnect(self, slot):
        pass
    
    def notifySubDisconnect(self, slots, indexes):
        pass


    def dumpToH5G(self, h5g, patchBoard):
        h5inputs = h5g.create_group("inputs")
        h5inputs.dumpObject(self.inputs)

        h5outputs = h5g.create_group("outputs")
        h5outputs.dumpObject(self.outputs)
        
        h5graph = h5g.create_group("graph")
        h5graph.dumpObject(self.graph)
    
    @classmethod
    def reconstructFromH5G(cls, h5g, patchBoard):
        
        h5graph = h5g["graph"]        
        g = h5graph.reconstructObject(patchBoard)        
        op = stringToClass(h5g.attrs["className"])(g)

        patchBoard[h5g.attrs["id"]] = op        
        
        h5inputs = h5g["inputs"]
        op.inputs = h5inputs.reconstructObject(patchBoard)
        
        h5outputs = h5g["outputs"]
        op.outputs = h5outputs.reconstructObject(patchBoard)
        
        return op
        
class OperatorWrapper(Operator):
    name = ""
    
    @property
    def inputSlots(self):
        return self._inputSlots
    
    @property
    def outputSlots(self):
        return self._outputSlots
    
    def __init__(self, operator, register = False):
        self.inputs = {}
        self.outputs = OutputDict()
        self.operator = operator
        self.register = False
        if operator is not None:
            self.graph = operator.graph
            self.name = operator.name
            
            self.comprehensionSlots = 1
            self.innerOperators = []
            self.comprehensionCount = 0
            self.origInputs = self.operator.inputs.copy()
            self.origOutputs = self.operator.outputs.copy()
            if lazyflow.verboseWrapping:
                print "wrapping operator [self=%r] '%s'" % (operator, operator.name)
            
            self._inputSlots = []
            self._outputSlots = []
            
            # replicate input slot definitions
            for islot in self.operator.inputSlots:
                level = islot.level + 1
                self._inputSlots.append(MultiInputSlot(islot.name, stype = islot._stype, level = level))
    
            # replicate output slot definitions
            for oslot in self.outputSlots:
                level = oslot.level + 1
                self._outputSlots.append(MultiOutputSlot(oslot.name, stype = oslot._stype, level = level))
    
                    
            # replicate input slots for the instance
            for islot in self.operator.inputs.values():
                level = islot.level + 1
                ii = MultiInputSlot(islot.name, self, stype = islot._stype, level = level)
                self.inputs[islot.name] = ii
                op = self.operator
                while isinstance(op.operator, (Operator, MultiInputSlot, OperatorGroup)):
                    op = op.operator
                op.inputs[islot.name] = ii
            
            # replicate output slots for the instance
            for oslot in self.operator.outputs.values():
                level = oslot.level + 1
                oo = MultiOutputSlot(oslot.name, self, stype = oslot._stype, level = level)
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
                if islot._value is not None:
                    ii.setValue(islot._value)
                    
            self._connectInnerOutputs()
    
    
            #connect output slots
            for oslot in self.origOutputs.values():
                oo = self.outputs[oslot.name]            
                partners = copy.copy(oslot.partners)
                oslot.disconnect()
                for p in partners:         
                    oo._connect(p)
            
            
    def _getOriginalOperator(self):
        op = self.operator
        while isinstance(op, OperatorWrapper):
            op = self.operator
        return op
                    
    def _testRestoreOriginalOperator(self):
        #TODO: only restore to the level that is needed, not to the most upper one !
        needWrapping = False
        for iname, islot in self.inputs.items():
            if islot.partner is not None:
                if islot.partner.level > self.origInputs[iname].level:
                    needWrapping = True
                
        if needWrapping is False:
            if lazyflow.verboseWrapping:
                print "Restoring original operator [self=%r] named '%s'" % (self, self.name)
            op = self
            while isinstance(op.operator, (OperatorWrapper)):
                op = op.operator
            op.operator.outputs = op.origOutputs
            op.operator.inputs = op.origInputs
            op = op.operator
             
            for k, islot in self.inputs.items():
                if islot.partner is not None:
                    op.inputs[k].connect(islot.partner)
    
            for k, oslot in self.outputs.items():
                for p in oslot.partners:
                    op.outputs[k]._connect(p)
                    
    def notifyDirty(self, slot, key):
        pass

    def notifySubSlotDirty(self, slots, indexes, key):
        pass

    
    def disconnect(self):
        for s in self.outputs.values():
            s.disconnect()
        for s in self.inputs.values():
            s.disconnect()
        self._testRestoreOriginalOperator()

    
    def _createInnerOperator(self):
        if self.operator.__class__ is not OperatorWrapper:
            opcopy = self.operator.__class__(self.graph, register = False)
        else:
            if lazyflow.verboseWrapping:
                print "_createInnerOperator OperatorWrapper"
            opcopy = OperatorWrapper(self.operator._createInnerOperator())
        return opcopy
    
    def _removeInnerOperator(self, op):
        index = self.innerOperators.index(op)
        self.innerOperators.remove(op)
        for name, oslot in self.outputs.items():
            oslot.pop(index)
        op.disconnect()

    def _connectInnerOutputsForIndex(self, index):
        for k,mslot in self.outputs.items():
            #assert isinstance(mslot,MultiOutputSlot)
            mslot.resize(len(self.innerOperators))

        innerOp = self.innerOperators[index]
        for key,mslot in self.outputs.items():            
            mslot[index] = innerOp.outputs[key]

            
    def _connectInnerOutputs(self):
        for k,mslot in self.outputs.items():
            #assert isinstance(mslot,MultiOutputSlot)
            mslot.resize(len(self.innerOperators))

        for key,mslot in self.outputs.items():
            for index, innerOp in enumerate(self.innerOperators):
                mslot[index] = innerOp.outputs[key]

#    def _recuresSetOutputs(self, outer, inner):
#        if not isinstance(inner, MultiOutputSlot):
#            assert not isinstance(outer, MultiOutputSlot)
#            outer._dtype = inner._dtype
#            outer._shape = inner._shape
#            outer._axistags = inner._axistags
#        else:
#            outer.resize(len(inner))
#            for i, innerSlot in enumerate(inner):
#                self._recuresSetOutputs(outer[i], inner[i])
                


    def _ensureInputSize(self, numMax = 0):
        
        newInnerOps = []
        maxLen = numMax
        for name, islot in self.inputs.items():
            assert isinstance(islot, MultiInputSlot)
            maxLen = max(islot._requiredLength(), maxLen)
                
        while maxLen > len(self.innerOperators):
            newop = self._createInnerOperator()
            self.innerOperators.append(newop)
            newInnerOps.append(newop)

        while maxLen < len(self.innerOperators):
            op = self.innerOperators[-1]
            self._removeInnerOperator(op)

        for k,mslot in self.inputs.items():
            mslot.resize(maxLen)
            assert len(mslot) == maxLen
#            for i, slot in enumerate(mslot):
#                if slot.partner is not None:
#                    slot.partner._connect(self.innerOperators[i].inputs[mslot.name])
        return maxLen

    def _notifyConnect(self, inputSlot):
        
        maxLen = self._ensureInputSize(len(inputSlot))
        for i,islot in enumerate(inputSlot):
            if islot.partner is not None:
                self.innerOperators[i].inputs[inputSlot.name].connect(islot.partner)
                if lazyflow.verboseWrapping:
                    print "Wrapped Op", self.name, "connected", i
            elif islot._value is not None:
                self.innerOperators[i].inputs[inputSlot.name].setValue(islot._value)

                        
        self._connectInnerOutputs()
        
        for k,mslot in self.outputs.items():
            assert len(mslot) == len(self.innerOperators) == maxLen, "%d, %d" % (len(mslot), len(self.innerOperators))        

    
    def _notifyConnectAll(self):
        maxLen = self._ensureInputSize()
        for o in self.outputs.values():
            o.resize(maxLen)
            
        while len(self.innerOperators) > maxLen:
            self.innerOperators.pop()
            
    def _notifySubConnect(self, slots, indexes):
        numMax = self._ensureInputSize(len(slots[0]))
        
        if slots[1].partner is not None:
            #
            # we have to connect the sub operator only
            # if it is a true inner operator, but not
            # if it is an OperatorWrapper. 
            #
            # why, is unclear.
            #
            #if not isinstance(self.innerOperators[indexes[0]], OperatorWrapper):
            self.innerOperators[indexes[0]].inputs[slots[0].name].connect(slots[1].partner)
        elif slots[1]._value is not None:
            #if not isinstance(self.innerOperators[indexes[0]], OperatorWrapper):
            self.innerOperators[indexes[0]].inputs[slots[0].name].disconnect()
            self.innerOperators[indexes[0]].inputs[slots[0].name].setValue(slots[1]._value)
            
        else:            
            if isinstance(self.innerOperators[indexes[0]], OperatorWrapper):
                
                if len(indexes)>1:
                    self.innerOperators[indexes[0]]._notifySubConnect(slots[1:],indexes[1:])
                else:
                    self.innerOperators[indexes[0]]._notifyConnect(slots[1],indexes[0])

#                # check wether all slots are connected and notify operator            
#                op = self.innerOperators[indexes[0]]
#                allConnected = True
#                for slot in op.inputs.values():
#                    if slot.partner is None and slot._value is None:
#                        allConnected = False
#                        break
#                if allConnected:
#                    op.notifyConnectAll()
                    
            else:
                if len(indexes)>1:
                    self.innerOperators[indexes[0]].inputs[slots[0].name].resize(len(slots[1]))
                    for i, islot in enumerate(slots[1]):
                        if islot.partner is not None:
                            self.innerOperators[indexes[0]].inputs[slots[0].name][i].connect(islot.partner)
                        elif islot._value is not None:
                            self.innerOperators[indexes[0]].inputs[slots[0].name][i].setValue(islot._value)
                else:
                    if slots[1].partner is not None:
                        self.innerOperators[indexes[0]].inputs[slots[0].name].connect(slots[1].partner)
                    elif slots[1]._value is not None:
                        self.innerOperators[indexes[0]].inputs[slots[0].name].setValue(slots[1]._value)                        
        self._connectInnerOutputsForIndex(indexes[0])
        return


    def _notifyDisconnect(self, slot):
        self._testRestoreOriginalOperator()
        
    def _notifySubDisconnect(self, slots, indexes):
        return
        maxLen = 0
        for name, islot in self.inputs.items():
            maxLen = max(len(islot), maxLen)
        
        while len(self.innerOperators) > maxLen:
            op = self.innerOperators[-1]
            self._removeInnerOperator(op)

    def notifySubSlotRemove(self, slots, indexes):
        if len(indexes) == 1:
            if len(self.innerOperators) > indexes[0]:
                op = self.innerOperators[indexes[0]]
                self._removeInnerOperator(op)
        else:
            if slots[0].partner is not None: #normal connect case
                self.innerOperators[indexes[0]]._notifySubSlotRemove(slots[1:], indexes[1:])
            else: #connectAdd case
                op = self.innerOperators[indexes[0]]
                self._removeInnerOperator(op)
        self._connectInnerOutputs()
                
    def getOutSlot(self, slot, key, result):
        #this should never be called !!!        
        assert 1==2


    def getSubOutSlot(self, slots, indexes, key, result):
        if len(indexes) == 1:
            return self.innerOperators[indexes[0]].getOutSlot(self.innerOperators[indexes[0]].outputs[slots[0].name], key, result)
        else:
            self.innerOperators[indexes[0]].getSubOutSlot(slots[1:], indexes[1:], key, result)
        
    def setInSlot(self, slot, key, value):
        #TODO: code this
        assert 1==2

    def setSubInSlot(self,multislot,slot,index, key,value):
        #TODO: code this
        assert 1==2


    def dumpToH5G(self, h5g, patchBoard):
        h5g.dumpSubObjects({
                    "graph" : self.graph,
                    "operator": self.operator,
                    "origInputs": self.origInputs,
                    "origOutputs": self.origOutputs,
                    "_inputSlots": self._inputSlots,
                    "_outputSlots": self._outputSlots,
                    "inputs": self.inputs,
                    "outputs": self.outputs,
                    "innerOperators": self.innerOperators                    
                },patchBoard)    
                
    @classmethod
    def reconstructFromH5G(cls, h5g, patchBoard):
        
        op = stringToClass(h5g.attrs["className"])(None)
        
        patchBoard[h5g.attrs["id"]] = op
        
        h5g.reconstructSubObjects(op, {
                    "graph" : "graph",
                    "operator" : "operator",
                    "origInputs": "origInputs",
                    "origOutputs": "origOutputs",
                    "_inputSlots": "_inputSlots",
                    "_outputSlots": "_outputSlots",
                    "inputs": "inputs",
                    "outputs": "outputs",
                    "innerOperators": "innerOperators"                    
                },patchBoard)    

        return op
        
        
        
        
        
class OperatorGroupGraph(object):
    def __init__(self, originalGraph):
        self._originalGraph = originalGraph
        self.operators = []
    
    def _registerCache(self, op):    
        self._originalGraph._registerCache(op)
    
    def _notifyMemoryAllocation(self, cache, size):
        self._originalGraph._notifyMemoryAllocation(cache, size)
    
    def _notifyFreeMemory(self, size):
        self._originalGraph._notifyFreeMemory(size)
    
    def _freeMemory(self, size):
        self._originalGraph._freeMemory(size)
    
    def _notifyMemoryHit(self):
        self._originalGraph._notifyMemoryHit()
    
    def putTask(self, reqObject):
        self._originalGraph.putTask(reqObject)

    def putFinalize(self, reqObject):
        self._originalGraph.putFinalize(reqObject)

    def finalize(self):
        self._originalGraph.finalize()
    
    def registerOperator(self, op):
        self.operators.append(op)
    
    def removeOperator(self, op):
        assert op in self.operators, "Operator %r not a registered Operator" % op
        self.operators.remove(op)
        op.disconnect()
 
    @property
    def suspended(self):
        return self._originalGraph.suspended
 
    def dumpToH5G(self, h5g, patchBoard):
        h5op = h5g.create_group("operators")
        h5op.dumpObject(self.operators, patchBoard)
        h5graph = h5g.create_group("originalGraph")
        h5graph.dumpObject(self._originalGraph, patchBoard)

    
    @classmethod
    def reconstructFromH5G(cls, h5g, patchBoard):
        h5graph = h5g["originalGraph"]        
        ograph = h5graph.reconstructObject(patchBoard)               
        g = OperatorGroupGraph(ograph)
        patchBoard[h5g.attrs["id"]] = g 
        h5ops = h5g["operators"]        
        g.operators = h5ops.reconstructObject(patchBoard)
 
        return g        
        
        
        
        
        
        
class OperatorGroup(Operator):
    def __init__(self, graph, register = True):

        # we use a fake graph, so that the sub operators
        # of the group operator are not visible in the 
        # operator list of the original graph
        self._originalGraph = graph
        fakeGraph = OperatorGroupGraph(graph)
        
        Operator.__init__(self,fakeGraph, register = register)

        self._visibleOutputs = None
        self._visibleInputs = None

        self._createInnerOperators()
        self._connectInnerOutputs()

        if self.register:
            self._originalGraph.registerOperator(self)
        
    def _createInnerOperators(self):
        # this method must setup the
        # inner operators and connect them (internally)
        pass
        
    def setupInputSlots(self):
        # this method must setupt the 
        # set self._visibleInputs
        pass
        
    
    def setupOutputSlots(self):
        # this method must setup 
        # self._visibleOutputs
        pass
    
    def _connectInnerOutputs(self):
        outputs = self.getInnerOutputs()
        
        for key, value in outputs.items():
            self.outputs[key] = value

    def _getInnerInputs(self):
        opInputs = self.getInnerInputs()
        inputs = dict(self.inputs)
        inputs.update(opInputs)
        return inputs
        
                   
    def getSubOutSlot(self, slots, indexes, key, result):               
        slot = self._visibleOutputs[slots[0].name]
        for ind in indexes:
            slot = slot[ind]
        slot[key].writeInto(result)

    def getOutSlot(self, slot, key, result):
        self._visibleOutputs[slot.name][key].writeInto(result)
   
    def _notifyConnect(self, inputSlot):
        inputs = self._getInnerInputs()
        if inputSlot != inputs[inputSlot.name]:
            if inputSlot.partner is not None and inputs[inputSlot.name].partner != inputSlot.partner:
                inputs[inputSlot.name].connect(inputSlot.partner)
            elif inputSlot._value is not None and id(inputs[inputSlot.name]._value) != id(inputSlot._value):
                inputs[inputSlot.name].setValue(inputSlot._value)
        self.notifyConnect(inputSlot)

   
                        
class Worker(Thread):
    def __init__(self, graph):
        Thread.__init__(self)
        self.graph = graph
        self.working = False
        self._hasSlept = False
        self.daemon = True # kill automatically on application exit!
        self.finishedRequestGreenlets = deque()
        self.currentRequest = None
        self.requests = deque()
        self.process = psutil.Process(os.getpid())
        self.number =  len(self.graph.workers)
        self.workAvailableEvent = Event()
        self.workAvailableEvent.clear()
    
    def signalWorkAvailable(self): 
        self.workAvailableEvent.set()
        
        
    def run(self):
        ct = current_thread()
        while self.graph.running:
            self.graph.freeWorkers.append(self)
            self.workAvailableEvent.wait()#(0.2)
            self.graph.freeWorkers.remove(self)
            self.workAvailableEvent.clear()
                
            while not self.graph.tasks.empty() or len(self.finishedRequestGreenlets) > 0:       
                while len(self.finishedRequestGreenlets) > 0:
                    req, gr = self.finishedRequestGreenlets.popleft()
                    gr.currentRequest = req                 
                    gr.switch()
                    del gr
                task = None
                try:
                    prio,task = self.graph.tasks.get(block = False)#timeout = 1.0)
                except Empty:
                    pass
                if task is not None:
                    reqObject = task
                    if reqObject.canceled is False:
                        #TODO: isnt a comparison against currentRequestLevel better 
                        # then against 1 ? ...
                        if self._hasSlept or reqObject.parentRequest is not None or self.process.get_memory_info().vms < self.graph.softMaxMem:
                            gr = CustomGreenlet(reqObject._execute)
                            gr.thread = self
                            gr.switch( gr)
                            del gr
                            self._hasSlept = False
                        else:
                            self.graph.tasks.put((prio,task)) #move task back to task queue
                            print "Worker %d: The process uses too much memory sleeping for a while even though work is available..." % self.number
                            #freesize = abs(self.process.get_memory_info().vms  - self.graph.softMaxMem)
                            #self.graph._freeMemory(freesize * 3)                            
                            gc.collect()
                            self._hasSlept = True
                            time.sleep(4.0)
    
class Graph(object):
    def __init__(self, numThreads = None, softMaxMem =  None):
        self.operators = []
        self.tasks = PriorityQueue() #Lifo <-> depth first, fifo <-> breath first
        self.workers = []
        self.freeWorkers = deque()
        self.running = True
        self.suspended = False
        self.stopped = False
        
        self._suspendedRequests = deque()
        self._suspendedNotifyFinish = deque()
        
        if numThreads is None:
            self.numThreads = detectCPUs()
        else:
            self.numThreads = numThreads
        self.lastRequestID = itertools.count()
        self.process = psutil.Process(os.getpid())
        
        self._memoryAccessCounter = itertools.count()
        if softMaxMem is None:
            softMaxMem = psutil.avail_phymem()
            try:
                softMaxMem += psutil.cached_phymem()
            except:
                pass
        self.softMaxMem = softMaxMem # in bytes
        self.softCacheMem = softMaxMem * 0.3
        self._registeredCaches = deque()
        self._allocatedCaches = deque()
        self._usedCacheMemory = 0
        self._memAllocLock = threading.Lock()

        self._startWorkers()
        
    def _startWorkers(self):
        self.workers = []
        self.freeWorkers = deque()
        self.tasks = PriorityQueue()
        for i in xrange(self.numThreads):
            w = Worker(self)
            self.workers.append(w)
            w.start()
            self.freeWorkers.append(w)        
    
    def _memoryUsage(self):
        return self.process.get_memory_info().vms
    
    def _registerCache(self, op):
        self._memAllocLock.acquire()
        if op not in self._registeredCaches:
            self._registeredCaches.append(op)
        self._memAllocLock.release()
    
    def _notifyMemoryAllocation(self, cache, size):
        if self._usedCacheMemory + size > self.softCacheMem:
            print "Graph._notifyMemoryAllocation: _usedCacheMemory + size = %f MB > softCacheMem = %f MB" \
                  % ((self._usedCacheMemory + size)/1024.0**2, self.softCacheMem/1024.0**2)
            self._freeMemory(size*3) #leave a little room
        self._memAllocLock.acquire()
        self._usedCacheMemory += size
        
        if lazyflow.verboseMemory:
            print "Graph._notifyMemoryAllocation: _usedCacheMemory      = %f MB" % ((self._usedCacheMemory)/1024.0**2,)
            print "                               get_memory_info().vms = %f MB" % (self.process.get_memory_info().vms/1024.0**2,)

        self._memAllocLock.release()
        if cache not in self._allocatedCaches:
            self._allocatedCaches.append(cache)
    
    
    def _notifyFreeMemory(self, size):
        self._memAllocLock.acquire()
        self._usedCacheMemory -= size
        if lazyflow.verboseMemory:
            print "Graph._notifyFreeMemory: freeing %f MB, now _usedCacheMemory = %f MB" % (size/1024.0**2, (self._usedCacheMemory)/1024.0**2,)
        self._memAllocLock.release()
    
    def _freeMemory(self, size):

        freesize = size*3
        freesize = min(self.softCacheMem*0.5, freesize)
        freesize = max(freesize, self.softCacheMem * 0.2)
        if lazyflow.verboseMemory:
            print "Graph._freeMemory: freesize = %f MB" % ((freesize)/1024.0**2,)

        freedMem = 0
        
        while len(self._allocatedCaches) > 0:
            if freedMem < freesize: #c._memorySize() > 1024
                try:
                    c = self._allocatedCaches.popleft()
                except:
                    c = None
                if c is not None:
                    if c._memorySize() > 1024:
                    #FIXME: handle very small chunks
                        freedMem += c._freeMemory()
                    else:
                        self._allocatedCaches.appendleft(c)
            else:
                break
        self._memAllocLock.acquire()
        self._usedCacheMemory = self._usedCacheMemory - freedMem
        self._memAllocLock.release()
        gc.collect()
        usedMem2 = self.process.get_memory_info().vms
        print "Graph._freeMemory: freed memory %f MB of get_memory_info().vms = %f MB" % (freedMem/1024.0**2, usedMem2/1024.0**2,)

    def _notifyMemoryHit(self):
        accesses = self._memoryAccessCounter.next()
        if accesses > 20:
            self._memoryAccessCounter = itertools.count() #reset counter
            # calculate the exponential moving average for the caches            
            #prevent manipulation of deque during calculation
            self._memAllocLock.acquire()
            for c in self._registeredCaches:
                ch = c._cacheHits
                ch = ch * 0.2
                c._cacheHits = ch

            self._allocatedCaches = deque(sorted(self._allocatedCaches, key=lambda x: x._cacheHits))
            self._memAllocLock.release()

            
    def putTask(self, reqObject):
        if self.suspended is False or reqObject.parentRequest is not None:
            task = reqObject
            self.tasks.put((-task._requestLevel,task))
            
            if len(self.freeWorkers) > 0:
                w = self.freeWorkers.pop()
                self.freeWorkers.appendleft(w)
                w.signalWorkAvailable()
        else:
            self._suspendedRequests.append(reqObject)

    def putFinalize(self, reqObject):
        self._suspendedNotifyFinish.append(reqObject)

    def stopGraph(self):
        print "Graph: stopping..."        
        self.stopped = True
        self.suspendGraph()

    def suspendGraph(self):
        print "Graph: suspending..."        
        tasks = []
        while not self.tasks.empty():
            try:
                t = self.tasks.get(block = False)
                tasks.append(t)
            except:
                break
        runningRequests = []
        for t in tasks:
            prio, req = t
            if req.parentRequest is not None:
                self.putTask(req)
                runningRequests.append(req)
            else:
                self._suspendedRequests.append(req)

        waitFor = sorted(runningRequests, key=lambda x: -x._requestLevel)
        if len(waitFor) == 0:
            print "   no requests that need to be waited for"
        
        for i,req in enumerate(waitFor):
            s = "    Waiting for request %6d/%6d" % (i+1,len(waitFor))
            sys.stdout.write(s)
            sys.stdout.flush()
            req.wait()
            sys.stdout.write("\b"*len(s))
        self.suspended = True

        sys.stdout.write("\n")
        sys.stdout.flush()
        print "finished."
        #self.finalize()
            
    def resumeGraph(self):
        if self.stopped:
            self.stopped = False
            self._suspendedRequests = deque()
            self._suspendedNotifyFinish = deque()
            
        print "Graph: resuming %d requests" % len(self._suspendedRequests)
        self.suspended = False
        
        while len(self._suspendedNotifyFinish) > 0:
            try:
                r = self._suspendedNotifyFinish.pop()
            except:
                break
            r._finalize()
            
        while len(self._suspendedRequests) > 0:
            try:
                r = self._suspendedRequests.pop()
            except:
                break
            self.putTask(r)
        print "finished."

        
    def finalize(self):
        self.running = False
        for w in self.workers:
            w.signalWorkAvailable()
            w.join()
    
    def registerOperator(self, op):
        self.operators.append(op)
    
    def removeOperator(self, op):
        assert op in self.operators, "Operator %r not a registered Operator" % op
        self.operators.remove(op)
        op.disconnect()
 
    def dumpToH5G(self, h5g, patchBoard):
        h5op = h5g.create_group("operators")
        h5op.dumpObject(self.operators, patchBoard)

        h5g.dumpSubObjects({
                    "operators" : self.operators,
                    "numThreads": self.numThreads,
                    "softMaxMem": self.softMaxMem,
                    "registeredCaches": self.registeredCaches
                },patchBoard)    

    
    @classmethod
    def reconstructFromH5G(cls, h5g, patchBoard):
        g = Graph(numThreads = h5g.attrs["numThreads"], softMaxMem = h5g.attrs["softMaxMem"])
        patchBoard[h5g.attrs["id"]] = g 

        patchBoard[h5g.attrs["id"]] = op
        h5g.reconstructSubObjects(op, {
                    "operators": "operators",
                    "numThreads": "numThreads",
                    "softMaxMem" : "softMaxMem",
                    "registeredCaches": "registeredCaches"
                },patchBoard)    
 
        return g
 
    def dumpToH5G_OLD(self,h5g):
        endPoints = []
        
        # loop over all operators and
        # and find the endpoints
        for o in self.operators:
            olength = 0
            ilength = 0
            for os in o.outputs.values():
                olength += len(os.partners)
            for k, ins in o.inputs.items():
                if ins.partner is not None or ins.value is not None:
                    ilength += 1
            # if an operator has no outputs but inputs
            # it belongs to the graph and is an endpoint
            if olength == 0 and ilength > 0:
                ooooo = o._getOriginalOperator()
                if ooooo not in endPoints:
                    endPoints.append(ooooo)                
                
        queue = endPoints
        
        doneQueue = []
        
        # loop over all operators in the queue
        # (i.e. the endpoints in the beginning)
        # and append all inputs operators on which
        # they depend onto the queue
        # -> we construct the dependency graph in
        #    a breadth first manner
        while len(queue) > 0:
            op = queue.pop(0)
            doneQueue.append(op)
            for i in op.inputs.values():
                if i.partner is not None:
                    p = i.partner
                    # we use the metaParent to allow for operatorGroups and operatorWrappers
                    assert p._metaParent is not None, "%r, %r" % (p.name, p.operator)
                    partnerOp = p._metaParent._getOriginalOperator()
                    if partnerOp not in queue and partnerOp not in doneQueue:
                        queue.append(partnerOp)
        
        # we reverse the dependencies
        # since the graph has to be reconstructed beginning from the inputs
        doneQueue.reverse()

        # create subgroups for the operators, inslot values and connections themself                        
        h5ops = h5g.create_group("operators")
        h5values = h5g.create_group("inslot_values")
        h5gconnections = h5g.create_group("connections")
        
        #save the operator class names and ids
        for i,op in enumerate(doneQueue):
            opG = h5ops.create_group(str(id(op)))
            opG.attrs["id"] = str(id(op))
            opG.attrs["class"] = instanceClassToString(op)
                    
        connections = []

        # save the connections between the operators
        # and potential .value, so that everything can be restored 
        for i,op in enumerate(doneQueue):
            for key,inslot in op.inputs.items():
                #save a connection
                val = inslot.value
                if inslot.partner is not None:
                    partnerOp = inslot.partner.operator._getOriginalOperator()
                    partnerSlotName = inslot.partner.name
                    connections.append(["connect", [str(id(op)),key,str(id(partnerOp)), partnerSlotName]])                    
                elif val is not None:
                    #save the value in to the dedicated value group
                    connections.append(["setValue", [str(id(op)), key, str(id(val))]])
                    valG = h5values.create_group(str(id(val)))
                    valG.dumpObject(val)
        
        # save the connectino nested lists recursively
        h5gconnections.dumpObject(connections)
        
        
    @classmethod
    def reconstructFromH5G_OLD(cls, h5g, patchBoard):
        graph = Graph()
        
        reconstructedOperators = {}        
        reconstructedValues = {}
        
        h5ops = h5g["operators"]
        h5values = h5g["inslot_values"]
        connections = h5g["connections"].reconstructObject()
        
        def getReconstructedOperator(opId):
            """
            helper method to map an operatorId string to an reconstructed object
            """
            op = reconstructedOperators.get(opId,None)
            if op is None:
                # if the operator is accessed for the first tim
                # construct the object once
                opClassName = h5ops[opId].attrs["class"]
                opClass = stringToClass(opClassName)
                reconstructedOperators[opId] = op = opClass(graph)
            return op

        def getReconstructedValue(valueId):
            """
            helper method to map an valueId string to an reconstructed object
            """
            value = reconstructedValues.get(valueId,None)
            if value is None:
                # if the valueId is accessed for the first tim
                # construct the object once
                reconstructedValues[valueId] = value = h5values[valueId].reconstructObject()
            return value

                
        for c in connections:
            operation, arguments = c
            if operation == "connect":
                opInId, inSlotName, opOutId,outSlotName = arguments
                opInObject = getReconstructedOperator(opInId)
                opOutObject = getReconstructedOperator(opOutId)
                opInObject.inputs[inSlotName].connect(opOutObject.outputs[outSlotName])
                
            elif operation == "setValue":
                opId, inSlotName, valueId = arguments
                op = getReconstructedOperator(opId)
                value = getReconstructedValue(valueId)
                op.inputs[inSlotName].setValue(value)
                
        return graph
                
     