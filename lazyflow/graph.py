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


import numpy
import vigra
import sys
import copy
import psutil
import os
import time
import gc
import ConfigParser
import string

from h5dumprestore import instanceClassToString, stringToClass
from helpers import itersubclasses
from roi import sliceToRoi, roiToSlice
from collections import deque
from Queue import Queue, LifoQueue, Empty
from threading import Thread, Event, current_thread, Lock
import greenlet
import weakref


greenlet.GREENLET_USE_GC # use garbage collection


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


class GetItemWriterObject(object):
    """
    Enables the syntax:

    InputSlot[:,:].writeInto(array)
    InputSlot[:,:].allocate()
    
    for requesting data from an input or output slot of an operator.
    
    An instance of this class is returned by a call to a __getitem__ (i.e. [key])
    method call of any InputSlot or OutputSlot.
    """
    
    __slots__ = ["_key", "_slot"]
    
    def __init__(self, slot, key):
        start, stop = sliceToRoi(key, slot.shape)
        key = roiToSlice(start,stop)        
        self._key = key
        self._slot = slot
    
    def writeInto(self, destination):
        """
        the writeInto method ensures that the data
        that is requested from an InputSlot or OutputSlot is written
        into the specified numpy.ndarray
        
        of course the destination numpy.ndarray must have
        the same size/shape/dimension as the slot will
        return in reponse to the requested key
        """
        return self._slot.fireRequest(self._key, destination)     
    
    def allocate(self):
        """
        if the user does not want lazyflow to write calculation
        results into a specific numpy array he can use
        the .allocate() call.
        
        a destination array of required size,shape,dtype will
        be constructed in which the results will be written.
        """
        destination, key = self._slot.allocateStorage(self._key)
        self._key = key
        return self.writeInto(destination)
    
    def __call__(self):
        #TODO: remove this convenience function when
        #      everything is ported ?
        return self.allocate()


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
        
    __slots__ = ["func", "slot","lock", "requestLevel", "greenlet", "event", "thread", "key", "destination", "closure",  "kwargs"]

    def __init__(self, slot, graph, partner, key, destination):
        self.key = key
        self.greenlet = None
        self.destination = destination
        self.closure = None
        self.event = Event()
        self.lock = Lock()
        self.thread = current_thread()
        self.slot = slot
        self.func = None
        self.kwargs = {}
        
        if slot is None or slot.partner is not None:
            if hasattr(self.thread, "currentRequestLevel"): #TODO: use more self explaining test
                self.requestLevel = self.thread.currentRequestLevel + 1
            else:
                self.requestLevel = 1
                self.thread = graph.workers[0]
            
            self.func = partner.fireRequest
            
            graph.putTask(self)

    
    def wait(self, timeout = 0):
        """
        calling .wait() on an RequestObject is a blocking
        call that will only return once the results
        of a requested Slot are calculated and stored in
        the  result area.
        """
        if self.slot is None or self.slot.partner is not None:
            self.lock.acquire()
            if not self.event.isSet():
                # --> wait until results are ready
                if greenlet.getcurrent().parent != None: #TODO: use other test as in __init__  
                    self.greenlet = greenlet.getcurrent()
                    self.lock.release()
                    self.greenlet.parent.switch(None)
                    self.greenlet = None
                else:
                    self.lock.release()
                    # loop to allow ctrl-c signal !
                    if timeout == 0:
                        while not self.event.isSet():
                            self.event.wait(timeout = 0.25) #in seconds
                    else:
                        self.event.wait(timeout = timeout) #in seconds
            else:
                self.lock.release()
        else:
            if isinstance(self.slot._value, numpy.ndarray):
                self.destination[:] = self.slot._value[self.key]
            else:
                self.destination[:] = self.slot._value
        return self.destination   
         
    def notify(self, closure, **kwargs): 
        """
        calling .notify(someFunction) on an RequestObject is a NON-blocking
        call that will return immediately.
        once the results are calculated and stored in the result
        are, the provided someFunction will be called by lazyflow.
        """
        self.kwargs = kwargs
        
        if isinstance(self.thread, Worker):
            self.lock.acquire()
            self.closure = closure
            self.lock.release()
        else:
            print "GetItemRequestObject: notify possible only from within worker thread -> waiting for result instead..."
            result = self.wait()
            closure(result = result, **self.kwargs)
            
    def __call__(self):
        #TODO: remove this convenience function when
        #      everything is ported ?
        return self.wait()

class InputSlot(object):
    """
    The base class for input slots, it provides methods
    to connect the InputSlot to an OutputSlot of another
    operator (i.e. .connect(partner) call) or allows 
    to directly provide a value as input (i.e. .setValue(value) call)
    """
    
    def __init__(self, name, operator = None, stype = "ndarray"):
        self.name = name
        self.operator = operator
        self.partner = None
        self.level = 0
        self._value = None
        self.stype = stype

    def setValue(self, value):
        """
        This methods allows to directly provide an array
        or other entitiy as input the the InputSlot instead
        of connecting it to a partner OutputSlot.
        """
        assert self.partner == None, "InputSlot %s (%r): Cannot dot setValue, because it is connected !" %(self.name, self)
        self._value = value
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
        if self._value is None and self.partner is None:
            answer = False
        return answer


    def connectAdd(self, partner):
        if isinstance(self.operator,(OperatorWrapper, Operator)):
            newop = OperatorWrapper(self.operator)
            newop.inputs[self.name].connectAdd(partner)
        else:
            raise RuntimeError("InputSlot: connectAdd called for a inner slot, NOT ALLOWED")        
    
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
                self._checkNotifyConnect()
    
    def _checkNotifyConnect(self):
        if self.operator is not None:
            self._checkNotifyConnectAll()
            
    def _checkNotifyConnectAll(self):
        """
        notify operator of connection
        the operator may do a compatibility
        check that involves
        more then one slot
        """
        if self.operator is not None:
            self.operator.notifyConnect(self)
            # check wether all slots are connected and notify operator            
            if isinstance(self.operator,Operator):
                allConnected = True
                for slot in self.operator.inputs.values():
                    if slot.connected() is False:
                        allConnected = False
                        break
                if allConnected:
                    self.operator.notifyConnectAll()
                
        else:
            print "BBBBBBBBBBBBBBBBBBBBBBB operator is NONE", self.name


       
    def disconnect(self):
        """
        Disconnect a InputSlot from its partner
        """
        #TODO: also reset ._value ??
        if self.partner is not None:
            self.partner.disconnectSlot(self)
        self.partner = None
    
    #TODO RENAME? createInstance
    # def __copy__ ?, clone ?
    def getInstance(self, operator):
        s = InputSlot(self.name, operator, stype = self.stype)
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
        return GetItemWriterObject(self, key)
        
    def fireRequest(self, key, destination):
        assert self.partner is not None or self._value is not None, "cannot do __getitem__ on Slot %s, of %r Not Connected!" % (self.name, self.operator)
        #print "GUGA", self.name, self.operator.name, self.operator, key
                                        
        reqObject = GetItemRequestObject(self, self.graph, self.partner, key, destination)
            
        return reqObject

    def allocateStorage(self, key):
        start, stop = sliceToRoi(key, self.shape)
        storage = numpy.ndarray(stop - start, dtype=self.dtype)
        key = roiToSlice(start,stop) #we need a fully specified key e.g. not [:] but [0:10,0:17] !!
        return storage, key
            
    def __setitem__(self, key, value):
        assert self.operator is not None, "cannot do __setitem__ on Slot '%s' -> no operator !!"
        if self._value is not None:
            self._value[key] = value
            self.setDirty(key) # only propagate the dirty key at the very beginning of the chain
        self.operator.setInSlot(self,key,value)
        
    @property
    def graph(self):
        return self.operator.graph

    @property
    def dtype(self):
        if self.partner is not None:
            return self.partner.dtype
        elif self._value is not None:
            if isinstance(self._value, numpy.ndarray):
                return self._value.dtype
            else:
                return object
            
    @property
    def shape(self):
        if self.partner is not None:
            return self.partner.shape
        elif self._value is not None:
            if isinstance(self._value, numpy.ndarray):
                return self._value.shape
            else:
                return (1,)

    @property
    def axistags(self):
        if self.partner is not None:
            return self.partner.axistags
        elif self._value is not None:
            if isinstance(self._value, vigra.VigraArray):
                return copy.copy(self._value.axistags)
            else:
                return vigra.VigraArray.defaultAxistags(len(self.shape))

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
    def __init__(self, name, operator = None, stype = "ndarray"):
        self.name = name
        self._metaParent = operator
        self.level = 0
        self.operator = operator
        if not hasattr(self, "_dtype"):
            self._dtype = None
        if not hasattr(self, "_secretshape"):
            self._secretshape = None
        if not hasattr(self, "_axistags"):
            self._axistags = None
        self.partners = []
        self.stype = stype
    
    @property
    def _shape(self):
        return self._secretshape
        
    @_shape.setter
    def _shape(self, value):
        if value is not None:
            if value != self._secretshape:
                self._secretshape = value
                for p in self.partners:
                    p._checkNotifyConnectAll()
            else:
                self.setDirty(slice(None,None,None)) #set everything to dirty! BEWARE; DANGER;
        else:
            self._secretshape = None
            for p in self.partners:
                p._checkNotifyConnectAll()
    
    
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

    #FIXME __copy__ ?
    def getInstance(self, operator):
        s = OutputSlot(self.name, operator, stype = self.stype)
        s._shape = self._shape
        s._dtype = self._dtype
        s._axistags = self._axistags
        return s

    def allocateStorage(self, key):
        start, stop = sliceToRoi(key, self.shape)
        storage = numpy.ndarray(stop - start, dtype=self.dtype)
        key = roiToSlice(start,stop)
        return storage, key

    def __getitem__(self, key):
        return GetItemWriterObject(self,key)

    def fireRequest(self, key, destination):
        assert self.operator is not None, "cannot do __getitem__ on Slot %s, of %r -> now operator !!" % (self.name,self.operator) 
        
        start, stop = sliceToRoi(key, self.shape)
        
        assert numpy.min(start) >= 0, "Somebody is requesting shit from slot %s of operator %s (%r)" %(self.name, self.operator.name, self.operator)
        assert (stop <= numpy.array(self.shape)).all(), "Somebody is requesting shit from slot %s of operator %s (%r) :  start: %r, stop %r, shape %r" %(self.name, self.operator.name, self.operator, start, stop, self.shape)
        
        gr = greenlet.getcurrent()
        
        if gr.parent == None: #FIXME: this is a bad test for a end user call ?!
            reqObject = GetItemRequestObject(None, self.graph, self, key, destination)
            return reqObject
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


    def dumpToH5G(self, h5g, patchBoard):
        h5g.dumpSubObjects({
            "name" : self.name,
            "level" : self.level,
            "operator" : self.operator,
            "shape" : self._shape,
            "axistags" : self._axistags,
            "dtype" : self._dtype,
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
            "shape" : "_secretshape",
            "axistags" : "_axistags",
            "dtype" : "_dtype",
            "partners" : "partners",
            "stype" : "stype"
            
        },patchBoard)
            
        return s
        

class MultiInputSlot(object):
    """
    The MultiInputSlot is a multidimensional InputSlot.
    
    it contains nested lists of InputSlot objects.
    """
    
    def __init__(self, name, operator = None, stype = "ndarray", level = 1):
        self.name = name
        self.operator = operator
        self.partner = None
        self.inputSlots = []
        self.level = level
        self.stype = stype
        self._value = None
    
    @property
    def value(self):
        return self._value

    def setValue(self, value):
        self._value = value
        for i,s in enumerate(self.inputSlots):
            s.setValue(self._value)
        self._checkNotifyConnectAll()
    
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
            islot = InputSlot(self.name ,self, stype = self.stype)
        else:
            islot = MultiInputSlot(self.name,self, stype = self.stype, level = self.level - 1)
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
            islot = InputSlot(self.name,self, self.stype)
        else:
            islot = MultiInputSlot(self.name,self, stype = self.stype, level = self.level - 1)
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
        if isinstance(self.operator, Operator):
            allConnected = True
            for slot in self.operator.inputs.values():
                if slot.partner is None and slot._value is None:
                    allConnected = False
                    break
            if allConnected:
                self.operator.notifyConnectAll()
        
    
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

    def connected(self):
        answer = True
        if self._value is None and self.partner is None:
            answer = False
        if answer is False:
            answer = True
            for s in self.inputSlots:
                if s.connected() is False:
                    answer = False
                    break
        
        return answer


        
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
                print "MultiInputSlot connecdt", self.operator, self.operator.name, len(self), partner.operator, partner.operator.name, len(partner)
                if len(self) != len(partner):
                    self.resize(len(partner))
                for i,p in enumerate(self.partner):
                    self.partner[i]._connect(self[i])

                self.operator.notifyConnect(self)
                self._checkNotifyConnectAll()
                
            elif partner.level < self.level:
                #if self.partner is not None:
                #    self.partner.disconnectSlot(self)                
                self.partner = partner
                for i, slot in enumerate(self):                
                    slot.connect(partner)
                    if self.operator is not None:
                        self.operator.notifySubConnect((self,slot), (i,))
                self._checkNotifyConnectAll()
            elif partner.level > self.level:
                #if self.partner is not None:
                #    self.partner.disconnectSlot(self)
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
        self.operator.notifySubConnect((self,slot), (index,))
    
    def notifySubConnect(self, slots, indexes):        
        index = self.inputSlots.index(slots[0])
        self.operator.notifySubConnect( (self,) + slots, (index,) +indexes)

    def notifyDisconnect(self, slot):
        index = self.inputSlots.index(slot)
        self.operator.notifySubDisconnect((self, slot), (index,))
    
    def notifySubDisconnect(self, slots, indexes):
        index = self.inputSlots.index(slots[0])
        self.operator.notifySubDisconnect((self,) + slots, (index,) + indexes)
        
    def notifySubSlotRemove(self, slots, indexes):
        if len(slots)>0:
            index = self.inputSlots.index(slots[0])
            indexes = (index,) + indexes
        self.operator.notifySubSlotRemove((self,) + slots, indexes)
        
    def disconnect(self):
        if self.partner is not None:
            self.partner.disconnectSlot(self)
            self.inputSlots = []
            self.partner = None
            self.operator.notifyDisconnect(self)
        for slot in self.inputSlots:
            slot.disconnect()
    
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
            self.notifySubSlotRemove((),(index,))

    def _partialSetItem(self, slot, key, value):
        index = self.inputSlots.index(slot)
        self.operator.multiSlotSetItem(self,slot,index, key,value)   
    
    #TODO RENAME? createInstance
    # def __copy__ ?
    def getInstance(self, operator):
        s = MultiInputSlot(self.name, operator, stype = self.stype, level = self.level)
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
            "stype" : self.stype,
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
    
    def __init__(self, name, operator = None, stype = "ndarray",level = 1):
        self.name = name
        self.operator = operator
        self._metaParent = operator
        self.partners = []
        self.outputSlots = []
        self.level = level
        self.stype = stype
    
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
                slot = OutputSlot(self.name,self, stype = self.stype)
            else:
                slot = MultiOutputSlot(self.name,self, stype = self.stype, level = self.level - 1)
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
        return self.operator.getSubOutSlot((self, slot,),(index,),key, result)

    def getSubOutSlot(self, slots, indexes, key, result):
        try:
            index = self.outputSlots.index(slots[0])
        except:
            #print self.name, self.operator.name, self.operator, slots
            raise
        return self.operator.getSubOutSlot((self,) + slots, (index,) + indexes, key, result)
    
    #TODO RENAME? createInstance
    # def __copy__ ?
    def getInstance(self, operator):
        s = MultiOutputSlot(self.name, operator, stype = self.stype, level = self.level)
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
         
    def getOriginalOperator(self):
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
    
    def __init__(self, operator):
        self.inputs = {}
        self.outputs = {}
        self.operator = operator
        if operator is not None:
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
                self._inputSlots.append(MultiInputSlot(islot.name, stype = islot.stype, level = level))
    
            # replicate output slot definitions
            for oslot in self.outputSlots:
                level = oslot.level + 1
                self._outputSlots.append(MultiOutputSlot(oslot.name, stype = oslot.stype, level = level))
    
                    
            # replicate input slots for the instance
            for islot in self.operator.inputs.values():
                level = islot.level + 1
                ii = MultiInputSlot(islot.name, self, stype = islot.stype, level = level)
                self.inputs[islot.name] = ii
                op = self.operator
                while isinstance(op.operator, (Operator, MultiInputSlot)):
                    op = op.operator
                op.inputs[islot.name] = ii
            
            # replicate output slots for the instance
            for oslot in self.operator.outputs.values():
                level = oslot.level + 1
                oo = MultiOutputSlot(oslot.name, self, stype = oslot.stype, level = level)
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

    def getOriginalOperator(self):
        op = self.operator
        while isinstance(op, OperatorWrapper):
            op = self.operator
        return op
                    
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
        self.testRestoreOriginalOperator()

    
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
                        
            mslot.resize(len(self.innerOperators))

        for index, innerOp in enumerate(self.innerOperators):
            for key,mslot in self.outputs.items():
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
                print "Wrapped Op", self.name, "connected", i
            elif islot._value is not None:
                self.innerOperators[i].inputs[inputSlot.name].setValue(islot._value)

                        
        self._connectInnerOutputs()
        
        for k,mslot in self.outputs.items():
            assert len(mslot) == len(self.innerOperators) == maxLen, "%d, %d" % (len(mslot), len(self.innerOperators))        

    
    def notifySubConnect(self, slots, indexes):
        #print "OperatorWrapper notifySubConnect", self.name, slots, indexes
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
        elif slots[1]._value is not None:
            if not isinstance(self.innerOperators[indexes[0]], OperatorWrapper):
                self.innerOperators[indexes[0]].inputs[slots[0].name].setValue(slots[1]._value)
            
        else:            
            if isinstance(self.innerOperators[indexes[0]], OperatorWrapper):
                
                if len(indexes)>1:
                    self.innerOperators[indexes[0]].notifySubConnect(slots[1:],indexes[1:])
                else:
                    self.innerOperators[indexes[0]].notifyConnect(slots[1],indexes[0])



                # check wether all slots are connected and notify operator            
                op = self.innerOperators[indexes[0]]
                allConnected = True
                for slot in op.inputs.values():
                    if slot.partner is None and slot._value is None:
                        allConnected = False
                        break
                if allConnected:
                    op.notifyConnectAll()
                    
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
        
    def notifySubDisconnect(self, slots, indexes):
        return
        maxLen = 0
        for name, islot in self.inputs.items():
            maxLen = max(len(islot), maxLen)
        
        while len(self.innerOperators) > maxLen:
            op = self.innerOperators[-1]
            self.removeInnerOperator(op)

    def notifySubSlotRemove(self, slots, indexes):
        print "OperatorWrapper notifySubSlotRemove", slots, indexes, self.name
        if len(indexes) == 1:
            op = self.innerOperators[indexes[0]]
            self.removeInnerOperator(op)
        else:
            self.innerOperators[indexes[0]].notifySubSlotRemove(slots[1:], indexes[1:])
    
    def getOutSlot(self, slot, key, result):
        #this should never be called !!!        
        pass


    def getSubOutSlot(self, slots, indexes, key, result):
        if len(indexes) == 1:
            #print "getSubOutSlot", indexes, slots
            return self.innerOperators[indexes[0]].getOutSlot(self.innerOperators[indexes[0]].outputs[slots[0].name], key, result)
        else:
            self.innerOperators[indexes[0]].getSubOutSlot(slots[1:], indexes[1:], key, result)
        
    def setInSlot(self, slot, key, value):
        #TODO: code this
        pass

    def setSubInSlot(self,multislot,slot,index, key,value):
        #TODO: code this
        pass


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

class OperatorGroup(Operator):
    def __init__(self, graph):
        Operator.__init__(self,graph)
        self._visibleOutputs = None
        self._visibleInputs = None
        
    def createInnerOperators(self):
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
        self.setupOutputSlots()
        
        for key, value in self.outputs.items():
            self._recurseOutputs(value, self._visibleOutputs[key])
   
    def _recurseOutputs(self, outer, inner):
        if not isinstance(inner, MultiOutputSlot):
            assert not isinstance(outer, MultiOutputSlot)
            outer._dtype = inner._dtype
            outer._shape = inner._shape
            outer._axistags = inner._axistags
        else:
            outer.resize(len(inner))
            for i, innerSlot in enumerate(inner):
                self._recurseOutputs(outer[i], inner[i])
                   
    def getSubOutSlot(self, slots, indexes, key, result):               
        slot = self._visibleOutputs[slots[0].name]
        for ind in indexes:
            slot = slot[ind]
        slot[key].writeInto(result)

    def getOutSlot(self, slot, key, result):
        self._visibleOutputs[slot.name][key].writeInto(result)
   
   
    def notifyConnectAll(self):
        self.createInnerOperators()
        self.setupInputSlots()
        self._connectInnerOutputs()
    
    def notifyConnect(self, inputSlot):
        if self._visibleInputs is not None:
            innerIns = self._visibleInputs
            innerIns[inputSlot.name].connect(inputSlot.partner)
            self._connectInnerOutputs()

    
    def notifySubConnect(self, slots, indexes):
        if self._visibleInputs is not None:            
            innerIns = self._visibleInputs
            
            innerSlot = innerIns[indexes[0].name]
    
            for i in range(len(slots)-1):
                if slots[i].partner is not None:
                    innerSlot.connect(slots[i+1].partner)
                    break 
                else:
                    innerSlot.resize(len( slots[i] ) )
                innerSlot = innerSlot[indexes[i]]
            
            self._connectInnerOutputs()
            
                            
            
            
            
    def notifyDisconnect(self, slot):
        pass
    
    def notifySubDisconnect(self, slots, indexes):
        pass
    
    def notifySubSlotRemove(self, slots, indexes):
        pass

   
                        
class Worker(Thread):
    def __init__(self, graph):
        Thread.__init__(self)
        self.graph = graph
        self.working = False
        self.daemon = True # kill automatically on application exit!
        self.finishedRequests = deque()
        self.requests = deque()
        self.currentRequestLevel = 0
        self.process = psutil.Process(os.getpid())
        self.number =  len(self.graph.workers)
        self.workAvailableEvent = Event()
        self.workAvailableEvent.clear()
        print "Initializing Worker #%d" % self.number

    def signalWorkAvailable(self):
        self.workAvailableEvent.set()
        
    def processReqObject(self, reqObject):
        reqObject.func(reqObject.key, reqObject.destination)
        reqObject.lock.acquire()
        reqObject.event.set()
        if reqObject.closure is not None:
            reqObject.closure(result = reqObject.destination, **reqObject.kwargs)
        reqObject.lock.release()
        
        #append 
        if reqObject.greenlet is not None:
            reqObject.thread.finishedRequests.append(reqObject)
            reqObject.thread.signalWorkAvailable()
        
    def run(self):
        while self.graph.running:
            self.graph.freeWorkers.append(self)
            self.workAvailableEvent.wait(1.0)
            self.graph.freeWorkers.remove(self)
            self.workAvailableEvent.clear()
            
            while not self.graph.tasks.empty() or len(self.finishedRequests) > 0:
                while len(self.finishedRequests) > 0:
                    reqObject = self.finishedRequests.popleft()
                    reqObject.lock.acquire()
                    tgr = reqObject.greenlet
                    reqObject.greenlet = None
                    reqObject.lock.release()
                    if tgr is not None:
                        self.currentRequestLevel = reqObject.requestLevel
                        task = tgr.switch()
                task = None
                try:
                    task = self.graph.tasks.get(False)#timeout = 1.0)
                except Empty:
                    pass
                if task is not None:
                    prio, reqObject = task
                    #TODO: isnt a comparison against currentRequestLevel better 
                    # then against 1 ? ...
                    if reqObject.requestLevel > 1 or self.process.get_memory_info().rss < self.graph.maxMem:
                        gr = greenlet.greenlet(self.processReqObject)
                        self.currentRequestLevel = reqObject.requestLevel
                        gr.switch( reqObject)
                    else:
                        self.graph.tasks.put(task) #move task back to task queue
                        print "Worker %d: The process uses too much memory sleeping for a while even though work is available..." % self.number
                        gc.collect()
                        time.sleep(1.0)
                    
        print "Finalized Worker"
                
    
class Graph(object):
    def __init__(self, numThreads = 3, softMaxMem =  500*1024*1024):
        self.operators = []
        self.tasks = LifoQueue() #Lifo <-> depth first, fifo <-> breath first
        self.workers = []
        self.freeWorkers = deque()
        self.running = True
        self.numThreads = numThreads
        self.maxMem = softMaxMem # in bytes
        
        for i in xrange(self.numThreads):
            w = Worker(self)
            self.workers.append(w)
            w.start()
            self.freeWorkers.append(w)
    
    def putTask(self, reqObject):
        task = [-reqObject.requestLevel, reqObject]
        self.tasks.put(task)
        
        if len(self.freeWorkers) > 0:
            w = self.freeWorkers.pop()
            self.freeWorkers.appendleft(w)
            w.signalWorkAvailable()
    
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
 
    def dumpToH5G(self, h5g, patchBoard):
        h5op = h5g.create_group("operators")
        h5op.dumpObject(self.operators, patchBoard)
        
        h5g.attrs["numThreads"] = self.numThreads
        h5g.attrs["softMaxMem"] = self.maxMem
    
    @classmethod
    def reconstructFromH5G(cls, h5g, patchBoard):
        g = Graph(numThreads = h5g.attrs["numThreads"], softMaxMem = h5g.attrs["softMaxMem"])
        patchBoard[h5g.attrs["id"]] = g 
        h5ops = h5g["operators"]        
        g.operators = h5ops.reconstructObject(patchBoard)
 
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
                ooooo = o.getOriginalOperator()
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
                    partnerOp = p._metaParent.getOriginalOperator()
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
                    partnerOp = inslot.partner.operator.getOriginalOperator()
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
                
     