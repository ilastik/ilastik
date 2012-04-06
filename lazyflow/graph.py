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
import traceback
import psutil

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
import weakref
from request import Request
import rtype
from roi import sliceToRoi, roiToSlice
from lazyflow.stype import ArrayLike
from lazyflow import stype




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


class ValueRequest(object):
  """
  Pseudo request that behaves like a Request.Request object

  this object is used to prevent the heavy construction of complete Request
  objects in simple cases where they are not needed.
  """
  def __init__(self, value):
    self.result = value

  def wait(self):
    return self.result

  def notify(self, callback, *args, **kwargs):
    callback(*args, **kwargs)

  def onCancel(self, callback, *args, **kwargs):
    pass

  def allocate(self, priority = 0):
    return self

  def writeInto(self, destination):
    if isinstance(destination, numpy.ndarray):
      destination[:] = self.result
    else:
      destination[:] = self.result
    return self

  def getResult(self):
    return self.result


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

    def _requestFunctionWrapper(self, roi, destination):
      if destination is None:
        destination = self.stype.allocateDestination(roi)
      tres = self.operator.execute(self, roi, destination)
      return destination

    def get( self, roi, destination = None ):
      if self._value is not None:
        # this handles the case of an inputslot
        # having a ._value
        # --> construct cheaper request object for this case
        result = self.stype.writeIntoDestination(destination, self._value, roi)
        return ValueRequest(result)
      elif self.partner is not None:
        # this handles the case of an inputslot
        # --> just relay the request
        return self.partner.get(roi, destination)
      else:
        # normal case
        # --> construct heavy request object..
        return Request(self._requestFunctionWrapper,roi = roi,destination = destination)        


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

    def __setattr__(self, name, value):
      """
      This method safeguards that operators do not overwrite slot names with
      custom instance attributes.
      """
      if self.__dict__.has_key("inputs") and self.__dict__.has_key("outputs"):
        if self.inputs.has_key(name) or self.outputs.has_key(name):
          assert isinstance(value, Slot), "ERROR: trying to set attribute %r of operator %r to value %r, which is not of type Slot !" % (name, self, value)
      object.__setattr__(self,name,value)
      

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
        
   
                        
class Graph(object):
  pass

  def stopGraph(self):
    pass

  def resumeGraph(self):
    pass

  def _registerCache(self, cache):
    pass

  def _notifyMemoryHit(self, *args, **kwargs):
    pass

  def _notifyMemoryAllocation(self, *args, **kwargs):
    pass

  def _notifyFreeMemory(self, *args, **kwargs):
    pass


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
 
