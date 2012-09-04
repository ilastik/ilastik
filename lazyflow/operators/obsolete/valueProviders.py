from lazyflow.graph import *
import lazyflow.roi
import threading
import copy

from operators import OpArrayCache, OpArrayPiper, OpMultiArrayPiper


class ArrayProvider(OutputSlot):
    def __init__(self, name, shape, dtype, axistags="not none"):
        OutputSlot.__init__(self,name)
        self.meta.shape = shape
        self.meta.dtype = dtype
        self._data = None
        self.meta.axistags = axistags
        self._lock = threading.Lock()

    def setData(self,d):
        assert d.dtype == self.meta.dtype
        assert d.shape == self.meta.shape
        self._lock.acquire()
        self._data = d
        self._lock.release()
        self.setDirty(slice(None,None,None))

    def fireRequest(self, key, destination):
        assert self._data is not None, "cannot do __getitem__ on Slot %s,  data was not set !!" % self.name
        self._lock.acquire()
        destination[:] = self._data.__getitem__(key)
        self._lock.release()




class ListToMultiOperator(Operator):
    name = "List to Multislot converter"
    category = "Input"
    inputSlots = [InputSlot("List", stype = "sequence")]
    outputSlots = [MultiOutputSlot("Items", level = 1)]

    def setupOutputs(self):
        inputSlot = self.inputs["List"]
        liste = self.inputs["List"].value
        self.outputs["Items"].resize(len(liste))
        for o in self.outputs["Items"]:
            o.meta.dtype = object
            o.meta.shape = (1,)

    def getSubOutSlot(self, slots, indexes, key, result):
        liste = self.inputs["List"].value
        result[0] = liste[indexes[0]]

class OpAttributeSelector(Operator):
    """
    Given an input slot of type object, outputs a slot (also of type object)
     that selects just one of the fields (attributes) of the input object.
    Note: This operator caches a copy of the value.  It should not be used for large objects.
    """
    name = "OpAttributeSelector"
    category = "Value provider"

    InputObject = InputSlot(stype='object')
    AttributeName = InputSlot(stype='string')

    Result = OutputSlot(stype='object')

    def __init__(self, *args, **kwargs):
        super(OpAttributeSelector, self).__init__(*args, **kwargs)

        self._cachedResult = None

    def setupOutputs(self):
        self.Result.meta.shape = (1,)
        self.Result.meta.dtype = object

    def execute(self, slot, roi, result):
        attrName = self.AttributeName.value
        inputObject = self.InputObject.value
        result[0] = getattr(inputObject, attrName)

    def propagateDirty(self, islot, roi):
        needToPropagate = False

        # We're only dirty if the field we're interested in changed
        if islot == self.InputObject and self.AttributeName.configured():
            attrName = self.AttributeName.value
            inputObject = self.InputObject.value
            newResult = getattr(inputObject, attrName)
            if newResult != self._cachedResult:
                needToPropagate = True
                self._cachedResult = copy.copy(newResult)

        if islot == self.AttributeName:
            needToPropagate = True

        if needToPropagate:
            self.Result.setDirty(slice(None))

class OpMetadataInjector(Operator):
    name = "Metadata injector"
    category = "Value provider"

    Input = InputSlot()
    Metadata = InputSlot() # Dict of { string : value }

    Output = OutputSlot()

    def setupOutputs(self):
        self.Output.meta.assignFrom( self.Input.meta )

        # Inject the additional metadata attributes
        extraMetadata = self.Metadata.value
        for k,v in extraMetadata.items():
            setattr(self.Output.meta, k, v)

    def execute(self, slot, roi, result):
        key = roi.toSlice()
        result[...] = self.Input(roi.start, roi.stop).wait()

    def propagateDirty(self, slot, roi):
        # Forward to the output slot
        self.Output.setDirty(roi)

class OpMetadataSelector(Operator):
    name = "OpMetadataSelector"
    category = "Value provider"
    
    Input = InputSlot()
    MetadataKey = InputSlot( stype='string' )
    
    Output = OutputSlot(stype='object')
    
    def setupOutputs(self):
        key = self.MetadataKey.value
        self.Output.setValue( self.Input.meta[key] )

    def execute(self, slot, roi, result):
        assert False # Output is directly connected

    def propagateDirty(self, slot, roi):
        # Output is dirty if the meta data attribute of interest changed.
        # Otherwise, not dirty.
        if slot.name == "MetadataKey":
            self.Output.setDirty(slice(None))

class OpOutputProvider(Operator):
    name = "OpOutputProvider"
    category = "test"
    
    Output = OutputSlot()
    
    def __init__(self, data, meta, *args, **kwargs):
        super(OpOutputProvider, self).__init__(*args, **kwargs)
        
        self._data = data
        self.Output.meta.assignFrom(meta)
    
    def setupOutputs(self):
        pass
    
    def execute(self, slot, roi, result):
        key = roi.toSlice()
        result[...] = self._data[key]


class OpValueCache(Operator):
    """
    This operator caches a value in its entirety, 
    and allows for the value to be "forced in" from an external user.
    No memory management, no blockwise access.
    """
    
    name = "OpValueCache"
    category = "Cache"
    
    Input = InputSlot()
    Output = OutputSlot()
    
    loggerName = __name__ + ".OpValueCache"
    logger = logging.getLogger(loggerName)
    traceLogger = logging.getLogger("TRACE." + loggerName)
    
    def __init__(self, *args, **kwargs):
        super(OpValueCache, self).__init__(*args, **kwargs)
        self._dirty = False
        self._value = None
        self._lock = threading.Lock()
        self._request = None
    
    def setupOutputs(self):
        self.Output.meta.assignFrom(self.Input.meta)
        self._dirty = True
    
    def execute(self, slot, roi, result):
        # Optimization: We don't let more than one caller trigger the value to be computed at the same time
        # If some other caller has already requested the value, we'll just wait for the request he already made.
        class State():
            Dirty = 0
            Waiting = 1
            Clean = 2

        request = None
        value = None
        with self._lock:
            # What state are we in?
            if not self._dirty:
                state = State.Clean
            elif self._request is not None:
                state = State.Waiting
            else:
                state = State.Dirty

            self.traceLogger.debug("State is: {}".format( {State.Dirty : 'Dirty', State.Waiting : 'Waiting', State.Clean : 'Clean'}[state]) )
            
            # Obtain the request to wait for (create it if necessary)
            if state == State.Dirty:
                request = self.Input[...]
                self._request = request
            elif state == State.Waiting:
                request = self._request
            else:
                value = self._value

        # Now release the lock and block for the request
        if state != State.Clean:
            value = request.wait()
        
        result[...] = value
        
        # If we made the request, set the members
        if state == State.Dirty:
            with self._lock:
                self._value = value
                self._request = None
                self._dirty = False

    def propagateDirty(self, islot, roi):
        self._dirty = True
        self.Output.setDirty(roi)

    def forceValue(self, value):
        """
        Allows a 'back door' to force data into this cache.
        Note: Use this function carefully.
        """
        with self._lock:
            self._value = value
            self._dirty = False
            self.Output.setDirty(slice(None))
        
class OpPrecomputedInput(Operator):
    """
    This operator uses its precomputed
    """
    name = "OpPrecomputedInput"
    category = "Value provider"
    
    SlowInput = InputSlot() # Used if the precomputed slot is dirty
    PrecomputedInput = InputSlot(optional=True) # Only used while the slow input stays clean.
    Reset = InputSlot(optional = True, value = False)
    
    Output = OutputSlot()
    
    def __init__(self, *args, **kwargs):
        super(OpPrecomputedInput, self).__init__(*args, **kwargs)
        self._lock = threading.Lock()
    
    def setupOutputs(self):
        if self.PrecomputedInput.ready():
            self.reset()
        else:
            self.Output.connect(self.SlowInput)

    def propagateDirty(self, slot, roi):
        # If either input became dirty, the party is over.
        # We can't use the pre-computed input anymore.
        if slot == self.SlowInput:
            with self._lock:
                if self.Output.partner != self.SlowInput:
                    self.Output.connect(self.SlowInput)
                    self.Output.setDirty(roi)
        elif slot == self.Reset:
            pass
        elif slot == self.PrecomputedInput:
            pass
        else:
            assert False, "Unknown dirty input slot."
    
    def reset(self):
        """
        Called by the user when the precomputed input is valid again.
        """
        with self._lock:
            self.Output.connect(self.PrecomputedInput)

    def execute(self):
        assert False, "Should not get here: Output is directly connected to the input."


















