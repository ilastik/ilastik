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
import string
import types
import itertools

from h5dumprestore import instanceClassToString, stringToClass
from helpers import itersubclasses, detectCPUs, deprecated, warn_deprecated
from collections import deque
from Queue import Queue, LifoQueue, Empty, PriorityQueue
from threading import Thread, Event, current_thread, Lock
import greenlet
import weakref
import threading

import rtype
from roi import sliceToRoi, roiToSlice
from lazyflow.stype import ArrayLike
from lazyflow import stype

greenlet.GREENLET_USE_GC = False #use garbage collection
sys.setrecursionlimit(1000)



class Operators(object):
    
    operators = {}
    
    @classmethod
    def register(cls, opcls):
        cls.operators[opcls.__name__] = opcls
        print "registered operator %s (%s)" % (opcls.name, opcls.__name__)

    @classmethod
    def registerOperatorSubclasses(cls):
        for o in itersubclasses(Operator):
            cls.register(o)
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
      
class CustomGreenlet(greenlet.greenlet):
    __slots__ = ("lastRequest","currentRequest","thread")


def patchForeignCurrentThread():
  setattr(current_thread(), "finishedRequestGreenlets", deque())#PriorityQueue())
  setattr(current_thread(), "workAvailableEvent", Event())
  setattr(current_thread(), "process", psutil.Process(os.getpid()))
  setattr(current_thread(), "lastRequest", None)
  setattr(current_thread(), "greenlet", None)

#patch main thread
patchForeignCurrentThread()

class GetItemRequestObject(object):
    """ 
    Enables the syntax
    InputSlot[:,:].writeInto(array).wait() or
    InputSlot[:,:].writeInto(array).notify(someFunction)
    
    It is returned by a call to the __getitem__ method of Slot.
 
    """

    __slots__ = ["roi", "destination", "slot", "func", "canceled",
                 "_finished", "inProcess", "parentRequest", "childRequests",
                 "graph", "waitQueue", "notifyQueue", "cancelQueue",
                 "_requestLevel", "arg1", "lock", "_priority"]
        
    def __init__(self, slot, roi, destination, priority):        
        self.roi = roi
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
        self.lock = Lock()
        if isinstance(slot, InputSlot) and self.slot._value is None:
            self.func = slot.partner.operator.execute
            self.arg1 = slot.partner            
        elif isinstance(slot, OutputSlot):
            self.func =  slot.operator.execute
            self.arg1 = slot
        else:
            # we are in the ._value case of an inputSlot
             if self.destination is None:
                self.destination = self.slot._allocateDestination(self.roi)
             self.destination = self.slot._writeIntoDestination(self.destination, self.slot._value, self.roi)
             self._finished = True
        if not self._finished:
            gr = greenlet.getcurrent()
            if isinstance(gr,CustomGreenlet):
                # we delay the firing of an request until
                # another one arrives 
                # by this we make sure that one call path
                # through the graph is done in one greenlet/thread
                
                self._burstLastRequest(gr)
                self.parentRequest = gr.currentRequest
                gr.currentRequest.lock.acquire()
                gr.currentRequest.childRequests[self] = self
                self._requestLevel = gr.currentRequest._requestLevel + self._priority + 1
                gr.lastRequest = self
                gr.currentRequest.lock.release()

            else:
                # we are in a unknownnnon worker thread
                tr = current_thread()
                if not hasattr(tr,"lastRequest"):
                  #some bad person called our library from a completely unknown strange thread
                  patchForeignCurrentThread()
                lr = tr.lastRequest
                tr.lastRequest = self
                if lr is not None:
                  lr.lock.acquire()
                  if lr.inProcess is False:
                    lr.inProcess = True
                    lr.lock.release()
                    lr._putOnTaskQueue()
                  else:
                    lr.lock.release()
                self._requestLevel = self._priority
            

    def _execute(self, gr):
        self.inProcess = True
        temp = gr.currentRequest
        if self.destination is None:
            self.destination = self.slot._allocateDestination( self.roi )
        gr.currentRequest = self
        try:
          assert(len(self.roi.toSlice()) == self.destination.ndim), "%r ndim=%r, shape=%r" % (self.roi.toSlice(), self.destination.ndim, self.destination.shape)
          ret = self.func(self.arg1,self.roi, self.destination)
          if ret == None:
              warn_deprecated("Old style operator with no return value in Op.execute() encountered: " + self.func.__self__.__class__.__name__)
          else:
              self.destination = ret
        except Exception,e:
          if isinstance(self.slot, InputSlot):
            print
            print "ERROR: Exception in Operator %s (%r)" % (self.slot.partner.operator.name, self.slot.partner.operator)
          else:
            pass 
          traceback.print_exc(e)
          sys.exit(1)
        self._finalize()        
        gr.currentRequest = temp

    def _putOnTaskQueue(self):
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

    def writeInto(self, destination, priority = 0):
        self.destination = destination
        if self.destination is not None:
            assert(len(self.roi.toSlice()) == self.destination.ndim), "%r ndim=%r, shape=%r" % (self.roi.toSlice(), self.destination.ndim, self.destination.shape)
        self._priority = priority
        return self

    @deprecated
    def allocate(self, priority = 0):
        if self.destination is None:
          return self.writeInto( None, priority)
        else:
          return self

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
            if not self._finished:
                if self.inProcess:   
                    if isinstance(gr,CustomGreenlet):
                        self.waitQueue.append((gr.thread, gr.currentRequest, gr))
                        gr.currentRequest.childRequests[self] = self
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
                        gr.thread.greenlet.switch(None)
                    else:
                        tr = current_thread()
                        if not hasattr(tr,"lastRequest"):
                          #some bad person called our library from a completely unknown strange thread
                          patchForeignCurrentThread()
                        lr = tr.lastRequest
                        tr.lastRequest = None
                        if lr is not None and lr != self:
                          lr.lock.acquire()
                          if lr.inProcess is False:
                            lr.inProcess = True
                            lr.lock.release()
                            lr._putOnTaskQueue()
                          else:
                            lr.lock.release()
                        cgr = CustomGreenlet(self.wait)
                        cgr.lastRequest = None
                        cgr.currentRequest = self
                        cgr.thread = tr                        
                        self.lock.release()
                        tr.greenlet = gr
                        cgr.switch(self)
                        self._waitFor(cgr,tr) #wait for finish
                else:
                    if isinstance(gr,CustomGreenlet):
                        self._burstLastRequest(gr)
                        self.inProcess = True
                        self.lock.release()
                        self._execute(gr)
                    else:
                        tr = current_thread()
                        if not hasattr(tr,"lastRequest"):
                          #some bad person called our library from a completely unknown strange thread
                          patchForeignCurrentThread()

                        lr = tr.lastRequest
                        tr.lastRequest = None
                        if lr is not None and lr != self:
                          lr.lock.acquire()
                          if lr.inProcess is False:
                            lr.inProcess = True
                            lr.lock.release()
                            lr._putOnTaskQueue()
                          else:
                            lr.lock.release()
                        cgr = CustomGreenlet(self._execute)
                        cgr.currentRequest = self
                        cgr.thread = tr
                        cgr.lastRequest = None
                        self.inProcess = True
                        self.lock.release()
                        tr.greenlet = gr
                        
                        cgr.switch(cgr)
                        self._waitFor(cgr,tr) #wait for finish
            else:
                self.lock.release()
            try:
              gr.currentRequest.childRequests.pop(self)
            except:
              pass
        else: # not (isinstance(self.slot, OutputSlot) or self.slot._value is None)
            if self.destination is None:
              self.destination = self.slot._allocateDestination(self.roi)
            self.slot._writeIntoDestination(self.destination, self.slot._value, self.roi)
        self._finished = True
        if self.canceled is False:
          assert self.destination is not None
          return self.destination
        else:
          return None
  
      
    def _waitFor(self, cgr, tr):
        while not cgr.dead:
            tr.workAvailableEvent.wait()
            tr.workAvailableEvent.clear()
            while len(tr.finishedRequestGreenlets) > 0:
                prio,req, gr = tr.finishedRequestGreenlets.pop()#get(block = False)
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
                lr.inProcess = True
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
                self.inProcess = True
                self.lock.release()
                self._putOnTaskQueue()
            else:
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
        nq = self.notifyQueue
        wq = self.waitQueue

        self.notifyQueue = deque()
        self.waitQueue = deque()

        self.lock.release()
        p = self.parentRequest
        self.parentRequest = None
        gr = greenlet.getcurrent()
        if p is not None:
            l = p._requestLevel + 1
            p._requestLevel = l
            
        if self.graph.suspended is False or self.parentRequest is not None:
            if self.canceled is False:
                while len(nq) > 0:
                    try:
                        func, kwargs = nq.pop()
                    except:
                        break
                    func(self.destination, **kwargs)
    
            while len(wq) > 0:
                w = wq.pop()
                tr, req, gr = w
                req.lock.acquire()
                if not req.canceled:
                    tr.finishedRequestGreenlets.append((-req._requestLevel,req,gr))#put((-req._requestLevel, req, gr))
                    req.lock.release()
                    tr.workAvailableEvent.set()
                else:
                  req.lock.release()
        else:
            self.graph.putFinalize(self)
        

        
    def _cancel(self):
        self.lock.acquire()
        canceled = True
        if len(self.waitQueue) == 0:
          if not self._finished:
              while canceled and len(self.cancelQueue) > 0:
                  try:
                      closure, kwargs = self.cancelQueue.pop()
                  except:
                      break
                  
                  canceled = canceld and not (closure(**kwargs) == False)

          self.lock.release()
          if canceled:
            self.canceled = True
            self._finalize()
          return canceled
        else:
          self.lock.release()
          return False

    def _cancelChildren(self,level):
            self.lock.acquire()
            childs = tuple(self.childRequests.values())
            self.childRequests = {}
            self.lock.release()
            for r in childs:
                r.cancel(level = level + 1)            

    def _cancelParents(self):
        if not self._finished:
            if self._cancel():
              if self.parentRequest is not None:
                self.parentRequest._cancelParents()


    def cancel(self, level = 0):
        if not self._finished:
            if self._cancel():
              self._cancelChildren(level = level)
              return True
            else:
              print "NOT CANCELING CHILDREN level=%d" % level, self
              return False

        
    def __call__(self):
        assert 1==2, "Please use the .wait() method, () is deprecated !"


class MetaDict(dict):
  def __init__(self, other=False):
    if(other):
      dict.__init__(self,other)
    else:
      dict.__init__(self)
    self._dirty = True
    #TODO: remove this, only for backwards compatability
    if not self.has_key("shape"):
      self.shape = None
    if not self.has_key("dtype"):
      self.dtype = None
    if not self.has_key("axistags"):
      self.axistags = None

  def __setattr__(self,name,value):
    if self.has_key(name):
      changed = True
      try:
        if self[name] == value:
          changed = False
      except:
        pass
      if changed:
        self["_dirty"] = True
    self[name] = value
    return value

  def __getattr__(self,name):
    return self[name]

  def copy(self):
    return MetaDict(dict.copy(self))

class Slot(object):
    """Common methods of all slot types."""

    @property
    def graph(self):
        return self.operator.graph
                        
    def __init__( self, name = "", operator = None, stype = ArrayLike, rtype = rtype.SubRegion, value = None, optional = False, level = 0):
        #if self.__class__ == Slot: # make Slot constructor "private"
            #raise Exception("Slot can't be constructed directly; use one of the derived slot types")
        if not hasattr(self, "_type"):
          self._type = None
        if type(stype) == str:
          stype = ArrayLike
        self.name = name
        self._optional = optional
        self.name = name
        self.operator = operator
        self.partner = None
        self.level = level
        self._value = None
        self._defaultValue = value
        self.rtype = rtype
        self.meta = MetaDict()
        self._subSlots = []
        self._stypeType = stype #class of stype
        self.stype = stype(self) #instance of stype
        self._clones = []

    @property
    def shape(self):
      return self.meta.shape

    @property
    def dtype(self):
      return self.meta.dtype

    @property
    def axistags(self):
      return self.meta.axistags

    @property
    def _shape(self):
        return self.meta.shape
        
    @_shape.setter
    def _shape(self,value):
      old = self.meta.shape
      self.meta.shape = value

    @property
    def _axistags(self):
      return self.meta.axistags
        
    @_axistags.setter
    def _axistags(self, value):
      old = self.meta.axistags
      self.meta.axistags = value

    @property
    def _dtype(self):
      return self.meta.dtype

    @_dtype.setter
    def _dtype(self, value):
      old = self.meta.dtype
      self.meta.dtype = value

    def _allocateDestination( self, key ):
        return self.stype.allocateDestination(key)
        
    def _writeIntoDestination( self, destination, value,roi ):
        return self.stype.writeIntoDestination(destination,value, roi)
                           
    def __getitem__(self, key):
        if self.level > 0:
            return self._subSlots[key]
        else:
          assert self.meta.shape is not None, "OutputSlot.__getitem__: self.shape is None !!! (operator %r [self=%r] slot: %s, key=%r" % (self.operator.name, self.operator, self.name, key)
          return self(pslice=key)


    def __setitem__(self, key, value):
        slot = self._subSlots[key]
        if slot != value:
            slot.disconnect()
            self._subSlots[key] = value
    
            oldslot = slot        
            newslot = value
            for p in oldslot.partners:
                newslot._connect(p)
        
    def __len__(self):
        return len(self._subSlots)
    
 
    @property
    def value(self):
        return self._value

    def setValue(self, value):
        changed = True
        try:
          if value == self._value:
            changed = False
        except:
          pass
        if changed:
          self._value = value
          for i,s in enumerate(self._subSlots):
              s.setValue(self._value)
          self._changed()    

    def __call__(self, *args, **kwargs):
      """
      new API

      the slot relays all arguments to the __init__ method
      of the Roi type. this allows lazyflow to support different
      types of rois without knowing anything about them.
      """
      roi = self.rtype(self,*args, **kwargs)
      return self.get( roi )

    def get( self, roi ):
      if not isinstance(self.partner, (InputSlot, MultiInputSlot)):
        return GetItemRequestObject(self,roi,None,0)        
      else:
        return GetItemRequestObject(self.partner, roi, None, 0)


    def _registerClone(self, slot):
      if not slot in self._clones:
        self._clones.append(slot)

    def _unregisterClone(self, slot):
      if slot in self._clones:
        self._clones.remove(slot)

    def getInstance(self, operator, level = None):
        if level is None:
          level = self.level
        if self._type == "input":
          if level > 0:
            s = MultiInputSlot(self.name, operator, stype = self._stypeType, rtype = self.rtype, value = self._defaultValue, optional = self._optional, level = level)
          else:
            s = InputSlot(self.name, operator, stype = self._stypeType, rtype = self.rtype, value = self._defaultValue, optional = self._optional)
        elif self._type == "output":
          if level > 0:
            s= MultiOutputSlot(self.name, operator, stype = self._stypeType, rtype = self.rtype, value = self._defaultValue, optional = self._optional, level = level)
          else:
            s= OutputSlot(self.name, operator, stype = self._stypeType, rtype = self.rtype, value = self._defaultValue, optional = self._optional)
        return s

    def notifyDisconnect(self, slot):
      pass

class InputSlot(Slot):
    """
    The base class for input slots, it provides methods
    to connect the InputSlot to an OutputSlot of another
    operator (i.e. .connect(partner) call) or allows 
    to directly provide a value as input (i.e. .setValue(value) call)
    """
    
    def __init__(self, name = "", operator = None, stype = ArrayLike, rtype=rtype.SubRegion, value = None, optional = False):
        self._type = "input"
        super(InputSlot, self).__init__(name = name, operator = operator, stype = stype, rtype=rtype, value = value, optional = optional)
        self.partner = None
 

    def _changed(self, notify = True):
      if self.partner is not None:
        self.meta = self.partner.meta.copy()
      self._checkNotifyConnectAll(notify = notify)
      for c in self._clones:
        c._changed(notify)

    def setValue(self, value, notify = True):
        """
        This methods allows to directly provide an array
        or other entitiy as input the the InputSlot instead
        of connecting it to a partner OutputSlot.
        """
        assert self.partner == None, "InputSlot %s (%r): Cannot dot setValue, because it is connected !" %(self.name, self)
        changed = True
        try:
          if value == self._value:
            changed = False
        except:
          pass
        if changed:
          if self.stype.isCompatible(value):
            self._value = value
            self.stype.setupMetaForValue(value)
            self._changed()

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
        if self._value is None and self.partner is None or not self.stype.isConfigured():
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
            
        if not isinstance(partner,(OutputSlot,MultiOutputSlot,Operator, InputSlot, MultiInputSlot)):
            self.setValue(partner)
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
            self.meta = partner.meta.copy()
            if not isinstance(partner, InputSlot):
              partner._connect(self)
            else:
              partner._registerClone(self)
            self.stype.connect(partner)
            if self.stype.isConfigured():
                self._changed()
    
    def _checkNotifyConnectAll(self, notify = True):
        """
        notify operator of connection
        the operator may do a compatibility
        check that involves
        more then one slot
        """
        
        if self.operator is not None:
          # check wether all slots are connected and notify operator            
          allConnected = True
          for slot in self.operator.inputs.values():
              if slot._optional is False and slot.connected() is False:
                  allConnected = False
                  break
          if allConnected:
              self.operator._setupOutputs()
                
    def disconnect(self):
        """
        Disconnect a InputSlot from its partner
        """
        #TODO: also reset ._value ??
        if self.partner is not None:
            if not isinstance(self.partner, (InputSlot, MultiInputSlot)):
              self.partner.disconnectSlot(self)
            else:
              self.partner._unregisterClone(self)
        self.partner = None
        self.meta = MetaDict()
        
    
            
    def setDirty(self, *args,**kwargs):
        """
        this method is called by a partnering OutputSlot
        when its content changes.
        
        the key parameter identifies the changed region
        of an numpy.ndarray
        """
        assert self.operator is not None, \
               "Slot '%s' cannot be set dirty, slot not belonging to any actual operator instance" % self.name
        if self.connected():
          roi = self.rtype(self,*args,**kwargs)
          print "Input %r of %r is dirty" % (self.name, self.operator)
          self.operator.propagateDirty(self, roi)
          for c in self._clones:
            c.setDirty(*args,**kwargs)
    
    def __setitem__(self, key, value):
        assert self.operator is not None, "cannot do __setitem__ on Slot '%s' -> no operator !!"     
        roi = self.rtype(self,pslice = key)
        if self._value is not None:
            self._value[key] = value
            self.setDirty(roi) # only propagate the dirty key at the very beginning of the chain
        
        self.operator.setInSlot(self,key,value)
        
    def dumpToH5G(self, h5g, patchBoard):
        h5g.dumpSubObjects({
            "name" : self.name,
            "level" : self.level,
            "operator" : self.operator,
            "partner" : self.partner,
            "value" : self._value,
            "stype" : self.stype
            
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
            "stype" : "stype"
            
        },patchBoard)

        return s
    
class OutputSlot(Slot):
    """
    The base class for output slots, it provides methods
    to connect the OutputSlot to an InputSlot of another
    operator (i.e. .connect(partner) call).
    
    the content of the OutputSlot e.g. the result of the operator
    it belongs to can be requested with the usual
    python array slicing syntax, i.e.
    
    outputslot[3,:,14:32]
    
    this call returns an GetItemRequestObject.
    """    
    
    
    def __init__(self, name = "", operator = None, stype = ArrayLike, rtype = rtype.SubRegion, value = None, optional = False, level = 0):
        self._type = "output"
        super(OutputSlot, self).__init__(name = name, operator = operator, stype = stype, rtype=rtype, level = 0)
        self._metaParent = operator
        self.operator = operator
        self.partners = []

        self._dirtyCallbacks = []
    

    def _changed(self):
      if self.meta._dirty:
        self.meta._dirty = False
        for p in self.partners:
          p._changed()


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
            
    def setDirty(self, *args, **kwargs):
        """
        This method can be called by an operator
        to indicate that a region (identified by key)
        has changed and needs recalculation.
        
        the method notifies all InputSlots that are connected to
        this output slot
        """

        if not self.stype.isConfigured():
            return
        if not isinstance(args[0],rtype.Roi):
          roi = self.rtype(self, *args, **kwargs)
        else:
          roi = args[0]

        for p in self.partners:
            p.setDirty(roi) #set everything dirty
            
        for cb in self._dirtyCallbacks:
            cb[0](roi.toSlice(), **cb[1])

    def __setitem__(self, key, value):
        for p in self.partners:
            p[key] = value

    
    def dumpToH5G(self, h5g, patchBoard):
        h5g.dumpSubObjects({
            "name" : self.name,
            "level" : self.level,
            "operator" : self.operator,
            "partners" : self.partners,
            "stype" : self.stype
            
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
            "stype" : "stype"
            
        },patchBoard)
            
        return s
        

class MultiInputSlot(Slot):
    """
    The MultiInputSlot is a multidimensional InputSlot.
    
    it contains nested lists of InputSlot objects.
    """
    
    def __init__(self, name = "", operator = None, stype = ArrayLike, rtype=rtype.SubRegion, level = 1, value = None, optional = False):
        self._type = "input"
        self.partner = None
        self._subSlots = []
        self.inputs = {}
        super(MultiInputSlot, self).__init__(name = name, operator = operator, stype = stype, rtype=rtype, value = value, optional = optional, level = level)
    
    def resize(self, size, notify = True, event = None):
        oldsize = len(self)
        if self.partner and len(self.partner) != size:
          self.partner.resize(size)
        while size > len(self):
            self._appendNew(notify=False,connect=False)
            
        while size < len(self):
            self._removeInputSlot(self[-1], notify = False)

        for i in range(0,size):
          self._connectSubSlot(i, notify = False)
        
        self._checkNotifyConnectAll()
        for c in self._clones:
          c.resize(size, notify, event)

    def _connectSubSlot(self,slot, notify = True):
      if type(slot) == int:
        index = slot
        slot = self._subSlots[slot]
      else:
        index = self._subSlots.index(slot)

      if self.partner is not None:
          if self.partner.level == self.level:
              if len(self.partner) > index:
                  self.partner[index]._connect(slot, notify = notify)
          else:
              slot.connect(self.partner)
      if self._value is not None:
          slot.setValue(self._value, notify = notify)    


                    
    def _appendNew(self, notify = True, event = None, connect = True):
        if self.level <= 1:
            islot = InputSlot(self.name ,self, stype = type(self.stype))
        else:
            islot = MultiInputSlot(self.name,self, stype = type(self.stype), level = self.level - 1)
        self._subSlots.append(islot)
        islot.name = self.name
        index = len(self)-1
        if connect:
          self._connectSubSlot(index, notify = notify)
        if self._value is not None:
          islot.setValue(self._value)
        return islot


    def _insertNew(self, index, notify = True, connect = True):
        if self.level == 1:
            islot = InputSlot(self.name,self, stype = type(self.stype))
        else:
            islot = MultiInputSlot(self.name,self, stype = type(self.stype), level = self.level - 1)
        self._subSlots.insert(index,islot)
        islot.name = self.name
        if connect:
          self._connectSubSlot(index, notify = notify)
        if self._value is not None:
          islot.setValue(self._value)

        return islot
    
    
    def _checkNotifyConnectAll(self, notify = True):
        # check wether all slots are connected and eventuall notify operator            
        if self.operator:
            allConnected = True
            for slot in self.operator.inputs.values():
                if slot._optional is False and not slot.connected():
                    allConnected = False
                    break
            if allConnected:
              self.operator._setupOutputs()
        
    
    def connected(self):
        answer = True
        if self._value is None and self.partner is None:
            answer = False
        if answer is False and len(self._subSlots) > 0:
            answer = True
            for s in self._subSlots:
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

    def _setupOutputs(self):
      self._changed()

    def _changed(self):
      if self.partner is not None:
        self.meta = self.partner.meta.copy()
        if self.partner.level == self.level:
          self.resize(len(self.partner))
      self._checkNotifyConnectAll()
      for c in self._clones:
        c._changed()
        
    def connect(self,partner, notify = True):
        if partner is None:
            self.disconnect()
            return
        
        if not isinstance(partner,(OutputSlot,MultiOutputSlot,Operator,InputSlot, MultiInputSlot)):
            self.setValue(partner)
            return
          
        if self.partner == partner and partner.level == self.level:
            return
        
        if partner is not None:
            if partner.level == self.level:
                if self.partner is not None:
                    self.partner.disconnectSlot(self)
                self.partner = partner
                self.meta = self.partner.meta.copy()
                
                if len(self) != len(partner):
                    self.resize(len(partner))
                    
                if not isinstance(partner, (InputSlot, MultiInputSlot)):
                  partner._connect(self)
                  for i in range(len(self.partner)):
                      p = self.partner[i]
                      self.partner[i]._connect(self[i])
                else:
                  partner._registerClone(self)
                  for i in range(len(self.partner)):
                      p = self.partner[i]
                      self[i].connect(self.partner[i])

                # call slot type connect function
                self.stype.connect(partner)
               
                self._changed()
                
            elif partner.level < self.level:
                self.partner = partner
                self.meta = self.partner.meta.copy()
                for i, slot in enumerate(self._subSlots):                
                    slot.connect(partner)
                self._changed()

            elif partner.level > self.level:
                if not isinstance(partner, (InputSlot, MultiInputSlot)):
                  partner.disconnectSlot(self)
                if lazyflow.verboseWrapping:
                  print "-> Wrapping operator because own level is", self.level, "partner level is", partner.level
                if isinstance(self.operator,(OperatorWrapper, Operator)):
                    newop = OperatorWrapper(self.operator)
                    partner._connect(newop.inputs[self.name])
                else:
                    raise RuntimeError("Trying to connect a higher order slot to a subslot - NOT ALLOWED")

    def disconnect(self):
        for slot in self._subSlots:
            slot.disconnect()
        if self.partner is not None:
            if not isinstance(self.partner, (InputSlot, MultiInputSlot)):
              self.partner.disconnectSlot(self)
            else:
              self.partner._unregisterClone(self)
            self._subSlots = []
            self.partner = None
        self.operator.notifyDisconnect(self)
    
    def removeSlot(self, index, notify = True, event = None):
        slot = index
        if type(index) is int:
            slot = self[index]
        self._removeInputSlot(slot, notify, event = event)
    
    def _removeInputSlot(self, inputSlot, notify = True, event = None):
        try:
            index = self._subSlots.index(inputSlot)
        except:
          pass
        self._subSlots.remove(inputSlot)
        if notify:
          self._checkNotifyConnectAll()
        for c in self._clones:
          c._changed()

        

    def setDirty(self, roi):
        assert self.operator is not None, "Slot %s cannot be set dirty, slot not belonging to any actual operator instance" % self.name
        self.operator.propagateDirty(self, roi)

    def propagateDirty(self, slot, roi):
        print "MultiInput %r of %r is dirty" % (self.name, self.operator)
        index = self._subSlots.index(slot)
        self.operator.notifySubSlotDirty((self,slot),(index,),roi)
    
    def notifySubSlotDirty(self, slots, indexes, roi):
        index = self._subSlots.index(slots[0])
        self.operator.notifySubSlotDirty((self,)+slots,(index,) + indexes,roi)
   
    @property
    def graph(self):
        return self.operator.graph

    def dumpToH5G(self, h5g, patchBoard):
        h5g.dumpSubObjects({
            "name" : self.name,
            "level" : self.level,
            "operator" : self.operator,
            "partner" : self.partner,
            "stype" : self.stype,
            "_subSlots": self._subSlots
            
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
            "_subSlots": "_subSlots"
            
        },patchBoard)
            
        return s


class MultiOutputSlot(Slot):
    """
    The MultiOutputSlot is a multidimensional OutputSlot.
    
    it contains nested lists of OutputSlot objects.
    """
    
    
    def __init__(self, name = "", operator = None, stype = ArrayLike, rtype=rtype.SubRegion, level = 1, optional = False, value = None):
        self._type = "output"
        super(MultiOutputSlot, self).__init__(name = name, operator = operator, stype = stype, rtype=rtype, level = level)
        self._metaParent = operator
        self.partners = []
    
   
    def append(self, subSlot, event = None):
        subSlot.operator = self
        self._subSlots.append(subSlot)
        index = len(self._subSlots) - 1
        self.meta._dirty = True
    
    def _insertNew(self,index, event = None):
        oslot = OutputSlot(self.name,self,stype=type(self.stype))
        self.insert(index,oslot, event = event)
        self.meta._dirty = True


    def insert(self, index, outputSlot, event = None):
        outputSlot.operator = self
        self._subSlots.insert(index,outputSlot)
        self.meta._dirty = True
        
    def remove(self, outputSlot, event = None):
        index = self._subSlots.index(outputSlot)
        self.pop(index, event = event)
        self.meta._dirty = True
    
    def pop(self, index = -1, event = None):
        oslot = self._subSlots[index]
        oslot.disconnect()
        oslot = self._subSlots.pop(index)
        self.meta._dirty = True

    def _changed(self):
      if self.meta._dirty:
        self.meta._dirty = False
        for p in self.partners:
          p._changed()

      for o in self._subSlots:
        o._changed()

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
        if len(self) != size:
          self.meta._dirty = True
        while len(self) < size:
            if self.level == 1:
                slot = OutputSlot(self.name,self, stype = type(self.stype))
            else:
                slot = MultiOutputSlot(self.name,self, stype = type(self.stype), level = self.level - 1)
            index = len(self)
            self._subSlots.append(slot)

        
        while len(self) > size:
            self.pop()

    def execute(self,slot,roi,result):
        index = self._subSlots.index(slot)
        #TODO: remove this special case  once all operators are ported
        key = roiToSlice(roi.start,roi.stop)
        return self.operator.getSubOutSlot((self, slot,),(index,),key, result)


    def getOutSlot(self, slot, key, result):
        index = self._subSlots.index(slot)
        return self.operator.getSubOutSlot((self, slot,),(index,),key, result)

    def getSubOutSlot(self, slots, indexes, key, result):
        try:
            index = self._subSlots.index(slots[0])
        except:
            raise RuntimeError("MultiOutputSlot.getSubOutSlot: name=%r, operator.name=%r, slots=%r" % \
                               (self.name, self.operator.name, self.operator, slots))
        return self.operator.getSubOutSlot((self,) + slots, (index,) + indexes, key, result)
    
    def setDirty(self, roi):
        return
    
    @property
    def graph(self):
        return self.operator.graph


    def dumpToH5G(self, h5g, patchBoard):
        h5g.dumpSubObjects({
            "name" : self.name,
            "level" : self.level,
            "operator" : self.operator,
            "partners" : self.partners,
            "stype" : self.stype,
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


class InputDict(dict):
    
    def __init__(self, operator):
      self.operator = operator


    def __setitem__(self, key, value):
        assert isinstance(value, (InputSlot, MultiInputSlot)), "ERROR: all elements of .inputs must be of type InputSlot or MultiInputSlot, you provided %r !" % (value,)
        return dict.__setitem__(self, key, value)
    def __getitem__(self, key):
        if self.has_key(key):
          return dict.__getitem__(self,key)
        elif hasattr(self.operator,key):
          return getattr(self.operator, key)
        else:
          raise Exception("Operator %s (class: %s) has no input slot named '%s'. available input slots are: %r" %(self.operator.name, self.operator.__class__, key, self.keys()))

    @classmethod
    def reconstructFromH5G(cls, h5g, patchBoard):
        temp = InputDict()
        patchBoard[h5g.attrs["id"]] = temp
        for i,g in h5g.items():
            temp[str(i)] = g.reconstructObject(patchBoard)
        return temp



class OutputDict(dict):
    
    def __init__(self, operator):
      self.operator = operator


    def __setitem__(self, key, value):
        assert isinstance(value, (OutputSlot, MultiOutputSlot)), "ERROR: all elements of .outputs must be of type OutputSlot or MultiOutputSlot, you provided %r !" % (value,)
        return dict.__setitem__(self, key, value)
    def __getitem__(self, key):
        if self.has_key(key):
          return dict.__getitem__(self,key)
        elif hasattr(self.operator,key):
          return getattr(self.operator, key)
        else:
          raise Exception("Operator %s (class: %s) has no output slot named '%s'. available output slots are: %r" %(self.operator.name, self.operator.__class__, key, self.keys()))

    @classmethod
    def reconstructFromH5G(cls, h5g, patchBoard):
        temp = OutputDict()
        patchBoard[h5g.attrs["id"]] = temp
        for i,g in h5g.items():
            temp[str(i)] = g.reconstructObject(patchBoard)
        return temp




class OperatorMetaClass(type):

    def __new__(cls,name,bases,classDict):
        cls = type.__new__(cls,name,bases,classDict)
        
        setattr(cls,"inputSlots", list(cls.inputSlots))
        setattr(cls,"outputSlots", list(cls.outputSlots))
        
        for k,v in cls.__dict__.items():
          if isinstance(v,(InputSlot, MultiInputSlot)):
            v.name = k
            cls.inputSlots.append(v)

          if isinstance(v,(OutputSlot, MultiOutputSlot)):
            v.name = k
            cls.outputSlots.append(v)
        return cls

    def __call__(cls,*args,**kwargs):
      # type.__call__ calls instance.__init__ internally
      instance = type.__call__(cls,*args,**kwargs)
      instance._after_init()
      return instance



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
    
    __metaclass__ = OperatorMetaClass

    def __new__( cls, *args, **kwargs ):
        ##
        # before __init__
        ##
        obj = super(Operator, cls).__new__(cls)
        obj.graph = None
        obj.operator = None
        obj.inputs = InputDict(obj)
        obj.outputs = OutputDict(obj)
        obj.register = True

        ##
        # wrap old api
        ##
        if hasattr(obj, "getOutSlot"):
            def getOutSlot_wrapper( self, slot, roi, result ):
                pslice = roiToSlice(roi.start,roi.stop)
                warn_deprecated( "getOutSlot() is superseded by execute()" )
                return self.getOutSlot(slot,pslice,result)
            obj.execute = types.MethodType(getOutSlot_wrapper, obj)
        return obj

    def __init__( self, parent = None, graph = None, register = True ):
        assert parent != None or graph != None
        # preserve compatability with old operators
        # that give the graph as first argument to 
        # operators they instantiate
        if parent is not None:
          if isinstance(parent, Graph):
            self.graph = parent
            self._parent = None
          else:
            self._parent = parent
            self.graph = self._parent.graph
        if graph is not None:
          if isinstance(graph, Graph):
            self.graph = Graph
            self._parent = None
          elif not  isinstance(graph, bool):
            self._parent = graph
            self.graph = self._parent.graph

        self._instantiate_slots()
        

    # continue initialization, when user overrides __init__
    def _after_init(self):
        #provide simple default name for lazy users
        if self.name == "": 
            self.name = type(self).__name__
        assert self.graph is not None, "Operator %r: self.graph is None, the parent  (%r) given to the operator must have a valid .graph attribute! " % (self, self._parent)
        # check for slot uniqueness
        temp = {}
        for i in self.inputSlots:
          if temp.has_key(i.name):
            raise Exception("ERROR: Operator %s has multiple slots with name %s, please make sure that all input and output slot names are unique" % (self.name, i.name))
            sys.exit(1)
          temp[i.name] = True

        for i in self.outputSlots:
          if temp.has_key(i.name):
            raise Exception("ERROR: Operator %s has multiple slots with name %s, please make sure that all input and output slot names are unique" % (self.name, i.name))
            sys.exit(1)
          temp[i.name] = True

        self._instantiate_slots()

        self._setDefaultInputValues()

        if len(self.inputs.keys()) == 0:
          self._setupOutputs()



    def _instantiate_slots(self):
        # replicate input slot connections
        # defined for the operator for the instance
        for i in self.inputSlots:
            if not self.inputs.has_key(i.name):
              ii = i.getInstance(self)
              ii.connect(i.partner)
              self.inputs[i.name] = ii

        for k,v in self.inputs.items():
          self.__dict__[v.name] = v
        
        # relicate output slots
        # defined for the operator for the instance 
        for o in self.outputSlots:
            if not self.outputs.has_key(o.name):
              oo = o.getInstance(self)
              self.outputs[o.name] = oo         

        for k,v in self.outputs.items():
          self.__dict__[v.name] = v



    def connected(self):
      allConnected = True
      for slot in self.inputs.values():
          if slot._optional is False and slot.connected() is False:
              allConnected = False
      if allConnected:
        pass

    def _setDefaultInputValues(self):
      for i in self.inputs.values():
        if i._defaultValue is not None:
          i.setValue(i._defaultValue)
         
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
    def propagateDirty(self, inputSlot, roi):
        # default implementation calls old api for backwardcompatability
        if hasattr(roi,"toSlice"):
          self.notifyDirty(inputSlot,roi.toSlice())
        else:
          print "propagateDirty: roi=", roi
          raise TypeError(".propagatedirty of Operator %r is not implemented !" % (self)) 

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

    def notifyDisconnect(self, slot):
        pass

    def _notifyConnect(self, inputSlot):
        pass#self.notifyConnect(inputSlot)
    
    def _notifyConnectAll(self):
        pass

    def connect(self, **kwargs):
        for k in kwargs:
          if k in self.inputs.keys():
            self.inputs[k].connect(kwargs[k])
          else:
            print "ERROR, connect(): operator %s has no slot named %s" % (self.name, k)
            print "                  available inputSlots are: ", self.inputs.keys()
            assert(1==2)


    def _setupOutputs(self):
      self.setupOutputs()

      #notify outputs of probably changed meta informatio
      for k,v in self.outputs.items():
        v._changed()

    def setupOutputs(self):
      """
      This method is called when all input slots of an operator are
      successfully connected, a successful connection is also established
      if the input slot is not connected to another slot, but has
      a default value defined.

      In this method the operator developer should stup 
      the .meta information of the outputslots.

      The default implementation emulates the old api behaviour.
      """
      # emulate old behaviour
      self.notifyConnectAll()



    """
    OBSOLETE API
    This method is called opon connection of all inputslots of
    an operator.
    
    The operator should setup the output all outputslots accordingly.
    this includes setting their shape and axistags properties.
    """
    def notifyConnectAll(self):
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
    def execute(self, slot, roi, result):
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
    
    def __init__(self, operator, register = False):
        self.inputs = InputDict(self)
        self.outputs = OutputDict(self)
        self.operator = operator
        self._eventCounter = 0
        self._processedEvents = {}       
        self._originalGraph = operator.graph
        self.graph = operator.graph
        self._parent = operator._parent
        self._connecting = False
        
        if operator is not None:
            self.name = operator.name
            self._originalGraph = operator.graph
            self.graph = operator.graph

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
                self._inputSlots.append(islot.getInstance(self,level = level))
    
            # replicate output slot definitions
            for oslot in self.outputSlots:
                level = oslot.level + 1
                self._outputSlots.append(oslot.getInstance(self, level = level))
    
                    
            # replicate input slots for the instance
            for islot in self.operator.inputs.values():
                level = islot.level + 1
                ii = islot.getInstance(self,level)
                self.inputs[islot.name] = ii
                setattr(self,islot.name,ii)
                op = self.operator
                while isinstance(op.operator, (Operator, MultiInputSlot)):
                    op = op.operator
                op.inputs[islot.name] = ii
                setattr(op,islot.name,ii)
            
            # replicate output slots for the instance
            for oslot in self.operator.outputs.values():
                level = oslot.level + 1
                oo = oslot.getInstance(self,level)
                self.outputs[oslot.name] = oo
                setattr(self,oslot.name,oo)
                op = self.operator
                while isinstance(op.operator, (Operator, MultiOutputSlot)):
                    op = op.operator
                op.outputs[oslot.name] = oo
                setattr(op,oslot.name,oo)

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
                    
            self._setupOutputs()
    
    
            #connect output slots
            for oslot in self.origOutputs.values():
                oo = self.outputs[oslot.name]            
                partners = copy.copy(oslot.partners)
                oslot.disconnect()
                for p in partners:         
                    oo._connect(p)
            
        self._setDefaultInputValues()

    def _getOriginalOperator(self):
        op = self.operator
        while isinstance(op, OperatorWrapper):
            op = self.operator
        return op
                    
    def _testRestoreOriginalOperator(self):
        #TODO: only restore to the level that is needed, not to the most upper one !
        for iname, islot in self.inputs.items():
            if islot.partner is not None:
                if islot.partner.level > self.origInputs[iname].level:
                    return
                
        if lazyflow.verboseWrapping:
            print "Restoring original operator [self=%r] named '%s'" % (self, self.name)

        op = self
        while isinstance(op.operator, (OperatorWrapper)):
            op = op.operator

        op.operator.outputs = op.origOutputs
        for o in op.operator.outputs.values():
          setattr(op.operator, o.name, o)
        
        
        op.operator.inputs = op.origInputs
        for i in op.operator.inputs.values():
          setattr(op.operator, i.name, i)

        op = op.operator
         

        # restore current connections
        for k, islot in self.inputs.items():
            if islot.partner is not None:
                op.inputs[k].connect(islot.partner)
            elif islot._value is not None:
                op.inputs[k].setValue(islot._value)

        for k, oslot in self.outputs.items():
            for p in oslot.partners:
                op.outputs[k]._connect(p)
    
    def notifyDisconnect(self, slot):
       self._testRestoreOriginalOperator() 
                    
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
            opcopy = self.operator.__class__(parent = self)
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

    def _setupOutputs(self):
      if self._connecting is True:
        return
      self._connecting = True
      inputSlot = self.inputs.values()[0]
      maxLen = self._ensureInputSize()
      for inputSlot in self.inputs.values():
        for i in range(len(inputSlot)):
            islot = inputSlot[i]
            if islot.partner is not None:
                self.innerOperators[i].inputs[inputSlot.name].connect(islot.partner)
            elif islot._value is not None:
                self.innerOperators[i].inputs[inputSlot.name].setValue(islot._value)
                        
      self._ensureOutputSize([],[], maxLen)
      self._connectInnerOutputs()
      self.setupOutputs()
        
      for k,mslot in self.outputs.items():
        assert len(mslot) == len(self.innerOperators) == maxLen, "%d, %d" % (len(mslot), len(self.innerOperators))        


      for o in self.outputs.values():
        o._changed()

      self._connecting = False

    
    def _ensureOutputSize(self,slots,indexes,size,event = None):
        oldSize = len(self.innerOperators)

        while len(self.innerOperators) < size:
          op = self._createInnerOperator()
          self.innerOperators.append(op)

        while len(self.innerOperators) > size:
          op = self.innerOperators.pop()
  

        for k,oslot in self.outputs.items():
          oslot.resize(size,event = event)

                
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
        
   
                        
class Worker(Thread):
    def __init__(self, graph):
        Thread.__init__(self)
        self.graph = graph
        self.working = False
        self.daemon = True # kill automatically on application exit!
        self.finishedRequestGreenlets = deque()#PriorityQueue()
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
                self.graph.freeWorkers.add(self)
            self.workAvailableEvent.wait()#(0.2)
            try:
                self.graph.freeWorkers.remove(self)
            except:
                pass
            self.workAvailableEvent.clear()
            
            didSomething = True

            while didSomething:
                didSomething = False
                while len(self.finishedRequestGreenlets) > 0:
                    prioFinReq, req, gr = self.finishedRequestGreenlets.pop()#get(block = False)
                    gr.currentRequest = req                 
                    if req.canceled is False:
                        gr.switch()
                    del gr
                    didSomething = True
                        
                
                task = None
                try:
                    prioLastReq,task = self.graph.tasks.get(block = False)#timeout = 1.0)
                except Empty:
                    prioLastReq = 0
                    pass                
                if task is not None:
                    didSomething = True
                    reqObject = task
                    if reqObject.canceled is False:
                        gr = CustomGreenlet(reqObject._execute)
                        gr.lastRequest = None
                        gr.currentRequest = reqObject
                        gr.thread = self
                        gr.switch( gr)
                        del gr
                        
                if didSomething is False: # only start a new request if nothing else was done
                    task = None
                    try:
                        pr,task = self.graph.newTasks.get(block = False)#timeout = 1.0)
                    except Empty:
                        pass               
                    if task is not None:
                        didSomething = True
                        reqObject = task
                        if reqObject.canceled is False:
                            gr = CustomGreenlet(reqObject._execute)
                            gr.thread = self
                            gr.lastRequest = None
                            gr.currentRequest = reqObject
                            gr.switch( gr)
                            del gr
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
        self.freeWorkers = set()
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
        self.freeWorkers = set()
        self.tasks = PriorityQueue()
        for i in xrange(self.numThreads):
            w = Worker(self)
            self.workers.append(w)
            w.start()
            self.freeWorkers.add(w)        
    
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
                    w = self.freeWorkers.pop()
                    w.signalWorkAvailable()
                    time.sleep(0)
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

          print "  Waiting for workers..."          
          for w in self.workers:
            w.signalWorkAvailable()
          while len(self.workers) > len(self.freeWorkers):
              time.sleep(0.1)
              print "    #workers = %d, #free workers = %d" % (len(self.workers),len(self.freeWorkers))
          time.sleep(0.1)
          while len(self.workers) > len(self.freeWorkers):
              time.sleep(0.1)
          print "  ok"
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
 
