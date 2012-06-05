import numpy, vigra
import time
from lazyflow.graph import *
import gc
import lazyflow.roi
import threading
import copy

from operators import OpArrayCache, OpArrayPiper, OpMultiArrayPiper


class ArrayProvider(OutputSlot):
    def __init__(self, name, shape, dtype, axistags="not none"):
        OutputSlot.__init__(self,name)
        self._shape = shape
        self._dtype = dtype
        self._data = None
        self._axistags = axistags
        self._lock = threading.Lock()

    def setData(self,d):
        assert d.dtype == self._dtype
        assert d.shape == self._shape
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

    def notifyConnectAll(self):
        inputSlot = self.inputs["List"]
        liste = self.inputs["List"].value
        self.outputs["Items"].resize(len(liste))
        for o in self.outputs["Items"]:
            o._dtype = object
            o._shape = (1,)

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

if __name__ == "__main__":
    g = Graph()
    op = OpMetadataInjector(graph=g)

    additionalMetadata = {'layertype' : 7}
    op.Metadata.setValue( additionalMetadata )
    op.Input.setValue('Hello')

    # Output value should match input value
    assert op.Output.value == op.Input.value

    # Make sure all input metadata was copied to the output
    assert all( ((k,v) in op.Output.meta.items()) for k,v in op.Input.meta.items())

    # Check that the additional metadata was added to the output
    assert op.Output.meta.layertype == 7

    # Make sure dirtyness gets propagated to the output.
    dirtyList = []
    def handleDirty(*args):
        dirtyList.append(True)

    op.Output.notifyDirty( handleDirty )
    op.Input.setValue( 8 )
    assert len(dirtyList) == 1
