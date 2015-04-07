###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the Lesser GNU General Public License
# as published by the Free Software Foundation; either version 2.1
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# See the files LICENSE.lgpl2 and LICENSE.lgpl3 for full text of the
# GNU Lesser General Public License version 2.1 and 3 respectively.
# This information is also available on the ilastik web site at:
#		   http://ilastik.org/license/
###############################################################################
#Python
import copy
import logging
import threading

#SciPy
import numpy

#lazyflow
from lazyflow.request import Request
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.operators.opCache import ObservableCache

class ListToMultiOperator(Operator):
    name = "List to Multislot converter"
    category = "Input"
    inputSlots = [InputSlot("List", stype = "sequence")]
    outputSlots = [OutputSlot("Items", level = 1)]

    def setupOutputs(self):
        inputSlot = self.inputs["List"]
        liste = self.inputs["List"].value
        self.outputs["Items"].resize(len(liste))
        for o in self.outputs["Items"]:
            o.meta.dtype = object
            o.meta.shape = (1,)

    def execute(self, slot, subindex, roi, result):
        index = subindex[0]
        liste = self.inputs["List"].value
        result[0] = liste[index]

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

    def execute(self, slot, subindex, roi, result):
        attrName = self.AttributeName.value
        inputObject = self.InputObject.value
        result[0] = getattr(inputObject, attrName)

    def propagateDirty(self, islot, subindex, roi):
        needToPropagate = False

        # We're only dirty if the field we're interested in changed
        if islot == self.InputObject and self.AttributeName.ready():
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

    def execute(self, slot, subindex, roi, result):
        req = self.Input(roi.start, roi.stop)
        req.writeInto(result)
        req.wait()
        return result

    def propagateDirty(self, slot, subindex, roi):
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

    def execute(self, slot, subindex, roi, result):
        assert False # Output is directly connected

    def propagateDirty(self, slot, subindex, roi):
        # Output is dirty if the meta data attribute of interest changed.
        # Otherwise, not dirty.
        if slot.name == "MetadataKey":
            self.Output.setDirty(slice(None))

class OpMetadataMerge(Operator):
    Input = InputSlot()
    MetadataSource = InputSlot()
    FieldsToClone = InputSlot(stype='list') # list of strings

    Output = OutputSlot()

    def setupOutputs(self):
        # Start with the original metadata
        self.Output.meta.assignFrom( self.Input.meta )

        # Merge in additional fields, selected from the source connection.
        for key in self.FieldsToClone.value:
            assert isinstance(key, str), "Metadata field names are expected to be strings"
            if key in self.MetadataSource.meta:
                setattr( self.Output.meta, key, self.MetadataSource.meta[key] )

    def execute(self, slot, subindex, roi, result):
        result[...] = self.Input(roi.start, roi.stop).wait()
        return result

    def propagateDirty(self, slot, subindex, roi):
        # Forward to the output slot
        self.Output.setDirty(roi)

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
    
    def execute(self, slot, subindex, roi, result):
        key = roi.toSlice()
        result[...] = self._data[key]


class OpValueCache(Operator, ObservableCache):
    """
    This operator caches a value in its entirety, 
    and allows for the value to be "forced in" from an external user.
    No memory management, no blockwise access.
    """
    
    name = "OpValueCache"
    category = "Cache"
    
    Input = InputSlot()
    fixAtCurrent = InputSlot(value=False)
    Output = OutputSlot()
    
    loggerName = __name__ + ".OpValueCache"
    logger = logging.getLogger(loggerName)
    traceLogger = logging.getLogger("TRACE." + loggerName)
    
    def __init__(self, *args, **kwargs):
        super(OpValueCache, self).__init__(*args, **kwargs)
        self._dirty = True
        self._value = None
        self._lock = threading.Lock()
        self._request = None

        # Now that we're initialized, it's safe to register with the memory manager
        self.registerWithMemoryManager()
        
        def handle_unready(slot):
            self._dirty = True
        self.Input.notifyUnready(handle_unready)
        
    def usedMemory(self):
        if isinstance(self._value, numpy.ndarray):
            return self._value.nbytes
        return 0 #FIXME

    def fractionOfUsedMemoryDirty(self):
        if self._dirty:
            return 1.0
        else:
            return 0.0

    def generateReport(self, report):
        super(OpValueCache, self).generateReport(report)
        if self._value is None:
            s = "no value"
        else:
            t = str(type(self._value))
            t = t[len("<type '"):-len("'>")]
            s = "value of type '{}'".format(t)
        report.info = s
    
    def setupOutputs(self):
        self.Output.meta.assignFrom(self.Input.meta)
    
    def execute(self, slot, subindex, roi, result):
        if self.fixAtCurrent.value is True or self._dirty is False:
            result[:] = self._value
            return result
        
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

            self.traceLogger.debug("State is: {}".format( {State.Dirty : 'Dirty',
                                                           State.Waiting : 'Waiting',
                                                           State.Clean : 'Clean'}[state]) )
            
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
            success = False
            while not success:
                try:
                    value = request.wait()
                    success = True
                except Request.InvalidRequestException:
                    # Oops, we're sharing the request with another thread 
                    #  and that other thread cancelled it before we got a chance to call wait().
                    # Just regenerate the request and try again...
                    with self._lock:
                        if request == self._request:
                            request = self.Input[...]
                            self._request = request
                        else:
                            request = self._request
                    state = State.Dirty
        
        result[...] = value
        
        # If we made the request, set the members
        if state == State.Dirty:
            with self._lock:
                self.Output._sig_value_changed()
                self._value = value
                self._request = None
                self._dirty = False

        return result

    def propagateDirty(self, slot, subindex, roi):
        if slot is self.Input:
            self._dirty = True
            if not self.fixAtCurrent.value:
                self.Output.setDirty(roi)
        elif slot is self.fixAtCurrent:
            if self.fixAtCurrent.value is False and self._dirty:
                self.Output.setDirty()


    def forceValue(self, value):
        """
        Allows a 'back door' to force data into this cache.
        Note: Use this function carefully.
        """
        with self._lock:
            self._value = value
            self._dirty = False
        self.Output.setDirty()
        
    def resetValue(self):
        """
        Remove the value from the cache.
        """
        with self._lock:
            self._value = None
            self._dirty = True
        self.Output.setDirty()
        
class OpPrecomputedInput(Operator):
    """
    Think of this operator like a railroad switch.  The output is connected to one of the two inputs.
    If the 'PrecomputedInput' slot is clean, then output comes directly from there.
    Otherwise, the output slot is connected to the 'SlowInput' slot.
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

    def propagateDirty(self, slot, subindex, roi):
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

    def execute(self, slot, subindex, roi, result):
        assert False, "Should not get here: Output is directly connected to the input."


class OpDummyData(Operator):
    """
    This operator provides a hard-coded test pattern that is a simple function of the requested output roi.
    It can be useful for cases where the desired output is not available, but you want to show something in the GUI anyway.
    """
    Input = InputSlot() # Used only to format the output metadata
    Output = OutputSlot()

    def setupOutputs(self):
        self.Output.meta.assignFrom(self.Input.meta)

    def execute(self, slot, subindex, roi, result):
        # Replace this entire request with a simple pattern to indicate "not available"
        # The pattern is simply a bunch of diagonal planes.
        pattern = numpy.indices( roi.stop - roi.start ).sum(0)
        pattern += numpy.sum(roi.start)
        pattern = ((pattern / 20) == (pattern + 10) / 20).astype(int)
        # If dtype is a float, use 0/1.
        # If its an int, use 0/255
        if isinstance(result.dtype, numpy.integer):
            pattern *= 255
    
        result[:] = pattern
        return result
    
    def propagateDirty(self, slot, subindex, roi):
        pass
    
class OpZeroDefault(Operator):
    """
    Provides an output that is always 'ready'.  
    Acts as a simple pass-through if 'Input' is ready().  Otherwise, provides zeros.  
    Marks everything dirty as soon as the Input becomes ready().
    """
    MetaInput = InputSlot() # Output metadata is copied from this slot
    Input = InputSlot(optional=True) # 'Real' data comes from this slot
    Output = OutputSlot() # This slot is always ready (as long as MetaInput is ready)

    def __init__(self, *args, **kwargs):
        super( OpZeroDefault, self ).__init__(*args, **kwargs)
        self._input_ready = True

    def setupOutputs(self):
        self.Output.meta.assignFrom(self.MetaInput.meta)
        input_became_ready = not self._input_ready and self.Input.ready()
        self._input_ready = self.Input.ready()
        if input_became_ready:
            self.Output.setDirty()

    def execute(self, slot, subindex, roi, result):
        if self._input_ready:
            self.Input(roi.start, roi.stop).writeInto( result ).wait()
        else:
            result[...] = 0
        return result

    def propagateDirty(self, slot, subindex, roi):
        if slot == self.Input:
            self.Output.setDirty( roi )
