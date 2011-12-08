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
import atexit
import traceback


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

greenlet.GREENLET_USE_GC = False #use garbage collection
sys.setrecursionlimit(100000)

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

setattr(current_thread(), "finishedRequestGreenlets", PriorityQueue())
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
                assert gr.currentRequest is not None
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
        temp = gr.currentRequest
        if self.destination is None:
            self.destination = self.slot._allocateStorage(self._writer._start, self._writer._stop, False)
        gr.currentRequest = self
        try:
          self.func(self.arg1,self.key, self.destination)
        except Exception,e:
          print
          print "ERROR: Exception in Operator %s (%r)" % (self.slot.operator.name, self.slot.operator)
          traceback.print_exc(e)
          sys.exit(1)
        self._finalize()        
        gr.currentRequest = temp

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
        childs = tuple(self.childRequests.values())
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
            gr = greenlet.getcurrent()
            if self.canceled:
                self.canceled = False
                self._finished = False
                self.childRequests = {}
                self.parentRequest = gr.currentRequest
            if not self._finished:
                if self.inProcess:   
                    if hasattr(gr, "currentRequest"):                         
                        if not self._finished:
                            self.waitQueue.append((gr.thread, gr.currentRequest, gr))
                            self.lock.release()

                            # reprioritize this request if running requests
                            # requestlevel is higher then that of the request
                            # on which we are waiting -> prevent starving of
                            # high prio requests through resources blocked
                            # by low prio requests.
                            if gr.currentRequest._requestLevel > self._requestLevel:
                                delta = gr.currentRequest._requestLevel - self._requestLevel
                                self.adjustPriority(delta)
                            
                            self._burstLastRequest(gr)
                            if gr.lastRequest == self:
                                gr.lastRequest = None                                  
                            gr.thread.greenlet.switch(None)
                        else:
                            self.lock.release()
                            return self.destination
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
                        self._burstLastRequest(gr)
                        if gr.lastRequest == self:
                            gr.lastRequest = None
                        self.inProcess = True
                        temp = gr.currentRequest
                        self.lock.release()
                        self._execute(gr)
                        gr.currentRequest = temp
                    else:
                        tr = current_thread()                    
                        cgr = CustomGreenlet(self.wait)
                        cgr.currentRequest = self
                        cgr.thread = tr                        
                        self.lock.release()
                        setattr(tr,"greenlet", greenlet.getcurrent())
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
            while not tr.finishedRequestGreenlets.empty():
                prio,req, gr = tr.finishedRequestGreenlets.get(block = False)
                gr.currentRequest = req                 
                gr.switch()
                del gr
        del cgr


    def _burstLastRequest(self,gr):
        lr = gr.lastRequest
        gr.lastRequest = None
        if lr is not None and lr != self:            
            lr.lock.acquire()
            if lr.inProcess is False and lr.canceled is False:
                lr.lock.release()
                lr._putOnTaskQueue()
            else:
                lr.lock.release()
       
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
        self.cancelQueue = deque()
        self.childRequests = {}
        self.lock.release()
        p = self.parentRequest
        if p is not None:
            l = p._requestLevel + 1
            p._requestLevel = l
            
        if self.graph.suspended is False or self.parentRequest is not None:
            if self.canceled is False:
                while len(self.notifyQueue) > 0:
                    try:
                        func, kwargs = self.notifyQueue.pop()
                    except:
                        break
                    func(self.destination, **kwargs)
    
            waiters = []
            while len(self.waitQueue) > 0:
                try:
                    w = self.waitQueue.pop()
                    waiters.append(w)
                except:
                    break
            waiter = sorted(waiters, key=lambda x: -x[1]._requestLevel)
            for tr, req, gr in waiters:
                req.lock.acquire()
                if not req.canceled:
                    tr.finishedRequestGreenlets.put((-req._requestLevel, req, gr))
                    tr.workAvailableEvent.set()
                req.lock.release()
        else:
            self.graph.putFinalize(self)
        #self.parentRequest = None
        

        
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
            self.lock.acquire()
            childs = tuple(self.childRequests.values())
            self.childRequests = {}
            self.lock.release()
            for r in childs:
                r.cancel()            

    def _cancelParents(self):
        if not self._finished:
            self._cancel()
            if self.parentRequest is not None:
                self.parentRequest._cancelParents()


    def cancel(self):
        self.lock.acquire()
        if not self._finished:
            self.canceled = True
            self.lock.release()
            self._cancelChildren()
            #self._cancelParents()
        else:            
            self.lock.release()
        
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

    def setValue(self, value, notify = True):
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
        self._checkNotifyConnect(notify = notify)

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


    def connect(self, partner, notify = True):
        """
        connects the InputSlot to a partner OutputSlot
        
        when all InputSlots of an Operator are connected (or
        are given a value by calling .setvalue(value))
        the Operator is notified via its notifyConnectAll() method.
        """
        if partner is None:
            self.disconnect()
            return    
            
        if not isinstance(partner,(OutputSlot,MultiOutputSlot)):
            self.setValue(partner)
            return
            
        assert partner is None or isinstance(partner, (OutputSlot, MultiOutputSlot)), \
               "InputSlot(name=%s, operator=%s).connect: partner has type %r" \
               % (self.name, self.operator, type(partner))
        
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
                self._checkNotifyConnect(notify = notify)
    
    def _checkNotifyConnect(self, notify = True):
        if self.operator is not None:
            if notify:
              self.operator._notifyConnect(self)
            self._checkNotifyConnectAll()
            
    def _checkNotifyConnectAll(self, notify = True):
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
            "_stype" : self._stype,
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
            "_stype" : "_stype",
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
                
    def _connect(self, partner, notify = True):
        if partner not in self.partners:
            self.partners.append(partner)
        #Re-run the connect anyway, because we might want to
        #propagate information like this
        partner.connect(self, notify = notify)
        
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
            "_stype" : self._stype
            
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
            "_stype" : "_stype"
            
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
        
    def resize(self, size, notify = True, event = None):
        oldsize = len(self)
        
        while size > len(self):
            self._appendNew(notify=False,connect=False)
            
        while size < len(self):
            self._removeInputSlot(self[-1], notify = False)

        if notify:
          self._notifySubSlotResize(tuple(),tuple(),size = size,event = event)

        for i in range(oldsize,size):
          self._connectSubSlot(i, notify = notify)

    def _connectSubSlot(self,slot, notify = True):
      if type(slot) == int:
        index = slot
        slot = self.inputSlots[slot]
      else:
        index = self.inputSlots.index(slot)

      if self.partner is not None:
          if self.partner.level > 0:
              if len(self.partner) >= len(self):
                  self.partner[index]._connect(slot, notify = notify)
          else:
              self.partner._connect(slot, notify = notify)
      if self._value is not None:
          slot.setValue(self._value, notify = notify)    


                    
    def _appendNew(self, notify = True, event = None, connect = True):
        if self.level <= 1:
            islot = InputSlot(self.name ,self, stype = self._stype)
        else:
            islot = MultiInputSlot(self.name,self, stype = self._stype, level = self.level - 1)
        self.inputSlots.append(islot)
        islot.name = self.name
        index = len(self)-1
        if notify:
          self._notifySubSlotInsert((islot,),tuple(), event = event)
        if connect:
          self._connectSubSlot(index)
        return islot


    def _insertNew(self, index, notify = True, connect = True):
        if self.level == 1:
            islot = InputSlot(self.name,self, self._stype)
        else:
            islot = MultiInputSlot(self.name,self, stype = self._stype, level = self.level - 1)
        self.inputSlots.insert(index,islot)
        islot.name = self.name
        if notify:
          self._notifySubSlotInsert((islot,),tuple())
        if connect:
          self._connectSubSlot(index)

        return islot
    
    
    def _checkNotifyConnectAll(self, notify = True):
        
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

        
    def connect(self,partner, notify = True):
        if partner is None:
            self.disconnect()
            return
        
        if not isinstance(partner,(OutputSlot,MultiOutputSlot)):
            self.setValue(partner)
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
                
                if notify:
                  self.operator._notifyConnect(self)
                self._checkNotifyConnectAll(notify = notify)
                
            elif partner.level < self.level:
                #if self.partner is not None:
                #    self.partner.disconnectSlot(self)                
                self.partner = partner
                for i, slot in enumerate(self):                
                    slot.connect(partner)
                    if self.operator is not None:
                        self.operator._notifySubConnect((self,slot), (i,))
                self._checkNotifyConnectAll(notify=notify)
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

    def _notifySubSlotInsert(self,slots,indexes,event = None):
        index = self.inputSlots.index(slots[0])
        self.operator._notifySubSlotInsert( (self,) + slots, (index,) + indexes, event = event)

    def _notifyDisconnect(self, slot):
        index = self.inputSlots.index(slot)
        self.operator._notifySubDisconnect((self, slot), (index,))
    
    def _notifySubDisconnect(self, slots, indexes):
        index = self.inputSlots.index(slots[0])
        self.operator._notifySubDisconnect((self,) + slots, (index,) + indexes)
        
    def _notifySubSlotRemove(self, slots, indexes, event = None):
        if len(slots)>0:
            index = self.inputSlots.index(slots[0])
            indexes = (index,) + indexes
        self.operator._notifySubSlotRemove((self,) + slots, indexes, event = event)
            
    def _notifySubSlotResize(self,slots,indexes,size,event = None):
        if len(slots) > 0:
          index = self.inputSlots.index(slots[0])
          indexes = (index,) + indexes
        self.operator._notifySubSlotResize((self,) + slots, indexes, size, event = event)


    def disconnect(self):
        for slot in self.inputSlots:
            slot.disconnect()
        if self.partner is not None:
            self.operator._notifyDisconnect(self)
            self.partner.disconnectSlot(self)
            self.inputSlots = []
            self.partner = None
    
    def removeSlot(self, index, notify = True, event = None):
        slot = index
        if type(index) is int:
            slot = self[index]
        self._removeInputSlot(slot, notify, event = event)
    
    def _removeInputSlot(self, inputSlot, notify = True, event = None):
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
            self._notifySubSlotRemove((),(index,),event = event)
        self.inputSlots.remove(inputSlot)

        

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
            "_stype" : self._stype,
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
            "_stype" : "_stype",
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
    
    def append(self, outputSlot, event = None):
        outputSlot.operator = self
        self.outputSlots.append(outputSlot)
        index = len(self.outputSlots) - 1
        for p in self.partners:
            p.resize(len(self), event = event)
            outputSlot._connect(p.inputSlots[index])
    
    def _insertNew(self,index, event = None):
        oslot = OutputSlot(self.name,self,stype=self._stype)
        self.insert(index,oslot, event = event)


    def insert(self, index, outputSlot, event = None):
        outputSlot.operator = self
        self.outputSlots.insert(index,outputSlot)
        for p in self.partners:
            pslot = p._insertNew(index, event = event)
            outputSlot._connect(pslot)
        
    def remove(self, outputSlot, event = None):
        index = self.outputSlots.index(outputSlot)
        self.pop(index, event = event)
    
    def pop(self, index = -1, event = None):
        oslot = self.outputSlots[index]
        for p in oslot.partners:
            if isinstance(p.operator, MultiInputSlot):
                p.operator._removeInputSlot(p, event = event)
        
        oslot.disconnect()
        oslot = self.outputSlots.pop(index)
        
    def _connect(self, partner, notify = True):
        if partner not in self.partners:
            self.partners.append(partner)
        #Re-run the connect anyway, because we might want to
        #propagate information like this
        partner.connect(self, notify = notify)
        
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
            
    def resize(self, size, event = None):
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
            p.resize(size, event = event)
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
            "_stype" : self._stype,
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
            "_stype" : "_stype",
            "outputSlots" : "outputSlots"
            
        },patchBoard)
            
        return s


class OutputDict(dict):
    
    def __setitem__(self, key, value):
        assert isinstance(value, (OutputSlot, MultiOutputSlot)), "ERROR: all elements of .outputs must be of type OutputSlot or MultiOutputSlot, you provided %r !" % (value,)
        return dict.__setitem__(self, key, value)

    @classmethod
    def reconstructFromH5G(cls, h5g, patchBoard):
        temp = OutputDict()
        patchBoard[h5g.attrs["id"]] = temp
        for i,g in h5g.items():
            temp[str(i)] = g.reconstructObject(patchBoard)
        return temp

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
    
    
    """
    This method is called when an output of another operator on which 
    this operators dependds, i.e. to which it is connected gets invalid. 
    The region of interest of the inputslot which is now dirty is specified
    in the key property, the input slot which got dirty is specified in the inputSlot
    property.
    
    This method must calculate what output ports and which subregions of them are
    invalidated by this, and must call the .setDirty(key) of the corresponding
    outputslots.
    """
    def notifyDirty(self, inputSlot, key):
        # simple default implementation
        # -> set all outputs dirty    
        for os in self.outputs.values():
            os.setDirty(slice(None,None,None))
    
    
    """
    This method corresponds to the notifyDirty method, but is used
    for multidimensional inputslots, which contain subslots.
    
    The slots argument is a list of slots in which the first
    element specifies the mainslot (i.e. the slot which is specified
    in the operator.). The next element specifies the sub slot, i.e. the 
    child of the main slot, and so forth.
    
    The indexes argument is a list of the subslot indexes. As such it is 
    of lenght n-1 where n is the length of the slots arugment list.
    It contains the indexes of all subslots realtive to their parent slot.
    
    The key argument specifies the region of interest.    
    """
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

    def _notifySubSlotRemove(self, slots, indexes, event = None):
        self.notifySubSlotRemove(slots, indexes)
        
    def _notifySubSlotInsert(self,slots,indexes, event = None):
        self.notifySubSlotInsert(slots,indexes)

    def _notifySubSlotResize(self,slots,indexes, size,event = None):
        print "EVENT:",event
        self.notifySubSlotResize(slots,indexes,size,event)

    def connect(self, **kwargs):
        for k in kwargs:
          if k in self.inputs.keys():
            self.inputs[k].connect(kwargs[k])
          else:
            print "ERROR, connect(): operator %s has no slot named %s" % (self.name, k)
            print "                  available inputSlots are: ", self.inputs.keys()
            assert(1==2)

    """
    This method is called opon connection of an inputslot.
    The slot is specified in the inputSlot argument.
    
    The operator should setup the output slots that depend on this
    inputslot accordingly.
    
    reimplementation of this method is optional, a full setup
    may also be done only in the .notifyConnectAll method.
    """
    def notifyConnect(self, inputSlot):
        pass
    
    """
    This method is called opon connection of all inputslots of
    an operator.
    
    The operator should setup the output all outputslots accordingly.
    this includes setting their shape and axistags properties.
    """
    def notifyConnectAll(self):
        pass


    """
    This method corresponds to the notifyConnect method, but is used
    for multidimensional inputslots, which contain subslots.
    
    The slots argument is a list of slots in which the first
    element specifies the mainslot (i.e. the slot which is specified
    in the operator.). The next element specifies the sub slot, i.e. the 
    child of the main slot, and so forth.
    
    The indexes argument is a list of the subslot indexes. As such it is 
    of lenght n-1 where n is the length of the slots arugment list.
    It contains the indexes of all subslots realtive to their parent slot.
    
    The key argument specifies the region of interest.    
    """    
    def notifySubConnect(self, slots, indexes):
        pass
   
   
    """
    This method is called when a subslot of a multidimensional inputslot
    is removed.
    
    The slots argument is a list of slots in which the first
    element specifies the mainslot (i.e. the slot which is specified
    in the operator.). The next element specifies the sub slot, i.e. the 
    child of the main slot, and so forth.
    
    The indexes argument is a list of the subslot indexes. As such it is 
    of lenght n-1 where n is the length of the slots arugment list.
    It contains the indexes of all subslots realtive to their parent slot.
    
    The operator should recalculate the shapes of its output slots 
    when neccessary.
    """   
    def notifySubSlotRemove(self, slots, indexes):
        pass
         
    def notifySubSlotInsert(self,slots,indexes):
      pass

    def notifySubSlotResize(self,slots,indexes,size,event):
      pass

    """
    This method of the operator is called when a connected operator
    or an outside user of the graph wants to retrieve the calculation results
    from the operator.
    
    The slot which is requested is specified in the slot arguemt,
    the region of interest is specified in the key property.
    The result area into which the calculation results MUST be written is 
    specified in the result argument. "result" is an numpy.ndarray that
    has the same shape as the region of interest(key).
    
    The method must retrieve all required inputs that are neccessary to
    calculate the requested output area from its input slots,
    run the calculation and put the results into the provided result argument.
    """
    def getOutSlot(self, slot, key, result):
        return None


    """
    This method corresponds to the getOutSlot method, but is used
    for multidimensional inputslots, which contain subslots.
    
    The slots argument is a list of slots in which the first
    element specifies the mainslot (i.e. the slot which is specified
    in the operator.). The next element specifies the sub slot, i.e. the 
    child of the main slot, and so forth.
    
    The indexes argument is a list of the subslot indexes. As such it is 
    of lenght n-1 where n is the length of the slots arugment list.
    It contains the indexes of all subslots realtive to their parent slot.
    
    The key argument specifies the region of interest.    
    """
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


    """
    This method is called when an inputslot is disconnected.

    The slot argument specifies the inputslot that is affected.
        
    The operator should recalculate the shapes of its output slots
    when neccessary..
    """    
    def notifyDisconnect(self, slot):
        pass
    
    
    """
    This method corresponds to the notifyDisconnect method, but is used
    for multidimensional inputslots, which contain subslots.
    
    The slots argument is a list of slots in which the first
    element specifies the mainslot (i.e. the slot which is specified
    in the operator.). The next element specifies the sub slot, i.e. the 
    child of the main slot, and so forth.
    
    The indexes argument is a list of the subslot indexes. As such it is 
    of lenght n-1 where n is the length of the slots arugment list.
    It contains the indexes of all subslots realtive to their parent slot.
    
    The key argument specifies the region of interest.    
    """    
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
        self._eventCounter = 0
        self._processedEvents = {}
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
                    return
                
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
        op.disconnect()
        index = self.innerOperators.index(op)
        self.innerOperators.remove(op)
        for name, oslot in self.outputs.items():
            oslot.pop(index)

    def _connectInnerOutputsForIndex(self, index):
        innerOp = self.innerOperators[index]
        for key,mslot in self.outputs.items():            
            print len(mslot), index
            print mslot[index]
            print innerOp.outputs[key]
            mslot[index] = innerOp.outputs[key]

            
    def _connectInnerOutputs(self):
        #for k,mslot in self.outputs.items():
        #    #assert isinstance(mslot,MultiOutputSlot)
        #    mslot.resize(len(self.innerOperators))

        for key,mslot in self.outputs.items():
            for index, innerOp in enumerate(self.innerOperators):
                if innerOp is not None and index < len(mslot):
                  mslot[index] = innerOp.outputs[key]

    def _ensureInputSize(self, numMax = 0, event = None):
        
        if event is None:
          self._eventCounter += 1
          event = (id(self),self._eventCounter)

        if self._processedEvents.has_key(event):
          return

        self._processedEvents[event] = True
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

        for name, islot in self.inputs.items():
            islot.resize(maxLen, notify = False, event = event)

        for name, oslot in self.outputs.items():
            oslot.resize(maxLen,event = event)

        #for name, oslot in self.outputs.items():
        #    oslot.resize(maxLen)

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
        pass
    
    def _notifySubSlotInsert(self,slots,indexes, event = None):
        print "_notifySubSlotInsert Wrapper of", self.operator.name,slots, indexes
        if len(indexes) != 1:
          return
        
        if event is None:
          self._eventCounter += 1
          event = (id(self),self._eventCounter)

        if self._processedEvents.has_key(event):
          return

        self._processedEvents[event] = True
                                                            
        op = self._createInnerOperator()
        self.innerOperators.insert(indexes[0],op)

        for k,oslot in self.outputs.items():
          oslot._insertNew(indexes[0], event = event)


        for k,islot in self.inputs.items():
          if islot != slots[0]:
            islot._insertNew(indexes[0],notify=False, event = event)

    def _notifySubSlotResize(self,slots,indexes,size,event = None):
        if len(indexes) != 0:
          return

        if event is None:
          self._eventCounter += 1
          event = (id(self),self._eventCounter)

        print "_notifySubSlotResize Wrapper of", self.operator.name,slots, indexes,size
        print "Wrapper: ",self
        print "Keys:", self._processedEvents.keys()
        print "event", event, " has_key", self._processedEvents.has_key(event)

        if self._processedEvents.has_key(event):
          return

        self._processedEvents[event] = True

        oldSize = len(self.innerOperators)

        while len(self.innerOperators) < size:
          op = self._createInnerOperator()
          self.innerOperators.append(op)

        while len(self.innerOperators) > size:
          op = self.innerOperators.pop()
  

        for k,oslot in self.outputs.items():
          oslot.resize(size,event = event)

        for k,islot in self.inputs.items():
          if islot != slots[0]:
            islot.resize(size,event = event)





    def _notifySubSlotRemove(self, slots, indexes, event = None):
        
        print "_notifySubSlotRemove Wrapper of ", self.operator.name,slots, indexes
        if len(indexes) != 1:
          return
        
        if event is None:
          self._eventCounter += 1
          event = (id(self),self._eventCounter)

        if self._processedEvents.has_key(event):
          return

        self._processedEvents[event] = True

        op = self.innerOperators[indexes[0]]


        for k,oslot in self.outputs.items():
          oslot.pop(indexes[0], event = event)

        self.innerOperators.pop(indexes[0])

        for k,islot in self.inputs.items():
          if islot != slots[0]:
            islot.removeSlot(indexes[0],notify=False, event = event)


    def _notifySubConnect(self, slots, indexes):
        print "_notifySubConnect Wrapper of", self.operator.name, slots, indexes
        print len(self.innerOperators)
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

    @property
    def freeWorkers(self):
        return self._originalGraph.freeWorkers
 
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
        self.finishedRequestGreenlets = PriorityQueue()
        self.currentRequest = None
        self.requests = deque()
        self.process = psutil.Process(os.getpid())
        self.number =  len(self.graph.workers)
        self.workAvailableEvent = Event()
        self.workAvailableEvent.clear()
        self.openUserRequests = set()
        self.greenlet = None
    
    def signalWorkAvailable(self): 
        self.workAvailableEvent.set()
        
        
    def run(self):
        ct = current_thread()
        self.greenlet = greenlet.getcurrent()
        prioLastReq = 0
        while self.graph.running:
            if not self.workAvailableEvent.isSet():
                self.graph.freeWorkers.append(self)
            self.workAvailableEvent.wait()#(0.2)
            try:
                self.graph.freeWorkers.remove(self)
            except:
                pass
            self.workAvailableEvent.clear()
            self._hasSlept = True
            
            while not self.graph.tasks.empty() or not self.finishedRequestGreenlets.empty() or (not self.graph.newTasks.empty() and self._hasSlept):       
                #print self, len(self.openUserRequests)                
                while not self.finishedRequestGreenlets.empty():
                    prioFinReq, req, gr = self.finishedRequestGreenlets.get(block = False)
                    gr.currentRequest = req                 
                    if req.canceled is False:
                        gr.switch()
                    del gr
                    if prioLastReq < prioFinReq:
                        #print prioLastReq, prioFinReq
                        break
                        
                        
                        
                task = None
                try:
                    prioLastReq,task = self.graph.tasks.get(block = False)#timeout = 1.0)
                except Empty:
                    prioLastReq = 0
                    pass                
                if task is not None:
                    reqObject = task
                    if reqObject.canceled is False:
                        gr = CustomGreenlet(reqObject._execute)
                        gr.thread = self
                        gr.switch( gr)
                        del gr
                        
                if len(self.openUserRequests) < 4:
                    self._hasSlept = True                    
                    task = None
                    try:
                        pr,task = self.graph.newTasks.get(block = False)#timeout = 1.0)
                    except Empty:
                        pass               
                    if task is not None:
                        reqObject = task
                        self.openUserRequests.add(reqObject)                
                        if reqObject.canceled is False:
                            gr = CustomGreenlet(reqObject._execute)
                            gr.thread = self
                            gr.switch( gr)
                            del gr
                else:
                    self._hasSlept = False
                for r in self.openUserRequests.copy():
                    if r.canceled or r._finished:
                        self.openUserRequests.remove(r)
                        self._hasSlept = True
        self.graph.workers.remove(self)

    
class Graph(object):

    _runningGraphs = [] 

    @atexit.register
    def stopGraphs():
       for g in Graph._runningGraphs:
          g.stopGraph()


    def __init__(self, numThreads = None, softMaxMem =  None):
        self.operators = []
        self.tasks = PriorityQueue() #Lifo <-> depth first, fifo <-> breath first
        self.newTasks = PriorityQueue() #Lifo <-> depth first, fifo <-> breath first
        self.workers = []
        self.freeWorkers = deque()
        self.running = True
        self.suspended = False
        self.stopped = False
        
        self._suspendedRequests = deque()
        self._suspendedNotifyFinish = deque()
        
        if numThreads is None:
            self.numThreads = detectCPUs()
            if self.numThreads <= 2:
              self.numThreads += 1
            if self.numThreads > 3:
                self.numThreads -= 1
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
        print "GRAPH: using %d Threads" % (self.numThreads)
        print "GRAPH: using target size of %dMB of Memory" % (softMaxMem / 1024**2)
        self.softMaxMem = softMaxMem # in bytes
        self.softCacheMem = softMaxMem * 0.5
        self._registeredCaches = deque()
        self._allocatedCaches = deque()
        self._usedCacheMemory = 0
        self._memAllocLock = threading.Lock()
        Graph._runningGraphs.append(self)
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
        i = 0
        maxCount = len(self._allocatedCaches)
        while len(self._allocatedCaches) > 0 and i < maxCount:
            i +=1            
            if freedMem < freesize: #c._memorySize() > 1024
                try:
                    c = self._allocatedCaches.popleft()
                except:
                    c = None
                if c is not None:
                    fmc = 0
                    if c._memorySize() > 1024:
                    #FIXME: handle very small chunks
                        fmc = c._freeMemory()
                        freedMem += fmc
                    if fmc == 0: #freeing did not succeed
                        self._allocatedCaches.append(c)
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
        if accesses > 30:
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
        if self.suspended is False:
            task = reqObject
            if task.parentRequest is not None:
                self.tasks.put((-task._requestLevel,task))
            else:
                self.newTasks.put((-task._requestLevel,task))
            if len(self.freeWorkers) > 0:
                try:
                    w = self.freeWorkers.popleft()
                    w.signalWorkAvailable()
                except:
                    pass
        else:
            self._suspendedRequests.append(reqObject)

    def putFinalize(self, reqObject):
        self._suspendedNotifyFinish.append(reqObject)
    
    def stopGraph(self):
        if not self.stopped:
            print "Graph: stopping..."        
            self.stopped = True
            self.suspendGraph()

    def suspendGraph(self):
        if not self.suspended:
          tasks = []
          while not self.newTasks.empty():
              try:
                  t = self.newTasks.get(block = False)
                  tasks.append(t)
              except:
                  break
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

          print "   Waiting for workers..."          
          for w in self.workers:
            w.signalWorkAvailable()
          while len(self.workers) > len(self.freeWorkers):
              time.sleep(0.1)
              print len(self.workers),len(self.freeWorkers)
          time.sleep(0.1)
          while len(self.workers) > len(self.freeWorkers):
              time.sleep(0.1)
          print "   ok"
          print "finished."
          self._runningGraphs.remove(self)
            
    def resumeGraph(self):        
        if self.stopped:
            self.stopped = False
            self._suspendedRequests = deque()
            self._suspendedNotifyFinish = deque()
            for w in self.workers:
                w.openUserRequests = set()            
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
            self._runningGraphs.append(self)
            print "finished."

        
    def finalize(self):
        self.running = False
        for w in self.workers:
            w.signalWorkAvailable()
            w.join()
        self.stopGraph()

    def registerOperator(self, op):
        self.operators.append(op)
    
    def removeOperator(self, op):
        assert op in self.operators, "Operator %r not a registered Operator" % op
        self.operators.remove(op)
        op.disconnect()
 
    def dumpToH5G(self, h5g, patchBoard):
        self.stopGraph()
        h5g.dumpSubObjects({
                    "operators" : self.operators,
                    "numThreads": self.numThreads,
                    "softMaxMem": self.softMaxMem
                },patchBoard)    
        self.resumeGraph()

    
    @classmethod
    def reconstructFromH5G(cls, h5g, patchBoard):
        numThreads = h5g["numThreads"].reconstructObject()
        softMaxMem = h5g["softMaxMem"].reconstructObject()

        g = Graph(numThreads = numThreads, softMaxMem = softMaxMem)
        patchBoard[h5g.attrs["id"]] = g 
        g.stopGraph()
        
        h5g.reconstructSubObjects(g, {
                    "operators": "operators",
                    "numThreads": "numThreads",
                    "softMaxMem" : "softMaxMem"
                },patchBoard)    
        g.resumeGraph()
        return g
 
